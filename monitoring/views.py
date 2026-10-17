from django.contrib import messages
from functools import wraps
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.http import Http404, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.core.files.base import ContentFile
from .analysis import AnalysisError, analyse_video, annotated_video_stream
from .forms import FineReportForm, PasswordResetConfirmForm, PasswordResetLookupForm, RegistrationForm, VideoForm
from .models import AccessLog, AdministratorProfile, RegisteredVehicle, TrafficSummary, TrafficVideo, VideoAnalysis, VehicleProfile, Violation, ViolationEvidence, normalize_vehicle_number

DEFAULT_EVIDENCE_PLATES = ("KA01AB1234", "KA02AB1234", "KA03AB1234")

def destination(user):
    return "dashboard" if user.is_staff else "user_dashboard"

def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, "This page is available to the Traffic Administrator only.")
            return redirect("user_dashboard")
        return view(request, *args, **kwargs)
    return wrapped

def login_view(request):
    if request.user.is_authenticated:
        return redirect(destination(request.user))
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST":
        identifier = request.POST.get("username", "")
        user = authenticate(request, username=identifier, password=request.POST.get("password", ""))
        if user is None and "@" in identifier:
            from django.contrib.auth.models import User
            matched = User.objects.filter(email__iexact=identifier).first()
            user = authenticate(request, username=matched.username, password=request.POST.get("password", "")) if matched else None
        if user is not None:
            login(request, user)
            AccessLog.objects.create(user=request.user)
            return redirect(destination(user))
        form.add_error(None, "Enter a valid username/email and password.")
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        AccessLog.objects.create(user=request.user)
        return redirect(destination(request.user))
    return render(request, "registration/login.html", {"form": form})


def reset_password(request):
    reset_user_id = request.session.get("password_reset_user_id")
    if reset_user_id:
        form = PasswordResetConfirmForm(request.POST or None)
        if request.method == "POST" and form.is_valid():
            user = User.objects.filter(pk=reset_user_id).first()
            if user is None:
                request.session.pop("password_reset_user_id", None)
                messages.error(request, "Please verify your details again.")
                return redirect("reset_password")
            user.set_password(form.cleaned_data["new_password"])
            user.save(update_fields=["password"])
            request.session.pop("password_reset_user_id", None)
            messages.success(request, "Password reset successfully. Please sign in.")
            return redirect("login")
        return render(request, "registration/reset_password.html", {"form": form, "verified": True})

    form = PasswordResetLookupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        verification_number = form.cleaned_data["verification_number"]
        if form.cleaned_data["account_type"] == "admin":
            user = User.objects.filter(
                email__iexact=email,
                is_staff=True,
                administrator_profile__unique_number=verification_number,
            ).first()
        else:
            user = User.objects.filter(
                email__iexact=email,
                vehicle_profile__vehicle_number=verification_number,
            ).first()
        if user:
            request.session["password_reset_user_id"] = user.pk
            return redirect("reset_password")
        form.add_error(None, "Details do not match our records")
    return render(request, "registration/reset_password.html", {"form": form, "verified": False})

def register(request):
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        VehicleProfile.objects.create(user=user, vehicle_number=form.cleaned_data["vehicle_number"])
        login(request, user)
        AccessLog.objects.create(user=user)
        return redirect("user_dashboard")
    return render(request, "registration/register.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect("login")

def terms(request):
    return render(request, "terms.html")

def base_context(request):
    recent = TrafficSummary.objects.order_by("-created_at", "-id")[:5]
    return {"access_logs": AccessLog.objects.filter(user=request.user)[:2], "recent_summaries": recent, "latest": recent[0] if recent else None}

@admin_required
def dashboard(request):
    context = base_context(request)
    context.update({"active": "overview"})
    return render(request, "dashboard.html", context)

@login_required
def user_dashboard(request):
    context = base_context(request)
    context.update({"traffic_summaries": TrafficSummary.objects.order_by("-created_at", "-id")[:8]})
    return render(request, "user_dashboard.html", context)

@login_required
def pending_fines(request):
    if request.user.is_staff:
        return redirect("violations")
    context = base_context(request)
    plate = normalize_vehicle_number(request.GET.get("plate", ""))
    pending_fines = Violation.objects.none()
    error_message = ""
    registered_plate = getattr(getattr(request.user, "vehicle_profile", None), "vehicle_number", "")
    if plate and plate != registered_plate:
        error_message = "Can not see others info"
    elif plate:
        pending_fines = Violation.objects.filter(
            vehicle_number=registered_plate,
            is_issued=True,
        ).order_by("-detected_at")
    context.update({"plate": plate, "pending_fines": pending_fines, "error_message": error_message, "registered_plate": registered_plate})
    return render(request, "pending_fines.html", context)

@admin_required
def live_monitoring(request):
    form = VideoForm(request.POST, request.FILES) if request.method == "POST" else VideoForm()
    if request.method == "POST" and form.is_valid():
        uploads = form.cleaned_data["source"]
        for upload in uploads:
            video = TrafficVideo.objects.create(source=upload, display_name=upload.name)
        messages.success(request, f"{len(uploads)} video(s) added to the local analysis queue.")
        return redirect("live_monitoring")
    context = base_context(request)
    videos = TrafficVideo.objects.all()
    selected_video = None
    if videos and request.GET.get("video"):
        selected_video = videos.filter(pk=request.GET.get("video")).first()
    context.update({"video_form": form, "videos": videos, "selected_video": selected_video, "active": "monitoring"})
    return render(request, "live_monitoring.html", context)

@admin_required
def process_video(request, video_id):
    if request.method != "POST":
        return redirect("live_monitoring")
    video = get_object_or_404(TrafficVideo, pk=video_id)
    analysis, _ = VideoAnalysis.objects.get_or_create(video=video)
    video.status = analysis.status = "Processing"
    video.error_message = analysis.error_message = ""
    video.save(update_fields=["status", "error_message"])
    analysis.started_at = timezone.now()
    analysis.save(update_fields=["status", "error_message", "started_at"])
    try:
        result = analyse_video(video)
        ViolationEvidence.objects.filter(video=video).delete()
        for index, (seconds, image) in enumerate(result["evidence_frames"]):
            evidence = ViolationEvidence(video=video, plate_number=DEFAULT_EVIDENCE_PLATES[index % len(DEFAULT_EVIDENCE_PLATES)])
            evidence.evidence.save(f"{video.pk}-helmet-{index + 1}.jpg", ContentFile(image), save=False)
            evidence.save()
        TrafficSummary.objects.filter(source_name=video.display_name).delete()
        TrafficSummary.objects.create(source_name=video.display_name, **result["summary"])
        for field in ("total_frames", "vehicle_count", "motorcycle_count", "car_count", "bus_count", "person_count"):
            setattr(analysis, field, result[field])
        analysis.status = video.status = "Completed"
        analysis.completed_at = video.processed_at = timezone.now()
        analysis.save()
        video.save(update_fields=["status", "processed_at", "preview"])
    except Exception as exc:
        message = str(exc) if isinstance(exc, AnalysisError) else "Unexpected analysis error. Check the server console."
        analysis.status = video.status = "Failed"
        analysis.error_message = video.error_message = message
        analysis.completed_at = timezone.now()
        analysis.save()
        video.save(update_fields=["status", "error_message"])
        messages.error(request, f"Could not analyse {video.display_name}: {message}")
    else:
        messages.success(request, f"Analysis completed for {video.display_name}.")
    return redirect("reports")

@admin_required
def analysis_status(request, video_id):
    video = get_object_or_404(TrafficVideo, pk=video_id)
    return JsonResponse({"status": video.status, "completed": video.status == "Completed", "failed": video.status == "Failed"})


@admin_required
def congestion_history(request):
    summaries = TrafficSummary.objects.order_by("-created_at", "-id")[:12]
    return JsonResponse({"points": [{"label": item.created_at.strftime("%H:%M"), "score": float(item.score)} for item in reversed(summaries)]})

@admin_required
def video_stream(request, video_id):
    video = get_object_or_404(TrafficVideo, pk=video_id)
    try:
        stream = annotated_video_stream(video)
    except AnalysisError as exc:
        raise Http404(str(exc))
    return StreamingHttpResponse(stream, content_type="multipart/x-mixed-replace; boundary=frame")

@admin_required
def reports(request):
    context = base_context(request)
    context.update({"summaries": TrafficSummary.objects.order_by("-created_at", "-id"), "analyses": VideoAnalysis.objects.select_related("video").order_by("-completed_at", "-started_at", "-id"), "active": "reports"})
    return render(request, "reports.html", context)

@admin_required
def violations(request):
    context = base_context(request)
    videos = TrafficVideo.objects.all()
    form = FineReportForm(request.POST or None, request.FILES or None, videos=videos)
    if request.method == "POST" and form.is_valid():
        Violation.objects.create(
            evidence=form.cleaned_data["evidence"],
            source_name=form.cleaned_data["area"],
            location=form.cleaned_data["area"],
            vehicle_number=form.cleaned_data["vehicle_number"],
            offence_type=Violation.HELMET_VIOLATION,
            fine_amount=form.cleaned_data["fine_amount"],
            is_issued=True,
        )
        messages.success(request, "Fine report generated and added to the user’s pending fines.")
        return redirect("violations")
    context.update({"violations": Violation.objects.all(), "form": form, "active": "violations"})
    return render(request, "violations.html", context)

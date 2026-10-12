from django.contrib import messages
from functools import wraps
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .analysis import AnalysisError, analyse_video
from .forms import RegistrationForm, VideoForm, ViolationForm
from .models import AccessLog, TrafficSummary, TrafficVideo, Violation

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

def register(request):
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
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
    recent = TrafficSummary.objects.all()[:5]
    return {"access_logs": AccessLog.objects.filter(user=request.user)[:2], "recent_summaries": recent, "latest": recent[0] if recent else None}

@admin_required
def dashboard(request):
    context = base_context(request)
    context.update({"video_form": VideoForm(), "videos": TrafficVideo.objects.all()[:4], "active": "overview"})
    return render(request, "dashboard.html", context)

@login_required
def user_dashboard(request):
    context = base_context(request)
    context.update({"traffic_summaries": TrafficSummary.objects.all()[:8]})
    return render(request, "user_dashboard.html", context)

@login_required
def pending_fines(request):
    if request.user.is_staff:
        return redirect("violations")
    context = base_context(request)
    plate = request.GET.get("plate", "").strip()
    pending_fines = Violation.objects.none()
    if plate:
        pending_fines = Violation.objects.filter(
            vehicle_number__iexact=plate,
            is_issued=True,
        ).order_by("-detected_at")
    context.update({"plate": plate, "pending_fines": pending_fines})
    return render(request, "pending_fines.html", context)

@admin_required
def videos(request):
    form = VideoForm(request.POST, request.FILES) if request.method == "POST" else VideoForm()
    if request.method == "POST" and form.is_valid():
        uploads = form.cleaned_data["source"]
        for upload in uploads:
            TrafficVideo.objects.create(source=upload, display_name=upload.name)
        messages.success(request, f"{len(uploads)} video(s) added to the local analysis queue.")
        return redirect("videos")
    context = base_context(request)
    context.update({"video_form": form, "videos": TrafficVideo.objects.all(), "active": "videos"})
    return render(request, "videos.html", context)

@admin_required
def live_monitoring(request):
    context = base_context(request)
    context.update({"videos": TrafficVideo.objects.all(), "active": "monitoring"})
    return render(request, "live_monitoring.html", context)


@admin_required
def process_video(request, video_id):
    """Run a bounded YOLO pass over one local upload and persist the result."""
    if request.method != "POST":
        return redirect("videos")
    video = get_object_or_404(TrafficVideo, pk=video_id)
    video.status = "Processing"
    video.error_message = ""
    video.save(update_fields=["status", "error_message"])
    try:
        result = analyse_video(video)
    except AnalysisError as exc:
        video.status = "Failed"
        video.error_message = str(exc)
        video.save(update_fields=["status", "error_message"])
        messages.error(request, f"Could not analyse {video.display_name}: {exc}")
    except Exception:
        video.status = "Failed"
        video.error_message = "Unexpected analysis error. Check the server console."
        video.save(update_fields=["status", "error_message"])
        messages.error(request, f"Could not analyse {video.display_name}. Check the server console.")
    else:
        TrafficSummary.objects.create(source_name=video.display_name, **result.summary)
        video.status = "Processed"
        video.processed_at = timezone.now()
        video.save(update_fields=["status", "processed_at", "preview"])
        messages.success(request, f"YOLO analysis completed for {video.display_name}.")
    return redirect(request.POST.get("next") or "videos")

@admin_required
def reports(request):
    context = base_context(request)
    context.update({"summaries": TrafficSummary.objects.all(), "active": "reports"})
    return render(request, "reports.html", context)

@admin_required
def violations(request):
    context = base_context(request)
    context.update({"violations": Violation.objects.all(), "active": "violations"})
    return render(request, "violations.html", context)

@admin_required
def create_fine_report(request):
    form = ViolationForm(request.POST, request.FILES) if request.method == "POST" else ViolationForm()
    if request.method == "POST" and form.is_valid():
        report = form.save(commit=False)
        report.is_issued = True
        report.save()
        messages.success(request, "Fine report created for vehicle-number lookup.")
        return redirect("violations")
    context = base_context(request)
    context.update({"form": form, "active": "violations"})
    return render(request, "create_fine_report.html", context)

@admin_required
def issue_fine(request, violation_id):
    violation = get_object_or_404(Violation, pk=violation_id)
    if request.method == "POST":
        violation.vehicle_number = request.POST.get("vehicle_number", "")
        violation.offence_type = request.POST.get("offence_type", violation.offence_type)
        violation.location = request.POST.get("location", "")
        violation.fine_amount = request.POST.get("fine_amount") or 0
        violation.is_issued = True
        violation.save()
        messages.success(request, "Fine marked as issued.")
    return redirect("violations")

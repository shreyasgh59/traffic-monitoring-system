from django.conf import settings
from django.db import models
import re


def normalize_vehicle_number(value):
    return re.sub(r"[\s-]+", "", (value or "")).upper()


class RegisteredVehicle(models.Model):
    plate_number = models.CharField(max_length=32, unique=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.plate_number = normalize_vehicle_number(self.plate_number)
        super().save(*args, **kwargs)


class VehicleProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vehicle_profile")
    vehicle_number = models.CharField(max_length=32, unique=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.vehicle_number = normalize_vehicle_number(self.vehicle_number) or None
        super().save(*args, **kwargs)


class AdministratorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="administrator_profile")
    unique_number = models.CharField(max_length=32, unique=True)

    def save(self, *args, **kwargs):
        self.unique_number = (self.unique_number or "").strip()
        super().save(*args, **kwargs)

class AccessLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="accesses")
    accessed_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-accessed_at"]

class TrafficVideo(models.Model):
    source = models.FileField(upload_to="traffic_videos/")
    display_name = models.CharField(max_length=160)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=24, default="Queued")
    processed_at = models.DateTimeField(blank=True, null=True)
    preview = models.ImageField(upload_to="analysis_previews/", blank=True, null=True)
    error_message = models.TextField(blank=True)

    @property
    def area_name(self):
        match = re.search(r"clip\s*(\d+)", self.display_name, flags=re.IGNORECASE)
        return f"Area-{match.group(1)}" if match else self.display_name

class TrafficSummary(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    source_name = models.CharField(max_length=160)
    visible_vehicles = models.PositiveIntegerField(default=0)
    score = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    level = models.CharField(max_length=12, default="Low")

    @property
    def area_name(self):
        match = re.search(r"clip\s*(\d+)", self.source_name, flags=re.IGNORECASE)
        return f"Area-{match.group(1)}" if match else self.source_name


class VideoAnalysis(models.Model):
    video = models.OneToOneField(TrafficVideo, on_delete=models.CASCADE, related_name="analysis")
    status = models.CharField(max_length=16, default="Queued")
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    total_frames = models.PositiveIntegerField(default=0)
    vehicle_count = models.PositiveIntegerField(default=0)
    motorcycle_count = models.PositiveIntegerField(default=0)
    car_count = models.PositiveIntegerField(default=0)
    bus_count = models.PositiveIntegerField(default=0)
    person_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)


class ViolationEvidence(models.Model):
    video = models.ForeignKey(TrafficVideo, on_delete=models.CASCADE, related_name="evidence_items", blank=True, null=True)
    plate_number = models.CharField(max_length=32)
    violation_type = models.CharField(max_length=100, default="Helmet violation")
    evidence = models.ImageField(upload_to="violation_evidence/", blank=True, null=True)
    detected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-detected_at"]

    @property
    def is_registered(self):
        return RegisteredVehicle.objects.filter(plate_number=normalize_vehicle_number(self.plate_number)).exists()

    @property
    def area_name(self):
        return self.video.area_name if self.video else "Live monitoring"

class Violation(models.Model):
    HELMET_VIOLATION = "Helmet violation (motorcycle)"
    OFFENCE_CHOICES = [(HELMET_VIOLATION, HELMET_VIOLATION)]
    evidence = models.ImageField(upload_to="evidence/", blank=True, null=True)
    source_name = models.CharField(max_length=160)
    detected_at = models.DateTimeField(auto_now_add=True)
    confidence = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    vehicle_number = models.CharField(max_length=32, blank=True)
    offence_type = models.CharField(max_length=100, choices=OFFENCE_CHOICES, default=HELMET_VIOLATION)
    fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    location = models.CharField(max_length=160, blank=True)
    is_issued = models.BooleanField(default=False)

    class Meta:
        ordering = ["-detected_at"]

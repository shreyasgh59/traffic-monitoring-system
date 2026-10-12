from django.conf import settings
from django.db import models

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

class TrafficSummary(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    source_name = models.CharField(max_length=160)
    visible_vehicles = models.PositiveIntegerField(default=0)
    occupancy = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    score = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    level = models.CharField(max_length=12, default="Low")

class Violation(models.Model):
    evidence = models.ImageField(upload_to="evidence/", blank=True, null=True)
    source_name = models.CharField(max_length=160)
    detected_at = models.DateTimeField(auto_now_add=True)
    confidence = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    vehicle_number = models.CharField(max_length=32, blank=True)
    offence_type = models.CharField(max_length=100, default="No helmet - review required")
    fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    location = models.CharField(max_length=160, blank=True)
    is_issued = models.BooleanField(default=False)

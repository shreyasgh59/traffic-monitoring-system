from django.contrib import admin
from .models import AccessLog, AdministratorProfile, RegisteredVehicle, TrafficVideo, TrafficSummary, VideoAnalysis, Violation, ViolationEvidence
admin.site.register([AccessLog, AdministratorProfile, RegisteredVehicle, TrafficVideo, TrafficSummary, VideoAnalysis, Violation, ViolationEvidence])

from django.contrib import admin
from .models import AccessLog, RegisteredVehicle, TrafficVideo, TrafficSummary, VideoAnalysis, Violation, ViolationEvidence
admin.site.register([AccessLog, RegisteredVehicle, TrafficVideo, TrafficSummary, VideoAnalysis, Violation, ViolationEvidence])

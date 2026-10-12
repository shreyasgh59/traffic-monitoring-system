from django.contrib import admin
from .models import AccessLog, TrafficVideo, TrafficSummary, Violation
admin.site.register([AccessLog, TrafficVideo, TrafficSummary, Violation])

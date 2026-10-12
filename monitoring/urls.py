from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"), path("user/", views.user_dashboard, name="user_dashboard"), path("user/pending-fines/", views.pending_fines, name="pending_fines"), path("login/", views.login_view, name="login"), path("register/", views.register, name="register"), path("logout/", views.logout_view, name="logout"), path("terms/", views.terms, name="terms"),
    path("videos/", views.videos, name="videos"), path("videos/<int:video_id>/process/", views.process_video, name="process_video"), path("monitoring/", views.live_monitoring, name="live_monitoring"), path("reports/", views.reports, name="reports"), path("violations/", views.violations, name="violations"), path("violations/create/", views.create_fine_report, name="create_fine_report"), path("violations/<int:violation_id>/issue/", views.issue_fine, name="issue_fine"),
]

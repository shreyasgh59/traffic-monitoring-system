from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("user/", views.user_dashboard, name="user_dashboard"),
    path("user/pending-fines/", views.pending_fines, name="pending_fines"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register, name="register"),
    path("reset-password/", views.reset_password, name="reset_password"),
    path("logout/", views.logout_view, name="logout"),
    path("terms/", views.terms, name="terms"),
    path("monitoring/", views.live_monitoring, name="live_monitoring"),
    path("monitoring/<int:video_id>/stream/", views.video_stream, name="video_stream"),
    path("monitoring/<int:video_id>/process/", views.process_video, name="process_video"),
    path("monitoring/<int:video_id>/status/", views.analysis_status, name="analysis_status"),
    path("api/congestion-history/", views.congestion_history, name="congestion_history"),
    path("reports/", views.reports, name="reports"),
    path("violations/", views.violations, name="violations"),
]

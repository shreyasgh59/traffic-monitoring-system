from io import BytesIO
import tempfile
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from PIL import Image

from .models import AdministratorProfile, TrafficSummary, TrafficVideo, VehicleProfile, Violation


def image_upload(name="snapshot.png"):
    image = Image.new("RGB", (8, 8), "red")
    content = BytesIO()
    image.save(content, format="PNG")
    return SimpleUploadedFile(name, content.getvalue(), content_type="image/png")


class TrafficMonitoringViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary_media = tempfile.TemporaryDirectory(dir=settings.BASE_DIR)
        cls.media_override = override_settings(MEDIA_ROOT=cls.temporary_media.name)
        cls.media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.media_override.disable()
        cls.temporary_media.cleanup()

    def setUp(self):
        self.admin = User.objects.create_user(username="admin", password="safe-test-password", is_staff=True)
        AdministratorProfile.objects.create(user=self.admin, unique_number="012")
        self.owner = User.objects.create_user(username="owner", password="safe-test-password")
        self.other_user = User.objects.create_user(username="other", password="safe-test-password")
        VehicleProfile.objects.create(user=self.owner, vehicle_number="KA77AB1234")
        VehicleProfile.objects.create(user=self.other_user, vehicle_number="KA88AB1234")
        self.video = TrafficVideo.objects.create(
            source=SimpleUploadedFile("clip1.mp4", b"video", content_type="video/mp4"),
            display_name="clip1.mp4",
        )

    def test_signup_normalizes_and_rejects_duplicate_vehicle_number(self):
        response = self.client.post(reverse("register"), {
            "username": "duplicate-plate",
            "email": "duplicate@example.com",
            "vehicle_number": "ka 77 ab 1234",
            "password1": "StrongPass!123",
            "password2": "StrongPass!123",
        })

        self.assertContains(response, "This vehicle number is already registered")
        self.assertFalse(User.objects.filter(username="duplicate-plate").exists())

        response = self.client.post(reverse("register"), {
            "username": "new-driver",
            "email": "new@example.com",
            "vehicle_number": "ka 01 ab 9999",
            "password1": "StrongPass!123",
            "password2": "StrongPass!123",
        })

        self.assertRedirects(response, reverse("user_dashboard"))
        self.assertEqual(User.objects.get(username="new-driver").vehicle_profile.vehicle_number, "KA01AB9999")

    def test_user_cannot_view_another_registered_plate(self):
        Violation.objects.create(vehicle_number="KA88AB1234", source_name="Area-2", location="Area-2", is_issued=True)
        self.client.force_login(self.owner)

        response = self.client.get(reverse("pending_fines"), {"plate": "ka 88 ab 1234"})

        self.assertContains(response, "Can not see others info")
        self.assertNotContains(response, "Area-2")

    def test_user_sees_only_own_fines(self):
        Violation.objects.create(vehicle_number="KA77AB1234", source_name="Area-1", location="Area-1", is_issued=True)
        Violation.objects.create(vehicle_number="KA88AB1234", source_name="Area-2", location="Area-2", is_issued=True)
        self.client.force_login(self.owner)

        response = self.client.get(reverse("pending_fines"), {"plate": "KA77AB1234"})

        self.assertContains(response, "Area-1")
        self.assertNotContains(response, "Area-2")

    def test_traffic_status_uses_area_names_without_occupancy_or_score(self):
        TrafficSummary.objects.create(source_name="clip1.mp4", visible_vehicles=4, level="Low")
        self.client.force_login(self.owner)

        response = self.client.get(reverse("user_dashboard"))

        self.assertContains(response, "Area-1")
        self.assertNotContains(response, "OCCUPANCY")
        self.assertNotContains(response, "SCORE")

    @patch("monitoring.views.annotated_video_stream")
    def test_admin_live_stream_returns_annotated_mjpeg(self, annotated_stream):
        annotated_stream.return_value = iter([b"--frame\r\nContent-Type: image/jpeg\r\n\r\nfake\r\n"])
        self.client.force_login(self.admin)

        response = self.client.get(reverse("video_stream", args=[self.video.id]))

        self.assertEqual(response.status_code, 200)
        self.assertIn("multipart/x-mixed-replace", response["Content-Type"])
        self.assertIn(b"Content-Type: image/jpeg", b"".join(response.streaming_content))

    def test_live_monitoring_starts_without_a_selected_video(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("live_monitoring"))

        self.assertContains(response, "No Video Source Selected")
        self.assertNotContains(response, 'id="live-stream"')

    def test_password_reset_requires_matching_email_and_vehicle_plate(self):
        self.owner.email = "owner@example.com"
        self.owner.save(update_fields=["email"])

        response = self.client.post(reverse("reset_password"), {
            "email": "owner@example.com",
            "account_type": "user",
            "verification_number": "KA00AB0000",
        })
        self.assertContains(response, "Details do not match our records")

        response = self.client.post(reverse("reset_password"), {
            "email": "owner@example.com",
            "account_type": "user",
            "verification_number": "ka 77 ab 1234",
        })
        self.assertRedirects(response, reverse("reset_password"))

        response = self.client.post(reverse("reset_password"), {
            "new_password": "NewSafePass!123",
            "confirm_password": "NewSafePass!123",
        })
        self.assertRedirects(response, reverse("login"))
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.check_password("NewSafePass!123"))

    def test_administrator_password_reset_requires_matching_unique_number(self):
        self.admin.email = "admin@example.com"
        self.admin.save(update_fields=["email"])

        response = self.client.post(reverse("reset_password"), {
            "email": "admin@example.com",
            "account_type": "admin",
            "verification_number": "011",
        })
        self.assertContains(response, "Details do not match our records")

        response = self.client.post(reverse("reset_password"), {
            "email": "admin@example.com",
            "account_type": "admin",
            "verification_number": "012",
        })
        self.assertRedirects(response, reverse("reset_password"))

    def test_admin_generates_timestamped_fine_report_with_snapshot(self):
        self.client.force_login(self.admin)

        response = self.client.post(reverse("violations"), {
            "vehicle_number": "ka 77 ab 1234",
            "area": "Area-1",
            "fine_amount": "1000",
            "evidence": image_upload(),
        })

        self.assertRedirects(response, reverse("violations"))
        report = Violation.objects.get(vehicle_number="KA77AB1234", offence_type=Violation.HELMET_VIOLATION)
        self.assertEqual(report.location, "Area-1")
        self.assertTrue(report.evidence.name.endswith("snapshot.png"))
        self.assertEqual(report.fine_amount, 1000)
        self.assertIsNotNone(report.detected_at)

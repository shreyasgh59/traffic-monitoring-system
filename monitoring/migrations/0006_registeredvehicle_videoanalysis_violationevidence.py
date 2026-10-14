from django.db import migrations, models
import django.db.models.deletion


PLATES = (
    "KA01AB1234", "KA02AB1234", "KA03AB1234", "KA04AB1234", "KA05AB1234",
    "KA06AB1234", "KA07AB1234", "KA08AB1234", "KA09AB1234", "KA10AB1234",
)


def seed_registered_vehicles(apps, schema_editor):
    RegisteredVehicle = apps.get_model("monitoring", "RegisteredVehicle")
    for plate in PLATES:
        RegisteredVehicle.objects.get_or_create(plate_number=plate)


class Migration(migrations.Migration):
    dependencies = [("monitoring", "0005_vehicle_profile_and_fine_constraints")]

    operations = [
        migrations.CreateModel(
            name="RegisteredVehicle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("plate_number", models.CharField(max_length=32, unique=True)),
                ("registered_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="VideoAnalysis",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(default="Queued", max_length=16)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("total_frames", models.PositiveIntegerField(default=0)),
                ("vehicle_count", models.PositiveIntegerField(default=0)),
                ("motorcycle_count", models.PositiveIntegerField(default=0)),
                ("violation_count", models.PositiveIntegerField(default=0)),
                ("error_message", models.TextField(blank=True)),
                ("video", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="analysis", to="monitoring.trafficvideo")),
            ],
        ),
        migrations.CreateModel(
            name="ViolationEvidence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("plate_number", models.CharField(max_length=32)),
                ("violation_type", models.CharField(default="Helmet violation", max_length=100)),
                ("evidence", models.ImageField(blank=True, null=True, upload_to="violation_evidence/")),
                ("detected_at", models.DateTimeField(auto_now_add=True)),
                ("video", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="evidence_items", to="monitoring.trafficvideo")),
            ],
            options={"ordering": ["-detected_at"]},
        ),
        migrations.RunPython(seed_registered_vehicles, migrations.RunPython.noop),
    ]

from django.contrib.auth.hashers import make_password
from django.db import migrations, models
import django.db.models.deletion


def seed_vehicle_profiles(apps, schema_editor):
    User = apps.get_model("auth", "User")
    VehicleProfile = apps.get_model("monitoring", "VehicleProfile")
    seeds = (("user1", "KA17AB1234"), ("User2", "KA19AB1234"))
    for username, plate in seeds:
        user = User.objects.filter(username__iexact=username).order_by("id").first()
        if user is None and username == "User2":
            user = User.objects.create(
                username="User2",
                email="user2@test.com",
                password=make_password("Test11234"),
                is_active=True,
            )
        if user is None:
            continue
        profile, _ = VehicleProfile.objects.get_or_create(user=user)
        if not profile.vehicle_number and not VehicleProfile.objects.filter(vehicle_number=plate).exclude(pk=profile.pk).exists():
            profile.vehicle_number = plate
            profile.save(update_fields=["vehicle_number"])


class Migration(migrations.Migration):
    dependencies = [("monitoring", "0004_trafficvideo_error_message_trafficvideo_preview_and_more")]

    operations = [
        migrations.CreateModel(
            name="VehicleProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("vehicle_number", models.CharField(blank=True, max_length=32, null=True, unique=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="vehicle_profile", to="auth.user")),
            ],
        ),
        migrations.AlterField(
            model_name="violation",
            name="offence_type",
            field=models.CharField(choices=[("Helmet violation (motorcycle)", "Helmet violation (motorcycle)")], default="Helmet violation (motorcycle)", max_length=100),
        ),
        migrations.AlterModelOptions(name="violation", options={"ordering": ["-detected_at"]}),
        migrations.RunPython(seed_vehicle_profiles, migrations.RunPython.noop),
    ]

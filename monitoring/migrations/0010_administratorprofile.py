from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def add_default_administrator_number(apps, schema_editor):
    User = apps.get_model("auth", "User")
    AdministratorProfile = apps.get_model("monitoring", "AdministratorProfile")
    administrator = User.objects.filter(username="Shreyas", is_staff=True).first()
    if administrator:
        AdministratorProfile.objects.update_or_create(user=administrator, defaults={"unique_number": "011"})


class Migration(migrations.Migration):
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ("monitoring", "0009_align_traffic_density_levels")]

    operations = [
        migrations.CreateModel(
            name="AdministratorProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("unique_number", models.CharField(max_length=32, unique=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="administrator_profile", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RunPython(add_default_administrator_number, migrations.RunPython.noop),
    ]

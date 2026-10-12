from django.contrib.auth.hashers import make_password
from django.db import migrations

def add_demo_user_and_fine(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Violation = apps.get_model("monitoring", "Violation")
    user, _ = User.objects.get_or_create(username="user1", defaults={"email": "user1@test.com"})
    user.email = "user1@test.com"
    user.is_staff = False
    user.is_superuser = False
    user.is_active = True
    user.password = make_password("Test11234")
    user.save()
    Violation.objects.get_or_create(vehicle_number="KA17AB1234", source_name="Demo traffic camera", defaults={"offence_type": "Signal violation - demo report", "fine_amount": 500, "location": "Demo Junction", "confidence": 95.00, "is_issued": True})

class Migration(migrations.Migration):
    dependencies = [("monitoring", "0002_single_shreyas_administrator")]
    operations = [migrations.RunPython(add_demo_user_and_fine, migrations.RunPython.noop)]

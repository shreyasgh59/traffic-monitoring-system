from django.contrib.auth.hashers import make_password
from django.db import migrations

def create_single_administrator(apps, schema_editor):
    User = apps.get_model("auth", "User")
    # Preserve other accounts but ensure they are ordinary users, never administrators.
    User.objects.exclude(username="Shreyas").update(is_staff=False, is_superuser=False)
    admin, created = User.objects.get_or_create(
        username="Shreyas",
        defaults={"email": "shreyas@test.com"},
    )
    admin.email = "shreyas@test.com"
    admin.is_staff = True
    admin.is_superuser = True
    admin.is_active = True
    admin.password = make_password("Shashank123")
    admin.save()

class Migration(migrations.Migration):
    dependencies = [("monitoring", "0001_initial"), ("auth", "0012_alter_user_first_name_max_length")]
    operations = [migrations.RunPython(create_single_administrator, migrations.RunPython.noop)]

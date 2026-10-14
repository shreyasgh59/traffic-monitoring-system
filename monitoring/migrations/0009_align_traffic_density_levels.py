from django.db import migrations


def align_levels(apps, schema_editor):
    TrafficSummary = apps.get_model("monitoring", "TrafficSummary")
    for summary in TrafficSummary.objects.all().only("id", "score", "level"):
        score = float(summary.score)
        level = "Heavy" if score >= 70 else "Medium" if score >= 40 else "Low"
        if summary.level != level:
            summary.level = level
            summary.save(update_fields=["level"])


class Migration(migrations.Migration):
    dependencies = [("monitoring", "0008_remove_occupancy_and_helmet_analytics")]

    operations = [migrations.RunPython(align_levels, migrations.RunPython.noop)]

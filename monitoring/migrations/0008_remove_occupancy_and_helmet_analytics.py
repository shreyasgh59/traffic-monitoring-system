from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("monitoring", "0007_videoanalysis_vehicle_breakdown")]

    operations = [
        migrations.RemoveField(model_name="trafficsummary", name="occupancy"),
        migrations.RemoveField(model_name="videoanalysis", name="truck_count"),
        migrations.RemoveField(model_name="videoanalysis", name="violation_count"),
        migrations.AddField(model_name="videoanalysis", name="person_count", field=models.PositiveIntegerField(default=0)),
    ]

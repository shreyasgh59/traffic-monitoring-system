from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("monitoring", "0006_registeredvehicle_videoanalysis_violationevidence")]

    operations = [
        migrations.AddField(model_name="videoanalysis", name="bus_count", field=models.PositiveIntegerField(default=0)),
        migrations.AddField(model_name="videoanalysis", name="car_count", field=models.PositiveIntegerField(default=0)),
        migrations.AddField(model_name="videoanalysis", name="truck_count", field=models.PositiveIntegerField(default=0)),
    ]

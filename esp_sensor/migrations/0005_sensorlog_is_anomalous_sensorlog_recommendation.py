# Generated by Django 4.2.3 on 2024-05-29 03:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('esp_sensor', '0004_alter_sensor_power_alter_sensor_volt_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sensorlog',
            name='is_anomalous',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='sensorlog',
            name='recommendation',
            field=models.TextField(blank=True, null=True),
        ),
    ]

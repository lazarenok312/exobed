# Generated by Django 4.2.3 on 2024-03-22 05:55

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('esp_sensor', '0004_sensor_fan_speed_sensor_temperature'),
    ]

    operations = [
        migrations.AddField(
            model_name='sensor',
            name='previous_fan_speed',
            field=models.IntegerField(default=0, verbose_name='Предыдущая скорость кулера'),
        ),
        migrations.AddField(
            model_name='sensor',
            name='previous_temperature',
            field=models.FloatField(default=0, verbose_name='Предыдущая температура'),
        ),
        migrations.AddField(
            model_name='sensor',
            name='previous_volt',
            field=models.IntegerField(default=0, verbose_name='Предыдущее электрическое напряжение'),
        ),
        migrations.AddField(
            model_name='sensor',
            name='previous_watt',
            field=models.IntegerField(default=0, verbose_name='Предыдущее потребление мощности'),
        ),
    ]
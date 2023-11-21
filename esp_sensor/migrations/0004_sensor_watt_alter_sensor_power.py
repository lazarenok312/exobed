# Generated by Django 4.1.5 on 2023-09-13 09:52

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('esp_sensor', '0003_sensor_volt'),
    ]

    operations = [
        migrations.AddField(
            model_name='sensor',
            name='watt',
            field=models.IntegerField(default=0, verbose_name='Измерение мощности'),
        ),
        migrations.AlterField(
            model_name='sensor',
            name='power',
            field=models.IntegerField(blank=True, default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='Мощность'),
        ),
    ]

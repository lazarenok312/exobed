# Generated by Django 4.1.5 on 2024-04-05 07:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('esp_sensor', '0007_alter_sensor_date_added'),
    ]

    operations = [
        migrations.AddField(
            model_name='sensor',
            name='start',
            field=models.BooleanField(default=False, verbose_name='Старт'),
        ),
    ]
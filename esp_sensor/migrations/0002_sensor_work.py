# Generated by Django 4.1.5 on 2023-07-21 06:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('esp_sensor', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sensor',
            name='work',
            field=models.BooleanField(default=True, verbose_name='Онлайн'),
        ),
    ]
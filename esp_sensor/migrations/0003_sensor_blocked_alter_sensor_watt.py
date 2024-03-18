# Generated by Django 4.1.5 on 2024-03-18 07:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('esp_sensor', '0002_delete_sensordata'),
    ]

    operations = [
        migrations.AddField(
            model_name='sensor',
            name='blocked',
            field=models.BooleanField(default=False, verbose_name='Заблокирован'),
        ),
        migrations.AlterField(
            model_name='sensor',
            name='watt',
            field=models.IntegerField(default=0, verbose_name='Потребление мощности'),
        ),
    ]

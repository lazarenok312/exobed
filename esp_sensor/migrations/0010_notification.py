# Generated by Django 4.1.5 on 2024-04-15 10:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('esp_sensor', '0009_sensor_ip_address'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.CharField(max_length=255)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
    ]
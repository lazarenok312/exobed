# Generated by Django 4.1.5 on 2023-07-26 07:34

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('esp_sensor', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, max_length=25, verbose_name='Имя')),
                ('surnames', models.CharField(blank=True, max_length=25, verbose_name='Фамилия')),
                ('work_phone', models.CharField(blank=True, max_length=20, null=True, verbose_name='Рабочий телефон')),
                ('email', models.EmailField(blank=True, max_length=40, verbose_name='Электронная почта')),
                ('photo', models.ImageField(blank=True, default='../static/img/default.png', upload_to='users/%Y/%m/%d', verbose_name='Фото')),
                ('slug', models.SlugField(blank=True, verbose_name='URL')),
                ('sensor', models.ManyToManyField(blank=True, to='esp_sensor.sensor', verbose_name='Датчик')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Профиль',
                'verbose_name_plural': 'Профиля',
            },
        ),
    ]

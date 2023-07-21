# Generated by Django 4.1.5 on 2023-07-20 10:41

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': 'Город',
                'verbose_name_plural': 'Города',
            },
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': 'Страна',
                'verbose_name_plural': 'Страны',
            },
        ),
        migrations.CreateModel(
            name='Sensor',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Имя датчика')),
                ('slug', models.SlugField(max_length=255, unique=True, verbose_name='URL')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('owner', models.CharField(blank=True, max_length=100, verbose_name='Владелец')),
                ('date_added', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата добавления')),
                ('inclusions', models.IntegerField(default=0, verbose_name='Количество включений')),
                ('power', models.IntegerField(default=0, verbose_name='Мощность')),
                ('city', models.ManyToManyField(blank=True, to='esp_sensor.city', verbose_name='Город')),
                ('country', models.ManyToManyField(blank=True, to='esp_sensor.country', verbose_name='Страна')),
            ],
            options={
                'verbose_name': 'Датчик',
                'verbose_name_plural': 'Датчики',
            },
        ),
        migrations.AddField(
            model_name='city',
            name='country',
            field=models.ManyToManyField(blank=True, to='esp_sensor.country', verbose_name='Страна'),
        ),
    ]

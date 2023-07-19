from django.utils import timezone
from django.db import models


class Country(models.Model):
    name = models.CharField(max_length=100)


class City(models.Model):
    country = models.ManyToManyField(Country, blank=True, verbose_name='Страна')
    name = models.CharField(max_length=100)


class Sensor(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField('Имя датчика', max_length=100, unique=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True, verbose_name="URL")
    description = models.TextField('Описание', blank=True)
    owner = models.CharField("Владелец", max_length=100, blank=True)
    date_added = models.DateTimeField('Дата добавления', default=timezone.now)
    country = models.ManyToManyField(Country, blank=True, verbose_name='Страна')
    city = models.ManyToManyField(City, blank=True, verbose_name='Город')
    inclusions = models.IntegerField("Количество включений", default=0)
    power = models.IntegerField("Мощность", default=0)

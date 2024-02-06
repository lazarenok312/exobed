from django.urls import reverse
from django.utils import timezone
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Country(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField("Название", max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Страна'
        verbose_name_plural = 'Страны'


class City(models.Model):
    id = models.AutoField(primary_key=True)
    country = models.ManyToManyField(Country, blank=True, verbose_name='Страна')
    name = models.CharField("Название", max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'


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
    power = models.IntegerField(default=0,
                                blank=True,
                                verbose_name='Мощность',
                                validators=[MinValueValidator(0), MaxValueValidator(100)])
    watt = models.IntegerField("Измерение мощности", default=0)
    volt = models.IntegerField("Электрическое напряжение", default=0)
    work = models.BooleanField('Онлайн', default=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('sensor_detail', args=[str(self.id)])

    class Meta:
        verbose_name = 'Датчик'
        verbose_name_plural = 'Датчики'


class SensorLog(models.Model):
    sensor = models.ForeignKey('Sensor', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    log_type = models.CharField(max_length=20)

    def __str__(self):
        return f'{self.sensor.name} - {self.log_type} - {self.timestamp}'

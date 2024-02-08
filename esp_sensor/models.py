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


class SensorData(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name='data')
    timestamp = models.DateTimeField('Время записи', default=timezone.now)
    value = models.FloatField('Значение')

    class Meta:
        ordering = ['-timestamp']


class SensorLog(models.Model):
    sensor = models.ForeignKey('Sensor', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    log_type = models.CharField(max_length=20)
    previous_power = models.IntegerField(null=True, blank=True)
    previous_watt = models.IntegerField(null=True, blank=True)
    previous_volt = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f'{self.sensor.name} - {self.log_type} - {self.timestamp}'

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old_log = SensorLog.objects.get(pk=self.pk)
                if old_log.watt != self.previous_watt:
                    log_type = 'Изменение мощности'
                    SensorLog.objects.create(sensor=self.sensor, log_type=log_type, previous_power=old_log.watt)
                elif old_log.volt != self.previous_volt:
                    log_type = 'Изменение напряжения'
                    SensorLog.objects.create(sensor=self.sensor, log_type=log_type, previous_volt=old_log.volt)
            except SensorLog.DoesNotExist:
                pass
        super(SensorLog, self).save(*args, **kwargs)

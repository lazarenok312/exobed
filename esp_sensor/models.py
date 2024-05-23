from django.urls import reverse
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify


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
    date_added = models.DateTimeField('Дата добавления', auto_now=True)
    country = models.ManyToManyField(Country, blank=True, verbose_name='Страна')
    city = models.ManyToManyField(City, blank=True, verbose_name='Город')
    inclusions = models.IntegerField("Количество включений", default=0)
    power = models.IntegerField(default=0, blank=True, verbose_name='Мощность %',
                                validators=[MinValueValidator(0), MaxValueValidator(100)])
    watt = models.IntegerField("Потребление мощности Ватт", default=0)
    volt = models.IntegerField("Электрическое напряжение Вольт", default=0)
    work = models.BooleanField('Онлайн', default=True)
    blocked = models.BooleanField('Заблокирован', default=False)
    start = models.BooleanField('Старт', default=False)
    temperature = models.FloatField('Температура', default=0)
    fan_speed = models.IntegerField('Скорость кулера', default=0)
    ip_address = models.CharField('IP Адрес', max_length=15, blank=True)
    mac_address = models.CharField('MAC Адрес', max_length=20, blank=True)
    confirmed = models.BooleanField('Подтвержден администратором', default=False)
    version = models.CharField('Версия прошивки', max_length=15, blank=True)
    processing_time = models.FloatField('Время обработки (мс)', null=True, blank=True)

    def __str__(self):
        return self.name

    def is_blocked(self):
        return self.blocked

    def get_absolute_url(self):
        return reverse('sensor_detail', args=[str(self.id)])

    class Meta:
        verbose_name = 'Датчик'
        verbose_name_plural = 'Датчики'

    def save(self, *args, **kwargs):
        if self.blocked:
            self.work = False

        if not self.slug:
            self.slug = slugify(self.name)

        if not self.work:
            self.watt = 0
            self.volt = 0
            self.temperature = 0
            self.fan_speed = 0

        super().save(*args, **kwargs)

        if self.pk:
            log_type = 'Изменение данных в базе'
            SensorLog.objects.create(sensor=self, log_type=log_type, previous_power=self.power,
                                     previous_watt=self.watt, previous_volt=self.volt)


class SensorLog(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE)
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
                if old_log.previous_watt != self.previous_watt:
                    log_type = 'Изменение мощности'
                    SensorLog.objects.create(sensor=self.sensor, log_type=log_type,
                                             previous_power=old_log.previous_watt)
                elif old_log.previous_volt != self.previous_volt:
                    log_type = 'Изменение напряжения'
                    SensorLog.objects.create(sensor=self.sensor, log_type=log_type, previous_volt=old_log.previous_volt)
            except SensorLog.DoesNotExist:
                pass
        super(SensorLog, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Логи'
        verbose_name_plural = 'Логи'


class Firmware(models.Model):
    version = models.CharField("Версия", max_length=10)
    file = models.FileField(upload_to='firmwares/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.version

    class Meta:
        verbose_name = 'Прошивка'
        verbose_name_plural = 'Прошивки'

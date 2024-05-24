from django.contrib.auth.models import User
from django.db import models
from esp_sensor.models import Sensor
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

class Profile(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, verbose_name="Пользователь", on_delete=models.CASCADE)
    name = models.CharField(max_length=25, verbose_name="Имя", blank=True)
    surnames = models.CharField(max_length=25, verbose_name="Фамилия", blank=True)
    sensor = models.ManyToManyField(Sensor, verbose_name="Датчик", blank=True)
    work_phone = models.CharField(null=True, verbose_name="Рабочий телефон", blank=True, max_length=20)
    email = models.EmailField(max_length=40, verbose_name="Электронная почта", blank=True)
    photo = models.ImageField(upload_to='users/%Y/%m/%d', blank=True, verbose_name="Фото",
                              default='../static/img/default.png')
    slug = models.SlugField("URL", max_length=50, blank=True)
    last_activity = models.DateTimeField(verbose_name="Последняя активность", default=timezone.now)

    @property
    def status(self):
        return "Администратор" if self.user.is_staff else "Пользователь"

    @property
    def is_online(self):
        now = timezone.now()
        return now - self.last_activity < timezone.timedelta(minutes=2)

    def __str__(self):
        return 'Профиль пользователя {}'.format(self.user.username)

    def get_absolute_url(self):
        return reverse('profile_detail', kwargs={'str': self.slug})

    def save(self, *args, **kwargs):
        self.slug = "{}".format(self.user.username)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профиля'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver
def safe_user_profile(sender, instance, *kwargs):
    instance.profile.save()


class RegistrationCode(models.Model):
    code = models.CharField('Код', max_length=10, unique=True)
    usage_count = models.IntegerField('Кол-во использований', default=0)
    max_usages = models.IntegerField('Максимальное кол-во использований')

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = 'Регистрационный код'
        verbose_name_plural = 'Регистрационный код'

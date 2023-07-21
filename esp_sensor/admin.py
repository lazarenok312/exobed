from django.contrib import admin
from .models import *


# Register your models here.
class SensorAdmin(admin.ModelAdmin):
    list_display = ['name', ]


admin.site.register(Sensor, SensorAdmin)
admin.site.register(Country)
admin.site.register(City)

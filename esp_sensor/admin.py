from django.contrib import admin
from .models import *


@admin.register(SensorLog)
class SensorLogAdmin(admin.ModelAdmin):
    list_display = ['sensor', 'previous_power', 'previous_watt', 'previous_volt', ]


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', ]
    list_display_links = ['name', ]


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', ]
    list_display_links = ['name', ]


@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}

    def countries_list(self, obj):
        return ", ".join([country.name for country in obj.country.all()])

    def cities_list(self, obj):
        return ", ".join([city.name for city in obj.city.all()])

    countries_list.short_description = "Страна"
    cities_list.short_description = "Город"

    list_display = (
        'id', 'name', 'owner', 'date_added', 'countries_list', 'cities_list', 'inclusions', 'power', 'volt', 'watt',
        'work')
    list_display_links = ['name', ]
    list_filter = ['country', 'city']
    search_fields = ['name', 'owner']
    list_editable = ['inclusions', 'power', 'watt', 'volt', 'work']

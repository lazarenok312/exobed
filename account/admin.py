from django.contrib import admin
from .models import Profile, RegistrationCode


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("user",)}
    list_display = ['id', 'user', 'photo']
    list_display_links = ['user', ]


@admin.register(RegistrationCode)
class CodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'usage_count', 'max_usages']
    list_display_links = ['code', ]

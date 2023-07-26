from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("user",)}
    list_display = ['id', 'user', 'photo']
    list_display_links = ['user', ]

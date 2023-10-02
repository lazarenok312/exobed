from django.contrib import admin
from chat.models import Message

# Register your models here.
# admin.site.register(Message)
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'message', 'is_read', ]
    list_display_links = ['message', ]
    list_editable = ['is_read']

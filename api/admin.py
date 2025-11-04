from django.contrib import admin
from .models import *
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'role', 'short_message', 'timestamp']
    list_filter = ['role', 'user']
    search_fields = ['content', 'user__username']

    def short_message(self, obj):
        return (obj.content[:50] + "...") if len(obj.content) > 50 else obj.content



@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('phn', 'dateofbirth', 'photo')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('phn', 'dateofbirth', 'photo')}),
    )

    list_display = ('username', 'email', 'phn', 'dateofbirth', 'is_staff', 'photo')
  

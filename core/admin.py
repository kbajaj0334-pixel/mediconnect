from django.contrib import admin
from .models import Hospital, Notification, ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'subject', 'is_resolved', 'created_at')
    list_filter = ('is_resolved', 'created_at')
    search_fields = ('full_name', 'email', 'subject', 'message')
    readonly_fields = ('full_name', 'email', 'subject', 'message', 'user', 'created_at')


admin.site.register(Hospital)
admin.site.register(Notification)

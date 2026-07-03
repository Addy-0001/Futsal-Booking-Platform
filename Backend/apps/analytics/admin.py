from django.contrib import admin

from .models import EventLog


@admin.register(EventLog)
class EventLogAdmin(admin.ModelAdmin):
    list_display = ("name", "path", "user", "session_id", "created_at")
    list_filter = ("name",)
    search_fields = ("name", "path", "session_id")
    date_hierarchy = "created_at"

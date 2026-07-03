from django.contrib import admin

from .models import ConsentRecord, Policy


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "version", "is_current", "published_at")
    list_filter = ("slug", "is_current")


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ("user", "policy", "ip_address", "created_at")
    list_filter = ("policy__slug",)
    readonly_fields = ("user", "policy", "ip_address", "created_at")

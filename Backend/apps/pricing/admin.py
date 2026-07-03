from django.contrib import admin

from .models import PriceRule


@admin.register(PriceRule)
class PriceRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "court", "start_time", "end_time", "price", "priority", "is_active")
    list_filter = ("is_active", "priority")
    search_fields = ("name", "court__name", "court__futsal__name")

from django.contrib import admin

from .models import Match, MatchPlayer


class MatchPlayerInline(admin.TabularInline):
    model = MatchPlayer
    extra = 0


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("format", "host", "proposed_start", "status", "max_players")
    list_filter = ("status", "format")
    inlines = [MatchPlayerInline]

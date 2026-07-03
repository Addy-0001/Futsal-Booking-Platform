from django.contrib import admin

from .models import MatchChallenge, Team, TeamMembership


class MembershipInline(admin.TabularInline):
    model = TeamMembership
    extra = 0
    autocomplete_fields = ["user"]


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "captain", "home_futsal")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = [MembershipInline]


@admin.register(MatchChallenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ("challenger_team", "opponent_team", "proposed_start", "status")
    list_filter = ("status",)

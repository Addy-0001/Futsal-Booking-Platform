from django.contrib import admin

from .models import (
    ClosureException,
    Court,
    CourtImage,
    Futsal,
    FutsalImage,
    FutsalRole,
    OperatingHours,
)


class FutsalImageInline(admin.TabularInline):
    model = FutsalImage
    extra = 0


class CourtImageInline(admin.TabularInline):
    model = CourtImage
    extra = 0


class CourtInline(admin.TabularInline):
    model = Court
    extra = 0


class FutsalRoleInline(admin.TabularInline):
    model = FutsalRole
    extra = 0
    autocomplete_fields = ["user"]


@admin.register(Futsal)
class FutsalAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "status", "created_by")
    list_filter = ("status", "city")
    search_fields = ("name", "city", "address")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [FutsalImageInline, CourtInline, FutsalRoleInline]


class OperatingHoursInline(admin.TabularInline):
    model = OperatingHours
    extra = 0


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ("name", "futsal", "surface_type", "default_price", "is_active")
    list_filter = ("surface_type", "is_active")
    search_fields = ("name", "futsal__name")
    inlines = [OperatingHoursInline, CourtImageInline]


@admin.register(FutsalRole)
class FutsalRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "futsal", "role", "granted_by")
    list_filter = ("role",)
    search_fields = ("user__email", "futsal__name")


@admin.register(ClosureException)
class ClosureExceptionAdmin(admin.ModelAdmin):
    list_display = ("court", "date", "reason")
    list_filter = ("date",)

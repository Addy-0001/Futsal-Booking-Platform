from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Exists, OuterRef

from .models import User


class AccountTypeFilter(admin.SimpleListFilter):
    """Segments users the way Sales actually needs to work the list: pure
    players vs. people already tied to a venue or a team in some way."""

    title = "account type"
    parameter_name = "account_type"

    def lookups(self, request, model_admin):
        return (
            ("owner", "Venue owner"),
            ("manager", "Venue manager"),
            ("pending_venue", "Applied to list a venue"),
            ("captain", "Team captain"),
            ("player", "Player only"),
        )

    def queryset(self, request, queryset):
        from apps.futsals.models import Futsal, FutsalRole

        value = self.value()
        if value == "owner":
            return queryset.filter(futsal_roles__role=FutsalRole.Role.OWNER).distinct()
        if value == "manager":
            return queryset.filter(futsal_roles__role=FutsalRole.Role.MANAGER).distinct()
        if value == "pending_venue":
            return queryset.filter(created_futsals__status=Futsal.Status.PENDING).distinct()
        if value == "captain":
            return queryset.filter(captained_teams__isnull=False).distinct()
        if value == "player":
            return queryset.filter(
                futsal_roles__isnull=True,
                created_futsals__isnull=True,
                captained_teams__isnull=True,
            ).distinct()
        return queryset


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = (
        "email", "phone", "full_name", "account_type",
        "is_email_verified", "is_staff", "is_active",
    )
    list_filter = (
        AccountTypeFilter, "is_staff", "groups", "is_active",
        "is_email_verified", "is_phone_verified",
    )
    search_fields = ("email", "phone", "full_name")
    readonly_fields = ("id", "date_joined", "last_login")

    def get_queryset(self, request):
        from apps.futsals.models import Futsal, FutsalRole
        from apps.teams.models import Team

        qs = super().get_queryset(request)
        return qs.annotate(
            _is_owner=Exists(
                FutsalRole.objects.filter(user=OuterRef("pk"), role=FutsalRole.Role.OWNER)
            ),
            _is_manager=Exists(
                FutsalRole.objects.filter(user=OuterRef("pk"), role=FutsalRole.Role.MANAGER)
            ),
            _venue_pending=Exists(
                Futsal.objects.filter(created_by=OuterRef("pk"), status=Futsal.Status.PENDING)
            ),
            _is_captain=Exists(Team.objects.filter(captain=OuterRef("pk"))),
        )

    @admin.display(description="Account type", boolean=False)
    def account_type(self, obj):
        tags = []
        if obj._is_owner:
            tags.append("Owner")
        if obj._is_manager:
            tags.append("Manager")
        if obj._venue_pending:
            tags.append("Venue pending")
        if obj._is_captain:
            tags.append("Captain")
        return ", ".join(tags) if tags else "Player"

    fieldsets = (
        (None, {"fields": ("id", "email", "password")}),
        ("Profile", {"fields": ("full_name", "phone")}),
        ("Verification", {"fields": ("is_email_verified", "is_phone_verified")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser",
                                    "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "phone", "full_name", "password1", "password2"),
        }),
    )

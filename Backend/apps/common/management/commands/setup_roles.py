"""
Create/refresh staff role groups with scoped admin permissions (WHMCS-style RBAC).

Booksall has exactly two kinds of *backend/admin-panel* staff:

- Sales — calls every registered user to find out if they just want to play,
  want to list their own venue, or want to partner some other way. They need
  to see who's who (users, venues, teams), not change bookings/tickets/money.
- Support — runs the ticketing system day to day. Full control over Support,
  plus enough read access on bookings/billing/accounts to actually help a
  customer.

Everyone else — players, venue managers, venue owners — never touches
/admin/ at all. Managers and owners are scoped per venue via
apps.futsals.FutsalRole, not via these groups.

Run:  python manage.py setup_roles

Then, per staff member, in the admin: set `is_staff = True` and add them to
one of these groups (Users → Permissions). Django's admin then only shows
what each role needs. Superusers keep full access regardless.
"""
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db.models import Q

# Group name -> {"full": [app_labels, full CRUD], "view": [app_labels, view-only]}
ROLE_PERMS = {
    "Sales": {
        "full": [],
        "view": ["accounts", "futsals", "teams", "matchmaking"],
    },
    "Support": {
        "full": ["support"],
        "view": ["accounts", "bookings", "billing", "futsals"],
    },
    # Broader, non-superuser operator role — full access everywhere the two
    # roles above touch, for whoever runs day-to-day ops.
    "Administrators": {
        "full": [
            "support", "billing", "futsals", "bookings", "pricing",
            "teams", "matchmaking", "accounts", "analytics", "legal",
        ],
        "view": [],
    },
}


class Command(BaseCommand):
    help = "Create/refresh the Sales, Support, and Administrators staff groups."

    def handle(self, *args, **options):
        for group_name, scope in ROLE_PERMS.items():
            group, created = Group.objects.get_or_create(name=group_name)

            conditions = []
            if scope["full"]:
                conditions.append(Q(content_type__app_label__in=scope["full"]))
            if scope["view"]:
                conditions.append(
                    Q(content_type__app_label__in=scope["view"], codename__startswith="view_")
                )

            if conditions:
                query = conditions[0]
                for extra in conditions[1:]:
                    query |= extra
                perms = Permission.objects.filter(query).distinct()
            else:
                perms = Permission.objects.none()

            group.permissions.set(perms)
            verb = "Created" if created else "Updated"
            self.stdout.write(f"{verb} '{group_name}': {perms.count()} permissions")

        self.stdout.write(
            self.style.SUCCESS(
                "\nRoles ready. For each staff member: set is_staff=True and add them "
                "to a group in the admin (Users → Permissions).\n"
                "Players, venue managers, and venue owners don't need any of "
                "this — they get their access from apps.futsals.FutsalRole instead."
            )
        )

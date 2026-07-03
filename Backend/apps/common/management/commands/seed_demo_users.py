"""
Seed a small, realistic set of demo users covering every Booksall role:

Frontend-facing (app_label-free, scoped via apps.futsals.FutsalRole /
apps.teams.TeamMembership — never touch /admin/):
  - Players            — plain accounts, no venue/team role
  - Venue manager      — FutsalRole(MANAGER) on one specific venue only
  - Venue owner        — FutsalRole(OWNER) on their own venue
  - (a second owner-applicant with a venue still PENDING review)
  - Team captain       — one of the players, so "Captain" shows up too

Backend/admin-panel-facing (is_staff=True + a Sales/Support group — see
setup_roles):
  - Sales staff
  - Support staff

Run:  python manage.py seed_demo_users

Idempotent — safe to run repeatedly; existing rows (matched by email) are
left alone and reported as skipped.
"""
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand

DEMO_PASSWORD = "Booksall#Demo1"  # noqa: S105 — seed/demo data only, never used in prod


class Command(BaseCommand):
    help = "Seed demo users covering every player/venue/team/staff role."

    def handle(self, *args, **options):
        from apps.accounts.models import User
        from apps.futsals.models import Court, Futsal, FutsalRole
        from apps.teams.models import Team

        # Make sure the Sales/Support/Administrators groups exist before we
        # try to add anyone to them.
        call_command("setup_roles")
        self.stdout.write("")

        def user(email, *, full_name, phone, is_staff=False, group=None, verified=True):
            existing = User.objects.filter(email=email).first()
            if existing:
                self.stdout.write(f"= {email} already exists, skipping")
                return existing
            u = User.objects.create_user(
                email=email,
                password=DEMO_PASSWORD,
                full_name=full_name,
                phone=phone,
                is_staff=is_staff,
                is_email_verified=verified,
                is_phone_verified=verified,
            )
            if group:
                u.groups.add(Group.objects.get(name=group))
            self.stdout.write(self.style.SUCCESS(f"+ created {email} ({full_name})"))
            return u

        # ---- Backend/admin-panel staff ------------------------------------
        sales = user(
            "sales1@staff.booksall.test", full_name="Priya Shah",
            phone="9800000001", is_staff=True, group="Sales",
        )
        support = user(
            "support1@staff.booksall.test", full_name="Rohan Basnet",
            phone="9800000002", is_staff=True, group="Support",
        )

        # ---- Players -------------------------------------------------------
        player1 = user("player1@demo.booksall.test", full_name="Aman Gurung", phone="9800000011")
        player2 = user("player2@demo.booksall.test", full_name="Sita Rai", phone="9800000012")
        user("player3@demo.booksall.test", full_name="Bikash Thapa", phone="9800000013")

        # ---- Venue owner (approved) + their venue --------------------------
        owner1 = user("owner1@demo.booksall.test", full_name="Nabin Shrestha", phone="9800000021")
        venue, venue_created = Futsal.objects.get_or_create(
            slug="kathmandu-futsal-arena",
            defaults={
                "name": "Kathmandu Futsal Arena",
                "description": "5-a-side artificial turf venue in the heart of Kathmandu.",
                "address": "Putalisadak", "city": "Kathmandu",
                "status": Futsal.Status.ACTIVE, "created_by": owner1,
            },
        )
        self.stdout.write(
            (self.style.SUCCESS if venue_created else self.style.NOTICE)(
                f"{'+ created' if venue_created else '='} venue: {venue.name}"
            )
        )
        Court.objects.get_or_create(
            futsal=venue, name="Court A",
            defaults={"surface_type": Court.Surface.ARTIFICIAL, "default_price": 1800},
        )
        FutsalRole.objects.get_or_create(user=owner1, futsal=venue, role=FutsalRole.Role.OWNER)

        # ---- Venue manager — scoped to owner1's venue only ------------------
        manager1 = user("manager1@demo.booksall.test", full_name="Kiran Adhikari", phone="9800000031")
        FutsalRole.objects.get_or_create(
            user=manager1, futsal=venue, role=FutsalRole.Role.MANAGER,
            defaults={"granted_by": owner1},
        )

        # ---- A second owner-applicant with a venue still pending review -----
        owner2 = user("owner2@demo.booksall.test", full_name="Sunita Karki", phone="9800000022")
        Futsal.objects.get_or_create(
            slug="pokhara-lakeside-futsal",
            defaults={
                "name": "Pokhara Lakeside Futsal",
                "description": "Newly submitted venue, awaiting admin review.",
                "address": "Lakeside", "city": "Pokhara",
                "status": Futsal.Status.PENDING, "created_by": owner2,
            },
        )

        # ---- A team, so "Team captain" shows up in the account-type filter --
        Team.objects.get_or_create(
            slug="thunder-fc",
            defaults={
                "name": "Thunder FC", "captain": player1, "home_futsal": venue,
                "description": "Weekend 5-a-side regulars.",
            },
        )
        if player2:
            from apps.teams.models import TeamMembership

            team = Team.objects.get(slug="thunder-fc")
            TeamMembership.objects.get_or_create(
                team=team, user=player2,
                defaults={"role": TeamMembership.Role.MEMBER, "status": TeamMembership.Status.ACTIVE},
            )

        self.stdout.write(self.style.SUCCESS(f"\nDone. Demo password for every seeded user: {DEMO_PASSWORD}"))
        self.stdout.write(
            "Sales/Support staff sign in at /admin/. Players/managers/owners sign in on the site."
        )

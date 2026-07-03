"""Seed initial draft policies so the public endpoints return content on first boot.
Replace the bodies with finalized legal text before launch (a new version row)."""
from django.db import migrations

SEED = [
    ("privacy", "Privacy Policy",
     "Booksall collects the minimum data needed to operate bookings — your name, "
     "email, and phone number — plus booking and usage records. We do not sell your "
     "data. This is placeholder text; replace with your finalized policy before launch."),
    ("terms", "Terms & Conditions",
     "By using Booksall you agree to these terms. Bookings are subject to venue "
     "approval and venue cancellation policies. This is placeholder text; replace with "
     "your finalized terms before launch."),
    ("cookies", "Cookie Policy",
     "Booksall uses essential cookies to keep you signed in and remember preferences. "
     "This is placeholder text; replace with your finalized cookie policy before launch."),
]


def seed(apps, schema_editor):
    Policy = apps.get_model("legal", "Policy")
    for slug, title, body in SEED:
        Policy.objects.get_or_create(
            slug=slug, version=1,
            defaults={"title": title, "body": body, "is_current": True},
        )


def unseed(apps, schema_editor):
    Policy = apps.get_model("legal", "Policy")
    Policy.objects.filter(version=1, slug__in=[s for s, _, _ in SEED]).delete()


class Migration(migrations.Migration):
    dependencies = [("legal", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]

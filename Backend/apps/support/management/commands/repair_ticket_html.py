"""
Repair ticket messages/replies whose HTML got escaped or double-encoded — data
created before the HTML sanitizer (nh3) was installed, which the fallback escaped
(e.g. `<p>&lt;p&gt;hi&lt;/p&gt;</p>`). Decodes the escaped tags and re-sanitizes.

Run:  python manage.py repair_ticket_html         (apply)
      python manage.py repair_ticket_html --dry-run
"""
import html
import re

from django.core.management.base import BaseCommand

from apps.common.sanitize import sanitize_html
from apps.support.models import SupportTicket, TicketReply

# Matches an ESCAPED html tag like &lt;p ... &lt;/div — not a lone "a &lt; b".
_ESCAPED_TAG = re.compile(r"&lt;/?[a-zA-Z]")


def _looks_escaped(s):
    return bool(s) and bool(_ESCAPED_TAG.search(s))


def _deep_unescape(s):
    prev = None
    while prev != s and _looks_escaped(s):
        prev = s
        s = html.unescape(s)
    return s


class Command(BaseCommand):
    help = "Fix ticket messages/replies whose HTML was escaped/double-encoded."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true",
                            help="Report what would change without saving.")

    def handle(self, *args, **options):
        dry = options["dry_run"]
        fixed = 0
        for model, field in ((SupportTicket, "message"), (TicketReply, "body")):
            for obj in model.objects.all():
                val = getattr(obj, field) or ""
                if not _looks_escaped(val):
                    continue
                new = sanitize_html(_deep_unescape(val))
                if new != val:
                    fixed += 1
                    self.stdout.write(f"{model.__name__} {obj.pk}: repaired")
                    if not dry:
                        setattr(obj, field, new)
                        obj.save(update_fields=[field, "updated_at"])
        verb = "Would repair" if dry else "Repaired"
        self.stdout.write(self.style.SUCCESS(f"{verb} {fixed} record(s)."))

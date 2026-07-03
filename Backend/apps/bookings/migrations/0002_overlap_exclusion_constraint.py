"""
Postgres-only: make two overlapping ACTIVE bookings on the same court physically
impossible via a GiST exclusion constraint over tstzrange(start_at, end_at).

This is the hard guarantee behind the booking concurrency model (design doc §5).
On non-Postgres backends (e.g. the SQLite dev fallback) this migration is a no-op;
the application-level overlap check in services.py still applies there.
"""
from django.db import migrations

CREATE_SQL = """
CREATE EXTENSION IF NOT EXISTS btree_gist;

ALTER TABLE bookings_booking
    ADD CONSTRAINT no_overlapping_active_booking
    EXCLUDE USING gist (
        court_id WITH =,
        tstzrange(start_at, end_at) WITH &&
    )
    WHERE (status IN ('PENDING_APPROVAL', 'APPROVED'));
"""

DROP_SQL = """
ALTER TABLE bookings_booking DROP CONSTRAINT IF EXISTS no_overlapping_active_booking;
"""


def apply_constraint(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(CREATE_SQL)


def drop_constraint(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(DROP_SQL)


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(apply_constraint, drop_constraint),
    ]

# Booksall — Backend

Django + DRF API for the Booksall futsal booking platform. See `../Documentation/BACKEND_DESIGN.md` for the full design.

## Phase 0 (current)

Foundation: custom `User` (UUID, email + Nepali phone), JWT auth (login / register / refresh / logout-blacklist), email verification, 30-minute single-use password reset, CORS, throttling, uniform error envelope, Sentry (prod), health check, OpenAPI docs.

## Local setup (venv + Postgres)

```bash
cd Backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                # then edit SECRET_KEY, DATABASE_URL, etc.

# First boot works on sqlite if you leave DATABASE_URL unset.
# For Postgres, create the db/user to match DATABASE_URL first:
#   createdb booksall && createuser booksall --pwprompt

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Settings default to `config.settings.dev` (via `manage.py`). Use `DJANGO_SETTINGS_MODULE=config.settings.prod` in production.

## Key endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/register/` | Create account, sends verification email |
| POST | `/api/auth/login/` | JWT access + refresh + user |
| POST | `/api/auth/refresh/` | Rotate access token |
| POST | `/api/auth/logout/` | Blacklist refresh token |
| GET/PATCH | `/api/auth/me/` | Current user (self only) |
| POST | `/api/auth/verify-email/` | Confirm email with uid + token |
| POST | `/api/auth/password-reset/` | Request reset link (no enumeration) |
| POST | `/api/auth/password-reset/confirm/` | Set new password (30-min, single-use token) |
| GET | `/api/docs/` | Swagger UI |
| GET | `/healthz/` | Health check |

### Phase 1 — futsals & pricing

| Method | Path | Purpose |
|---|---|---|
| GET/POST | `/api/futsals/` | List active venues (public) / create (creator becomes OWNER) |
| GET/PATCH/DELETE | `/api/futsals/{slug}/` | Venue detail (public) / edit (staff) / delete (owner) |
| * | `/api/courts/` | Courts per venue (writes: staff) |
| * | `/api/operating-hours/` | Per-weekday availability windows (writes: staff) |
| * | `/api/closures/` | One-off closures (writes: staff) |
| * | `/api/futsal-roles/` | Grant/revoke owner & manager roles (owner only; guards last owner) |
| * | `/api/price-rules/` | Dynamic pricing rules (staff only) |
| GET | `/api/pricing/quote/?court=<uuid>&start=<iso>` | Server-authoritative slot price (public) |

### Phase 2 — bookings

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/bookings/` | Create booking (PENDING_APPROVAL; validates past-slot, operating hours, overlap; snapshots price) |
| GET | `/api/bookings/` | List (player: own; staff: their venues' bookings) |
| GET | `/api/bookings/{id}/` | Detail (party only) |
| POST | `/api/bookings/{id}/cancel/` | Cancel (player or staff) — frees the slot |
| POST | `/api/bookings/{id}/reschedule/` | Move slot, re-enters PENDING (player) |
| POST | `/api/bookings/{id}/approve/` | Approve (venue staff only) |
| POST | `/api/bookings/{id}/reject/` | Reject (venue staff only) |
| GET | `/api/availability/?court=<uuid>&date=YYYY-MM-DD[&slot_minutes=60]` | Public slot grid: per-slot price + free/taken/past (occupied slots anonymized) |

### Phase 4 — matchmaking & teams

| Method | Path | Purpose |
|---|---|---|
| GET/POST | `/api/matches/` | Browse open pickup matches (public) / host one (auto-joins) |
| POST | `/api/matches/{id}/join/` | Join (blocks when full → 409; auto-flips to FULL) |
| POST | `/api/matches/{id}/leave/` | Leave (reopens a full match; host can't leave) |
| POST | `/api/matches/{id}/cancel/` | Cancel (host only) |
| GET/POST | `/api/teams/` | Browse teams (public) / create (creator = captain) |
| POST | `/api/teams/{slug}/invite/` | Invite a user (captain) |
| POST | `/api/teams/{slug}/accept-invite/` | Accept an invite (invitee) |
| POST | `/api/teams/{slug}/leave/` | Leave team (non-captain) |
| GET/POST | `/api/challenges/` | Team-vs-team challenges (the "war" flow) — propose (challenger captain) |
| POST | `/api/challenges/{id}/accept` `/decline` | Respond (opponent captain) |
| POST | `/api/challenges/{id}/result` | Record score → PLAYED (participating captain) |
| POST | `/api/challenges/{id}/cancel` | Cancel (challenger captain) |

### Phase 5 — legal, analytics, support

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/policies/` · `/api/policies/{slug}/` | Current legal policies (public; seeded: privacy/terms/cookies) |
| POST | `/api/consent/` | Record consent (anon or user) for a policy slug/version |
| POST | `/api/events/` | First-party event/page-view ingest (anon, throttled) |
| POST | `/api/support-tickets/` | File a support/bug/feedback ticket (public) |
| GET/PATCH | `/api/support-tickets/` | Triage tickets (platform staff only) |

**Concurrency:** non-overlap is enforced by a Postgres `btree_gist` exclusion constraint over
`tstzrange(start_at, end_at)` scoped to active statuses (migration `0002`, Postgres-only — no-op on
SQLite). The service layer adds a per-court row lock + overlap pre-check for friendly errors. The
true parallel-race test (`ConcurrencyTests`) runs only on PostgreSQL; run the suite on Postgres to
exercise it.

## Tests

```bash
python manage.py test
```

## Next phases

Phase 1 ✓ — `futsals` + `pricing` (Futsal, Court, OperatingHours, ClosureException, FutsalRole, PriceRule + resolution engine).
Phase 2 ✓ — `bookings` with the Postgres exclusion-constraint concurrency model, approval workflow, cancel/reschedule, Celery cleanup jobs.
Phase 3 — `notifications` (deferred; Nest SMS planned). Booking events currently log via `bookings/notifications.py`.
Phase 4 ✓ — `matchmaking` (open pickup matches) + `teams` (teams, memberships, team-vs-team challenge/"war" flow).
Phase 5 ✓ — `legal` (versioned policies + consent records, seeded), `analytics` (event/page-view ingest), `support` (tickets/bug reports).
Phase 6 — payments (cash-first now; drop in Khalti/eSewa later). SMS via Nest (deferred).
See the design doc for the full roadmap.

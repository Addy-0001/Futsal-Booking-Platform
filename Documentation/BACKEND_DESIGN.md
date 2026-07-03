# Booksall — Backend Design & Build Plan

**Stack decision:** Django + Django REST Framework, JWT auth, PostgreSQL, Redis + Celery. Vue.js SPA frontend (separate origin).
**Launch assumption:** Nepal market, **cash / pay-at-futsal first** (no payment gateway in v1, but the schema is gateway-ready). API style: **DRF REST + JWT**.

---

## 1. Guiding principles

- **Postgres does the hard guarantees, not Python.** Double-booking, past-slot, and duplicate-booking protection live in DB constraints + transactions. Application checks are a UX nicety on top, never the source of truth.
- **Modular Django apps**, one bounded context each. Keep `bookings` ignorant of `payments` internals, talk via services/signals.
- **Server is the only authority on price and availability.** The client never sends a price; it sends a slot and the server computes the price.
- **Everything user-scoped goes through an object-level permission.** A user can only touch their own rows unless RBAC says otherwise.
- **Cash-first but money-ready.** Model `Payment` now even though v1 settles in cash, so adding Khalti/eSewa later is a new `provider`, not a migration of the booking flow.

---

## 2. Recommended tech stack

| Concern | Choice | Why |
|---|---|---|
| Framework | Django 5.x + DRF | You know it; batteries included; strong ORM for the constraint work below |
| DB | PostgreSQL 15+ | Exclusion constraints, `tstzrange`, row locking — essential for booking integrity |
| Auth | `djangorestframework-simplejwt` | JWT access/refresh, rotation, blacklist |
| Async/queue | Celery + Redis | SMS sending, reminders, webhook retries, reconciliation |
| Scheduling | Celery Beat | SMS reminders, slot generation, cleanup jobs |
| Cache / locks | Redis | Rate limiting, short-lived advisory locks, caching price rules |
| SMS | Sparrow SMS or Aakash SMS (NP providers) behind an adapter interface | Local providers; abstract so you can swap |
| Email | Anymail + (Mailgun/SES) | Verification, password reset |
| API docs | drf-spectacular | OpenAPI schema for the Vue team |
| Rate limit | DRF throttling + `django-ratelimit` | Per-endpoint and per-IP |
| Errors | Sentry | Critical-failure alerting |
| Container | Docker + docker-compose (dev), same image prod | Blue/green needs identical artifacts |

---

## 3. Project & app structure

```
booksall/
  config/                 # settings split: base / dev / prod, urls, celery, asgi/wsgi
    settings/
      base.py
      dev.py
      prod.py
  apps/
    accounts/             # custom User, profiles, email/phone verification, RBAC roles
    futsals/              # Futsal, courts, ownership, managers, operating hours
    pricing/              # PriceRule, time brackets, surge / weekend pricing
    bookings/             # Booking, slot logic, approval workflow, conflict resolution
    teams/                # Team, membership, match challenges (the "war" system)
    matchmaking/          # open matches, join requests
    notifications/        # SMS/email dispatch, templates, delivery tracking
    payments/             # Payment, ledger (cash now, gateway-ready)
    legal/                # policy pages, consent records
    analytics/            # event + page tracking ingestion
    common/               # base models, mixins, permissions, exceptions, pagination
  manage.py
```

Rules of thumb: each app owns its models + serializers + services + permissions. Cross-app calls go through a thin `services.py`, never by importing another app's views.

---

## 4. Data model (the parts that matter)

### 4.1 Accounts & RBAC

Use a **custom User** from day one (`AbstractUser`, `email` as login, `phone` required & unique). Don't retrofit this later — it's painful.

```
User(id=UUID, email unique, phone unique, is_email_verified, is_phone_verified, ...)
```

Roles are **contextual**, not global. "Manager" means manager *of futsal X*, so model it as a relation, not a flag:

```
FutsalRole(user, futsal, role[OWNER|MANAGER], granted_by, created_at)
  unique(user, futsal, role)
```

A platform-wide `is_staff`/`is_superuser` stays for Booksall admins only. Every "can this user act on this futsal?" check reads `FutsalRole`. This cleanly handles your owner/manager requirements:

- One owner → many futsals: many `FutsalRole(OWNER)` rows for that user.
- One futsal → many owners: many OWNER rows pointing at the same futsal.
- Managers: same table, `role=MANAGER`.

### 4.2 Futsals & courts

A futsal venue can physically have more than one playing court/ground; bookings are per **court**, not per venue. Model it now even if most start with one.

```
Futsal(id=UUID, name, address, geo(lat,lng), description, status, timezone='Asia/Kathmandu', created_by)
Court(id=UUID, futsal, name, surface_type, is_active)
OperatingHours(court, weekday, open_time, close_time)   # availability window per day
ClosureException(court, date, reason)                    # holidays / maintenance
```

### 4.3 Pricing (dynamic / surge)

Don't store a price on the court. Store **rules** and resolve the price at booking time. This gives morning/day/night and weekend/weekend-surge pricing without code changes.

```
PriceRule(
  court, name,
  days_of_week,            # e.g. [SAT] or [MON..FRI]  (array / bitmask)
  start_time, end_time,    # the time bracket, e.g. 18:00–22:00 night
  price,                   # NPR per slot
  priority,                # higher wins on overlap
  valid_from, valid_to,    # optional seasonal windows
  is_active
)
```

Resolution: given a court + slot start, pick active rules matching weekday and covering the time, order by `priority` desc, take the first. Have a `DefaultPrice` fallback per court so a slot is never unpriced. **Snapshot the resolved price onto the Booking** (`price_at_booking`) so later rule edits never rewrite history.

### 4.4 Bookings — schema

Represent the booked period as a real time range so Postgres can enforce non-overlap.

```
Booking(
  id=UUID,
  court (FK),
  user (FK),
  slot (tstzrange)         # [start, end) in UTC, store venue tz separately for display
  status,                  # PENDING_APPROVAL → APPROVED / REJECTED / CANCELLED / EXPIRED / COMPLETED
  price_at_booking,
  payment_method,          # CASH (v1)
  created_at, updated_at,
  approved_by, approved_at,
  cancellation_reason,
)
```

Status lifecycle:

```
                 ┌────────────► REJECTED
PENDING_APPROVAL ┤
                 ├────────────► APPROVED ──► COMPLETED (after play time)
                 └──(timeout)──► EXPIRED         │
   user cancels at any pre-play point ───────────┴──► CANCELLED
```

---

## 5. Booking concurrency — the core engineering problem

This is where most booking apps quietly break. Solve it at the database level. Four of your guardrails map directly to one Postgres feature plus a transaction pattern.

### 5.1 Prevent two overlapping bookings on the same court (your points 1, 3, 4)

Use a **`btree_gist` exclusion constraint**. It makes overlapping active bookings *physically impossible* — the database rejects the second writer regardless of timing, race, or retries.

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;

ALTER TABLE bookings_booking
ADD CONSTRAINT no_overlapping_active_booking
EXCLUDE USING gist (
  court_id WITH =,
  slot     WITH &&
) WHERE (status IN ('PENDING_APPROVAL', 'APPROVED'));
```

In Django (5.x supports this natively):

```python
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import RangeOperators, DateTimeRangeField

class Booking(models.Model):
    slot = DateTimeRangeField()
    class Meta:
        constraints = [
            ExclusionConstraint(
                name="no_overlapping_active_booking",
                expressions=[("court", RangeOperators.EQUAL),
                             ("slot", RangeOperators.OVERLAPS)],
                condition=Q(status__in=["PENDING_APPROVAL", "APPROVED"]),
            )
        ]
```

The `WHERE` clause is important: a cancelled/rejected/expired booking must *not* block a new one for the same slot.

> **As implemented (Phase 2):** the booking stores two UTC columns `start_at`/`end_at` (portable across the SQLite dev fallback and Postgres) instead of a `DateTimeRangeField`, and the exclusion constraint is added in a vendor-guarded migration using `tstzrange(start_at, end_at)` directly: `EXCLUDE USING gist (court_id WITH =, tstzrange(start_at, end_at) WITH &&) WHERE (status IN ('PENDING_APPROVAL','APPROVED'))`. The DB-level guarantee is identical; only the Django field representation differs. On non-Postgres backends the constraint migration is a no-op and the application-level overlap check provides the (non-concurrent) protection.

### 5.2 The write path

```python
with transaction.atomic():
    court = Court.objects.select_for_update().get(pk=court_id)   # serialize per court
    validate_not_in_past(slot)                                   # point 2
    validate_within_operating_hours(court, slot)
    price = resolve_price(court, slot)                           # server-authoritative
    try:
        booking = Booking.objects.create(court=court, user=user,
                                         slot=slot, price_at_booking=price,
                                         status="PENDING_APPROVAL")
    except IntegrityError:                                       # exclusion constraint hit
        raise SlotTakenError("That slot was just taken.")        # point 4 resolution
```

The `IntegrityError` catch **is** your conflict-resolution path: if two users submit the same slot in the same millisecond, exactly one commits and the other gets a clean, deterministic "slot taken" — no double booking, no manual cleanup. The same applies to one user double-submitting (point 1): their second request just loses.

### 5.3 No past bookings (your point 2)

Two layers: a serializer validator (`slot.lower > timezone.now()` with a small grace buffer) for a friendly error, and a DB `CHECK` as backstop. Always compare in UTC; convert from `Asia/Kathmandu` at the edge.

### 5.4 Reschedule (change booking time)

Treat reschedule as *cancel-and-rebook inside one transaction* so the exclusion constraint validates the new slot. Don't mutate `slot` in place without re-running availability — wrap it the same way, and if the new slot collides, the whole transaction rolls back and the original stays intact.

### 5.5 Slot model: free-form vs fixed grid

Recommend **fixed grid slots** (e.g. 1-hour blocks aligned to the court's operating hours). It makes the UI a clean grid, makes pricing brackets trivial, and avoids weird 17-minute overlaps. The `tstzrange` still does the enforcement; the grid just constrains what ranges are offerable.

### 5.6 Stale-pending cleanup

A Celery Beat job moves `PENDING_APPROVAL` bookings older than, say, 2 hours (or past their slot start) to `EXPIRED`, freeing the slot. This stops abandoned pending bookings from locking inventory.

---

## 6. Approval workflow + notifications (your point 7)

```
Player creates booking ──► status=PENDING_APPROVAL
        │
        └─► Celery task: notify all FutsalRole(MANAGER|OWNER) of that futsal (SMS + in-app + email)
Manager approves/rejects (object-permission checked) ──► status=APPROVED/REJECTED
        │
        └─► Celery task: notify the player (SMS + in-app)
```

Keep notification dispatch **async** (Celery) so a slow SMS gateway never blocks the booking request. Record every send in `notifications` with delivery status for the bulk-SMS dashboard.

---

## 7. Teams & matchmaking (the "Clash of Clans war" system)

Two separate but linked features. Ship open-match matchmaking first (replaces the Facebook-group behaviour); add the team-vs-team layer second.

### 7.1 Open matches (individual matchmaking)

```
Match(id, court?, proposed_slot, host_user, format(5s/7s), skill_level, max_players, status[OPEN|FULL|CONFIRMED|CANCELLED], notes)
MatchPlayer(match, user, status[JOINED|LEFT|REMOVED])
```

A player posts an open match (optionally tied to a real booking); others join until full. When full, host can convert it into an actual court Booking.

### 7.2 Teams & challenges (war system)

```
Team(id=UUID, name unique, logo, captain(User), home_futsal?, created_at)
TeamMembership(team, user, role[CAPTAIN|MEMBER], status[INVITED|ACTIVE|LEFT], joined_at)
   unique(team, user)
MatchChallenge(
  challenger_team, opponent_team,
  proposed_slot, court?,
  status[PROPOSED|ACCEPTED|DECLINED|SCHEDULED|PLAYED|CANCELLED],
  result(optional: scores),
  created_by, responded_by
)
```

Flow mirrors a war declaration: Team A challenges Team B → B accepts → on acceptance, create a real court `Booking` for the slot (reusing the §5 transaction so it can't double-book) → after play, record result. Add a simple `TeamStats` (wins/losses/points) materialised from played challenges for a ladder/leaderboard later.

---

## 8. SMS & notification system (your "nice to have" 1–3)

Build one **notification service** with pluggable channels; SMS is one channel.

```
notifications/
  providers/base.py        # send(to, body) interface
  providers/sparrow.py     # concrete NP provider
  models: NotificationTemplate, NotificationLog(recipient, channel, template, status, provider_msg_id, sent_at)
  tasks.py                 # Celery: send_sms, send_bulk_sms, send_reminder
```

- **Event reminders:** on `APPROVED`, schedule a Celery task (eta = slot_start − 2h) to SMS the player.
- **Bulk SMS:** an admin endpoint that fans out via Celery with rate-limited batches; every message logged in `NotificationLog` for the dashboard (sent/failed/delivered counts).
- Keep templates in the DB so non-devs can edit copy; render with a safe template engine, never f-strings on user input.

---

## 9. Security — mapped to your checklist

| Your requirement | Implementation |
|---|---|
| Lock users to their UUID unless RBAC | DRF object-level permissions on every viewset; default queryset filtered to `request.user`; `FutsalRole` gate for futsal-scoped actions. Use UUID PKs so IDs aren't enumerable. |
| Password reset links expire in 30 min | Signed token (`itsdangerous`/Django signer) with 1800s max-age, single-use (store a hash + `used_at`), invalidate on use. |
| SQL-injection prevention | Use the ORM/parameterised queries exclusively; never string-format SQL. DRF serializers validate/sanitise all input. |
| CORS | `django-cors-headers`, explicit `CORS_ALLOWED_ORIGINS` (your Vue domains only), no wildcard in prod. |
| Rate limiting | DRF throttle classes (per-user, per-IP, scoped on auth & booking endpoints) + `django-ratelimit` on login/reset to stop brute force. |
| Custom error handling | DRF custom exception handler → uniform JSON error envelope; never leak stack traces; `DEBUG=False`; custom 4xx/5xx pages. |
| Logging & monitoring + alerts | Structured JSON logging, Sentry for exceptions with alert rules on 5xx spikes & Celery failures, health-check endpoint, uptime monitor. |
| Blue/green for rollback | Two identical environments behind a load balancer; deploy to idle (green), run migrations backward-compatible, smoke-test, switch traffic, keep blue warm for instant rollback. See §11. |

Additional baseline you should also include: HTTPS only (`SECURE_SSL_REDIRECT`, HSTS), `HttpOnly`/`Secure` cookies if any, JWT short access + rotating refresh with blacklist on logout, secrets in env (never in repo), `ALLOWED_HOSTS` locked, security headers (`SECURE_*`, CSP via `django-csp`), and audit logging on sensitive actions (approvals, role grants, cancellations).

---

## 10. Legal, analytics, marketing, feedback

- **Legal app:** `Policy(slug, title, body, version, published_at)` for Privacy, Terms, Cookie, Refund/Cancellation pages — versioned so you can prove what a user agreed to. `ConsentRecord(user, policy_version, accepted_at, ip)` for cookie/ToS consent.
- **Analytics:** lightweight `EventLog(user?, name, props(jsonb), session_id, ts)` ingestion endpoint for user-event + page tracking; or wire a hosted tool (PostHog/GA4) from the Vue side and keep server events for booking funnels.
- **Marketing/SEO:** SEO largely lives in the Vue/SSR layer; backend exposes clean canonical URLs, sitemap.xml, robots.txt, and Open Graph metadata endpoints. Register Google Search Console after launch.
- **Feedback loop:** `SupportTicket`/`BugReport(reporter?, type, message, url, status)` model + a simple admin dashboard; contact/support email piped to a shared inbox.

---

## 11. Deployment & ops (blue/green)

- **One Docker image**, environment-driven config. Dev via docker-compose (web, postgres, redis, celery worker, celery beat).
- **Migrations must be backward-compatible** (expand/contract pattern) so green can run new code against a schema blue still understands — this is what makes instant rollback safe.
- **Blue/green:** LB (Nginx/managed) points at blue; deploy green; migrate; smoke-test green; flip LB; if anything's wrong, flip back to blue. Don't drop old columns until the next release confirms green is healthy.
- **Backups:** automated nightly Postgres dumps + PITR if your host supports it. Booking/payment data is not something you can lose.
- Health endpoints (`/healthz` DB+Redis check) for the LB and uptime monitor.

---

## 12. How to get started — phased roadmap

Build in this order; each phase is shippable.

**Phase 0 — Foundation (week 1)**
Repo + Docker + settings split + Postgres/Redis. Custom `User` (UUID, email+phone). JWT auth, signup/login, email verification, password reset (30-min token). CORS, throttling, Sentry, custom exception handler, health check. *Get auth bulletproof before anything else — it's the thing you can't safely change later.*

**Phase 1 — Futsal core (week 2)**
`futsals` + `pricing`. Futsal/Court/OperatingHours CRUD. `FutsalRole` (owner/manager) + object permissions. PriceRule + price-resolution service with tests.

**Phase 2 — Bookings (weeks 3–4) — the heart**
`btree_gist` exclusion constraint, the transactional write path, past-slot + operating-hours validation, price snapshotting. Approval workflow (pending → approve/reject). Cancel + reschedule. Stale-pending cleanup job. **Write concurrency tests that fire parallel requests at the same slot and assert exactly one wins.**

**Phase 3 — Notifications (week 5)**
Celery + Redis, SMS adapter (Sparrow/Aakash), notification logging, booking + approval + reminder messages.

**Phase 4 — Social (weeks 6–7)**
Open matchmaking first, then teams + challenges (war system) reusing the booking transaction.

**Phase 5 — Compliance & polish (week 8)**
Legal/consent, analytics events, support/bug reporting, SEO endpoints, bulk-SMS dashboard.

**Phase 6 — Payments (later)**
Drop in Khalti/eSewa as a `Payment.provider` with webhook handling + reconciliation, when you're ready to move off cash.

### First concrete steps this week

1. `django-admin startproject` with the settings split; add Docker + Postgres + Redis.
2. Build the custom `User` and lock it in with the first migration **before** writing any other model.
3. Stand up JWT auth + email verification + 30-min reset.
4. Spike the booking exclusion constraint in a throwaway branch and write the parallel-request test — proving the concurrency model early de-risks the whole project.

---

## 13. Key packages

`djangorestframework`, `djangorestframework-simplejwt`, `psycopg[binary]`, `celery`, `redis`, `django-celery-beat`, `django-cors-headers`, `django-ratelimit`, `drf-spectacular`, `django-anymail`, `sentry-sdk`, `django-csp`, `python-decouple`/`django-environ`, `django-filter`.

---

*Open question for v1 scope: confirm whether a single venue can have multiple courts at launch (recommended to model now even if unused), and your SMS provider choice (Sparrow vs Aakash) so the adapter can be written against a real API.*

"""
Template helpers for the Booksall admin top navbar.

``group_nav_apps`` turns Django's flat, alphabetical ``available_apps`` list
(the same data ``admin/app_list.html`` renders) into a small, fixed set of
WHMCS-style menu groups — Sales, Support, Users, System, and a Misc catch-all
for anything we haven't explicitly categorised yet. New apps/models show up
automatically (in Misc, until someone adds them to ``_APP_TO_GROUP`` below),
so this never silently drops navigation as the project grows.
"""
from django.template import Library
from django.utils.safestring import mark_safe

register = Library()

# Which Django app_label belongs in which nav group. Anything not listed
# here falls into "misc" so it's never lost, just uncategorised.
_APP_TO_GROUP = {
    "bookings": "sales",
    "billing": "sales",
    "pricing": "sales",
    "support": "support",
    "accounts": "users",
    "auth": "users",
    "teams": "users",
    "futsals": "system",
    "matchmaking": "system",
    "legal": "system",
    "analytics": "system",
    "common": "system",
}

# Order they appear in the navbar, left to right.
_GROUP_ORDER = ["sales", "support", "users", "system", "misc"]

_GROUP_META = {
    "sales": {"label": "Sales", "icon": "sales", "highlight": True},
    "support": {"label": "Support", "icon": "support", "highlight": True},
    "users": {"label": "Users", "icon": "users", "highlight": False},
    "system": {"label": "System", "icon": "system", "highlight": False},
    "misc": {"label": "Misc", "icon": "misc", "highlight": False},
}


@register.simple_tag(takes_context=True)
def group_nav_apps(context):
    """Return available_apps grouped for the navbar, each app/model flagged
    with ``is_active`` against the current request path (same technique
    Django's own admin/app_list.html uses)."""
    request = context.get("request")
    path = getattr(request, "path", "") or ""
    available_apps = context.get("available_apps") or []

    groups = {key: {**meta, "key": key, "apps": [], "is_active": False} for key, meta in _GROUP_META.items()}

    for app in available_apps:
        app = dict(app)
        app_active = app.get("app_url", "\0") in path
        models = []
        for model in app.get("models", []):
            model = dict(model)
            model["is_active"] = bool(model.get("admin_url")) and model["admin_url"] in path
            app_active = app_active or model["is_active"]
            models.append(model)
        app["models"] = models
        app["is_active"] = app_active

        group_key = _APP_TO_GROUP.get(app.get("app_label"), "misc")
        groups[group_key]["apps"].append(app)
        if app_active:
            groups[group_key]["is_active"] = True

    return [groups[key] for key in _GROUP_ORDER if groups[key]["apps"]]


_ICONS = {
    "home": (
        '<path d="M3 10.5 12 3l9 7.5"/>'
        '<path d="M5 9.5V20a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1V9.5"/>'
    ),
    "sales": (
        '<rect x="2.5" y="6" width="19" height="12" rx="2"/>'
        '<circle cx="12" cy="12" r="2.5"/>'
        '<path d="M6 6v-.5A1.5 1.5 0 0 1 7.5 4h9A1.5 1.5 0 0 1 18 5.5V6"/>'
    ),
    "support": (
        '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3.5"/>'
        '<path d="m5.6 5.6 3.3 3.3M18.4 5.6l-3.3 3.3M5.6 18.4l3.3-3.3M18.4 18.4l-3.3-3.3"/>'
    ),
    "users": (
        '<circle cx="9" cy="8" r="3.25"/><path d="M2.75 19.25c0-3.2 2.8-5.5 6.25-5.5s6.25 2.3 6.25 5.5"/>'
        '<path d="M16 4.8c1.5.4 2.6 1.7 2.6 3.3s-1.1 2.9-2.6 3.3M18.6 13.9c2.2.6 3.65 2.3 3.65 4.4"/>'
    ),
    "system": (
        '<circle cx="12" cy="12" r="3"/>'
        '<path d="M19.4 13.5a7.7 7.7 0 0 0 0-3l2-1.4-2-3.4-2.3.8a7.6 7.6 0 0 0-2.6-1.5L14 2.5h-4l-.5 2.5a7.6 7.6 0 0 0-2.6 1.5l-2.3-.8-2 3.4 2 1.4a7.7 7.7 0 0 0 0 3l-2 1.4 2 3.4 2.3-.8c.75.65 1.63 1.16 2.6 1.5l.5 2.5h4l.5-2.5a7.6 7.6 0 0 0 2.6-1.5l2.3.8 2-3.4-2-1.4Z"/>'
    ),
    "misc": (
        '<circle cx="5.5" cy="5.5" r="1.75"/><circle cx="12" cy="5.5" r="1.75"/><circle cx="18.5" cy="5.5" r="1.75"/>'
        '<circle cx="5.5" cy="12" r="1.75"/><circle cx="12" cy="12" r="1.75"/><circle cx="18.5" cy="12" r="1.75"/>'
        '<circle cx="5.5" cy="18.5" r="1.75"/><circle cx="12" cy="18.5" r="1.75"/><circle cx="18.5" cy="18.5" r="1.75"/>'
    ),
    # Single-person avatar for the "my account" menu — deliberately distinct
    # from the two-person "users" icon used for the Users nav group.
    "account": (
        '<circle cx="12" cy="12" r="9"/>'
        '<circle cx="12" cy="10" r="3"/>'
        '<path d="M6.2 18.1a6.1 6.1 0 0 1 11.6 0"/>'
    ),
}


@register.simple_tag
def nav_icon(name):
    body = _ICONS.get(name, "")
    svg = (
        '<svg class="bk-navicon" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        f"{body}</svg>"
    )
    return mark_safe(svg)

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


# Admin branding (shown in the <title>, header, and login screen).
admin.site.site_header = "Booksall"
admin.site.site_title = "Booksall Admin"
admin.site.index_title = "Control room"

# We use a WHMCS-style top navbar (see templates/admin/base_site.html) instead
# of Django's default collapsible left sidebar — admins work on laptops, so
# there's no need for a mobile-friendly collapsing drawer.
admin.site.enable_nav_sidebar = False


def healthz(_request):
    """Lightweight health check for the load balancer / uptime monitor."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", healthz, name="healthz"),
    # API
    path("api/auth/", include("apps.accounts.urls")),
    path("api/", include("apps.futsals.urls")),
    path("api/", include("apps.pricing.urls")),
    path("api/", include("apps.bookings.urls")),
    path("api/", include("apps.billing.urls")),
    path("api/", include("apps.matchmaking.urls")),
    path("api/", include("apps.teams.urls")),
    path("api/", include("apps.legal.urls")),
    path("api/", include("apps.analytics.urls")),
    path("api/", include("apps.support.urls")),
    # Schema / docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]

# CKEditor 5 image-upload endpoint (only when the package is installed).
if getattr(settings, "CKEDITOR_5_AVAILABLE", False):
    urlpatterns += [path("ckeditor5/", include("django_ckeditor_5.urls"))]

# Serve uploaded media in development. In production, serve MEDIA from object
# storage / a CDN (S3, etc.) instead of Django.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

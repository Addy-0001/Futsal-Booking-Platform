from django.urls import path
from rest_framework.routers import DefaultRouter

from .availability import AvailabilityView
from .views import BookingViewSet

router = DefaultRouter()
router.register("bookings", BookingViewSet, basename="booking")

urlpatterns = [
    path("availability/", AvailabilityView.as_view(), name="availability"),
    *router.urls,
]

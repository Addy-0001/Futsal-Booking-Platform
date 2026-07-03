from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ConsentView, PolicyViewSet

router = DefaultRouter()
router.register("policies", PolicyViewSet, basename="policy")

urlpatterns = [
    path("consent/", ConsentView.as_view(), name="consent"),
    *router.urls,
]

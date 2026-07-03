from rest_framework.routers import DefaultRouter

from .views import (
    ClosureExceptionViewSet,
    CourtImageViewSet,
    CourtViewSet,
    FutsalImageViewSet,
    FutsalRoleViewSet,
    FutsalViewSet,
    OperatingHoursViewSet,
)

router = DefaultRouter()
router.register("futsals", FutsalViewSet, basename="futsal")
router.register("courts", CourtViewSet, basename="court")
router.register("operating-hours", OperatingHoursViewSet, basename="operatinghours")
router.register("closures", ClosureExceptionViewSet, basename="closure")
router.register("futsal-images", FutsalImageViewSet, basename="futsalimage")
router.register("court-images", CourtImageViewSet, basename="courtimage")
router.register("futsal-roles", FutsalRoleViewSet, basename="futsalrole")

urlpatterns = router.urls

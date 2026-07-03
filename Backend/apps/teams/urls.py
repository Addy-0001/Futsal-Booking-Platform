from rest_framework.routers import DefaultRouter

from .views import ChallengeViewSet, TeamViewSet

router = DefaultRouter()
router.register("teams", TeamViewSet, basename="team")
router.register("challenges", ChallengeViewSet, basename="challenge")

urlpatterns = router.urls

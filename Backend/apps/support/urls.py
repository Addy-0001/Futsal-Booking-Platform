from rest_framework.routers import DefaultRouter

from .views import SupportTicketViewSet

router = DefaultRouter()
router.register("support-tickets", SupportTicketViewSet, basename="supportticket")

urlpatterns = router.urls

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import PriceRuleViewSet, QuoteView

router = DefaultRouter()
router.register("price-rules", PriceRuleViewSet, basename="pricerule")

urlpatterns = [
    path("pricing/quote/", QuoteView.as_view(), name="price-quote"),
    *router.urls,
]

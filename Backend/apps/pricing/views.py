from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.futsals.models import Court, Futsal
from apps.futsals.permissions import require_futsal_staff

from .models import PriceRule
from .serializers import PriceRuleSerializer, QuoteSerializer
from .services import resolve_price


class PriceRuleViewSet(viewsets.ModelViewSet):
    """Staff-only configuration of dynamic pricing for their futsal's courts."""

    serializer_class = PriceRuleSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["court", "is_active"]

    def get_queryset(self):
        user = self.request.user
        qs = PriceRule.objects.select_related("court__futsal")
        if user.is_staff:
            return qs
        return qs.filter(court__futsal__roles__user=user).distinct()

    def perform_create(self, serializer):
        require_futsal_staff(self.request.user, serializer.validated_data["court"].futsal)
        serializer.save()

    def perform_update(self, serializer):
        court = serializer.validated_data.get("court") or serializer.instance.court
        require_futsal_staff(self.request.user, court.futsal)
        serializer.save()

    def perform_destroy(self, instance):
        require_futsal_staff(self.request.user, instance.court.futsal)
        instance.delete()


class QuoteView(APIView):
    """Public: server-authoritative price for a court + start time. ?court=<uuid>&start=<iso>."""

    permission_classes = [AllowAny]

    def get(self, request):
        serializer = QuoteSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        court = get_object_or_404(
            Court.objects.select_related("futsal"),
            Q(pk=serializer.validated_data["court"]),
            futsal__status=Futsal.Status.ACTIVE,
        )
        price = resolve_price(court, serializer.validated_data["start"])
        return Response({
            "court": str(court.pk),
            "start": serializer.validated_data["start"],
            "price": price,
            "currency": "NPR",
        })

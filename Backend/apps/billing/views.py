from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Invoice
from .serializers import InvoiceSerializer


class InvoiceViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    """Customers see (read-only) their own invoices; staff see all. Editing is
    admin-only — this is the customer billing portal."""

    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status"]
    ordering_fields = ["created_at", "due_date", "total"]

    def get_queryset(self):
        qs = (
            Invoice.objects.select_related("customer")
            .prefetch_related("items", "payments")
            .order_by("-created_at")
        )
        user = self.request.user
        if user.is_staff:
            return qs
        return qs.filter(customer=user)

from rest_framework import serializers

from .models import Invoice, InvoiceItem, Payment


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ("id", "description", "quantity", "unit_price", "amount")


class PaymentSerializer(serializers.ModelSerializer):
    method_display = serializers.CharField(source="get_method_display", read_only=True)

    class Meta:
        model = Payment
        fields = ("id", "amount", "method", "method_display", "reference", "paid_at")


class InvoiceSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    items = InvoiceItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.get_full_name", read_only=True)

    class Meta:
        model = Invoice
        fields = (
            "id", "number", "status", "status_display", "currency",
            "customer", "customer_name", "booking",
            "issue_date", "due_date", "paid_at",
            "subtotal", "tax_rate", "tax_amount", "total", "amount_paid", "balance",
            "notes", "items", "payments", "created_at",
        )
        read_only_fields = fields

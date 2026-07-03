from rest_framework import serializers

from .models import PriceRule
from .utils import days_from_mask


class PriceRuleSerializer(serializers.ModelSerializer):
    days = serializers.SerializerMethodField()

    class Meta:
        model = PriceRule
        fields = ("id", "court", "name", "days_mask", "days", "start_time", "end_time",
                  "price", "priority", "valid_from", "valid_to", "is_active")

    def get_days(self, obj):
        return days_from_mask(obj.days_mask)

    def validate(self, attrs):
        start = attrs.get("start_time") or getattr(self.instance, "start_time", None)
        end = attrs.get("end_time") or getattr(self.instance, "end_time", None)
        if start and end and start >= end:
            raise serializers.ValidationError("start_time must be before end_time.")
        return attrs


class QuoteSerializer(serializers.Serializer):
    court = serializers.UUIDField()
    start = serializers.DateTimeField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    currency = serializers.CharField(read_only=True, default="NPR")

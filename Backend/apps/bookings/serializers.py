from rest_framework import serializers

from apps.futsals.models import Court, Futsal

from .models import Booking


class BookingSerializer(serializers.ModelSerializer):
    """Read representation returned to clients.

    ``user_name``/``user_phone``/``user_email`` exist so venue staff can
    actually reach the person who made the booking (call to confirm before
    approving) without a second lookup — the view's queryset already
    ``select_related("user")``, so these don't add extra queries.
    """

    court_name = serializers.CharField(source="court.name", read_only=True)
    futsal = serializers.UUIDField(source="court.futsal_id", read_only=True)
    futsal_name = serializers.CharField(source="court.futsal.name", read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True, default="")
    user_phone = serializers.CharField(source="user.phone", read_only=True, default="")
    user_email = serializers.EmailField(source="user.email", read_only=True, default="")

    class Meta:
        model = Booking
        fields = ("id", "court", "court_name", "futsal", "futsal_name", "user",
                  "user_name", "user_phone", "user_email",
                  "start_at", "end_at", "status", "price_at_booking",
                  "payment_method", "note", "approved_at", "cancellation_reason",
                  "created_at")
        read_only_fields = fields


class CreateBookingSerializer(serializers.Serializer):
    court = serializers.PrimaryKeyRelatedField(
        queryset=Court.objects.filter(is_active=True, futsal__status=Futsal.Status.ACTIVE)
    )
    start_at = serializers.DateTimeField()
    end_at = serializers.DateTimeField()
    note = serializers.CharField(max_length=300, required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs["start_at"] >= attrs["end_at"]:
            raise serializers.ValidationError("start_at must be before end_at.")
        return attrs


class RescheduleSerializer(serializers.Serializer):
    start_at = serializers.DateTimeField()
    end_at = serializers.DateTimeField()


class BookingActionSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=300, required=False, allow_blank=True)

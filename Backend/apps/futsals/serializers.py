from rest_framework import serializers

from .models import (
    ClosureException,
    Court,
    CourtImage,
    Futsal,
    FutsalImage,
    FutsalRole,
    OperatingHours,
)


class FutsalImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FutsalImage
        fields = ("id", "futsal", "image", "caption", "is_primary", "order")


class CourtImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourtImage
        fields = ("id", "court", "image", "caption", "is_primary", "order")


class OperatingHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperatingHours
        fields = ("id", "court", "weekday", "open_time", "close_time")


class ClosureExceptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClosureException
        fields = ("id", "court", "date", "reason")


class CourtSerializer(serializers.ModelSerializer):
    operating_hours = OperatingHoursSerializer(many=True, read_only=True)
    images = CourtImageSerializer(many=True, read_only=True)

    class Meta:
        model = Court
        fields = ("id", "futsal", "name", "surface_type", "default_price",
                  "is_active", "operating_hours", "images")


class FutsalSerializer(serializers.ModelSerializer):
    courts = CourtSerializer(many=True, read_only=True)
    images = FutsalImageSerializer(many=True, read_only=True)
    my_role = serializers.SerializerMethodField()

    class Meta:
        model = Futsal
        fields = ("id", "name", "slug", "description", "address", "city",
                  "latitude", "longitude", "timezone", "status",
                  "courts", "images", "my_role", "created_at")
        read_only_fields = ("id", "slug", "status", "created_at")

    def get_my_role(self, obj):
        request = self.context.get("request")
        return obj.role_for(request.user) if request else None


class FutsalRoleSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = FutsalRole
        fields = ("id", "user", "user_email", "futsal", "role", "granted_by", "created_at")
        read_only_fields = ("id", "granted_by", "created_at")

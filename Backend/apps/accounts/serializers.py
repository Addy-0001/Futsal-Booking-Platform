from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .tokens import (
    decode_uid,
    email_verification_token,
    password_reset_token,
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Safe public-ish representation of the authenticated user."""

    class Meta:
        model = User
        fields = ("id", "email", "phone", "full_name", "avatar",
                  "is_email_verified", "is_phone_verified", "date_joined")
        read_only_fields = ("id", "is_email_verified", "is_phone_verified", "date_joined")
        extra_kwargs = {"avatar": {"required": False, "allow_null": True}}

    def validate_email(self, value):
        return value.lower()

    def validate_avatar(self, value):
        if value and value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Image must be under 5 MB.")
        return value

    def update(self, instance, validated_data):
        email_changed = "email" in validated_data and validated_data["email"] != instance.email
        phone_changed = "phone" in validated_data and validated_data["phone"] != instance.phone
        # Replacing/removing the avatar orphans the old file — clean it up.
        if "avatar" in validated_data and instance.avatar:
            instance.avatar.delete(save=False)
        user = super().update(instance, validated_data)

        # Changing a verified contact means it must be re-verified.
        update_fields = []
        if email_changed and user.is_email_verified:
            user.is_email_verified = False
            update_fields.append("is_email_verified")
        if phone_changed and user.is_phone_verified:
            user.is_phone_verified = False
            update_fields.append("is_phone_verified")
        if update_fields:
            user.save(update_fields=update_fields)
        if email_changed:
            from .emails import send_verification_email

            send_verification_email(user)
        return user


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_current_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "phone", "full_name", "password", "password_confirm")
        read_only_fields = ("id",)

    def validate_email(self, value):
        return value.lower()

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = True
        user.save()
        return user


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT login that also returns the user object. USERNAME_FIELD is email."""

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        return token


class _UidTokenSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()

    token_generator = None  # set by subclass

    def _get_user(self, uid):
        try:
            return User.objects.get(pk=decode_uid(uid))
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return None

    def validate(self, attrs):
        user = self._get_user(attrs["uid"])
        if user is None or not self.token_generator.check_token(user, attrs["token"]):
            # Same error for bad/expired/used token — don't leak which.
            raise serializers.ValidationError("Invalid or expired link.")
        attrs["user"] = user
        return attrs


class VerifyEmailSerializer(_UidTokenSerializer):
    token_generator = email_verification_token

    def save(self):
        user = self.validated_data["user"]
        if not user.is_email_verified:
            user.is_email_verified = True
            user.save(update_fields=["is_email_verified"])
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower()


class PasswordResetConfirmSerializer(_UidTokenSerializer):
    token_generator = password_reset_token
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

    def save(self):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])  # changing hash invalidates the token (single-use)
        return user

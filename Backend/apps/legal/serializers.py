from rest_framework import serializers

from .models import ConsentRecord, Policy


class PolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = Policy
        fields = ("id", "slug", "title", "body", "version", "published_at")


class ConsentSerializer(serializers.Serializer):
    # Accept either the policy slug (current version) or an explicit policy id.
    slug = serializers.ChoiceField(choices=Policy.Slug.choices, required=False)
    policy = serializers.UUIDField(required=False)

    def validate(self, attrs):
        if not attrs.get("slug") and not attrs.get("policy"):
            raise serializers.ValidationError("Provide a policy slug or id.")
        return attrs


class ConsentRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsentRecord
        fields = ("id", "policy", "created_at")

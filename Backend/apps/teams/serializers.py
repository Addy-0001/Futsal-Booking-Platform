from rest_framework import serializers

from .models import MatchChallenge, Team, TeamMembership


class TeamMembershipSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = TeamMembership
        fields = ("id", "team", "user", "user_name", "user_email", "role", "status")
        read_only_fields = ("id", "role", "status")


class TeamSerializer(serializers.ModelSerializer):
    captain_name = serializers.CharField(source="captain.get_full_name", read_only=True)
    members = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ("id", "name", "slug", "logo", "description", "captain", "captain_name",
                  "home_futsal", "members", "created_at")
        read_only_fields = ("id", "slug", "captain", "created_at")

    def get_members(self, obj):
        active = obj.memberships.filter(status=TeamMembership.Status.ACTIVE).select_related("user")
        return TeamMembershipSerializer(active, many=True).data


class InviteSerializer(serializers.Serializer):
    """Invite by email (preferred) or by user id."""

    email = serializers.EmailField(required=False)
    user = serializers.UUIDField(required=False)

    def validate(self, attrs):
        if not attrs.get("email") and not attrs.get("user"):
            raise serializers.ValidationError("Provide an email or user id to invite.")
        return attrs


class ChallengeSerializer(serializers.ModelSerializer):
    challenger_name = serializers.CharField(source="challenger_team.name", read_only=True)
    opponent_name = serializers.CharField(source="opponent_team.name", read_only=True)

    class Meta:
        model = MatchChallenge
        fields = ("id", "challenger_team", "challenger_name", "opponent_team", "opponent_name",
                  "court", "proposed_start", "status", "challenger_score", "opponent_score",
                  "created_by", "responded_by", "created_at")
        read_only_fields = ("id", "status", "created_by", "responded_by",
                            "challenger_score", "opponent_score", "created_at")


class ResultSerializer(serializers.Serializer):
    challenger_score = serializers.IntegerField(min_value=0)
    opponent_score = serializers.IntegerField(min_value=0)

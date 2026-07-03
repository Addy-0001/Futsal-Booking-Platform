from rest_framework import serializers

from .models import Match, MatchPlayer


class MatchPlayerSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = MatchPlayer
        fields = ("id", "user", "user_name", "status")


class MatchSerializer(serializers.ModelSerializer):
    host_name = serializers.CharField(source="host.get_full_name", read_only=True)
    joined_count = serializers.IntegerField(read_only=True)
    players = MatchPlayerSerializer(many=True, read_only=True)

    class Meta:
        model = Match
        fields = ("id", "host", "host_name", "court", "city", "proposed_start", "proposed_end",
                  "format", "skill_level", "max_players", "status", "notes",
                  "joined_count", "players", "created_at")
        read_only_fields = ("id", "host", "status", "created_at")


class CreateMatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = ("court", "city", "proposed_start", "proposed_end",
                  "format", "skill_level", "max_players", "notes")

    def validate_max_players(self, v):
        if v < 2:
            raise serializers.ValidationError("A match needs at least 2 players.")
        return v

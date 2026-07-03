from rest_framework import serializers

from .models import EventLog


class EventIngestSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=80)
    path = serializers.CharField(max_length=300, required=False, allow_blank=True)
    session_id = serializers.CharField(max_length=64, required=False, allow_blank=True)
    props = serializers.JSONField(required=False)


class EventLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventLog
        fields = ("id", "user", "name", "path", "session_id", "props", "created_at")

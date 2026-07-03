from rest_framework import serializers

from .models import SupportTicket, TicketReply


class TicketReplySerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = TicketReply
        fields = ("id", "author_name", "body", "is_staff_reply", "created_at")

    def get_author_name(self, obj):
        if obj.is_staff_reply:
            return "Support team"
        return obj.author.get_full_name() if obj.author else "You"


class SupportTicketSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicket
        fields = (
            "id", "number", "reporter", "type", "email", "subject", "message", "url",
            "priority", "priority_display", "status", "status_display",
            "department", "department_name", "last_reply_at", "replies", "created_at",
        )
        read_only_fields = (
            "id", "number", "reporter", "status", "status_display", "priority_display",
            "department_name", "last_reply_at", "replies", "created_at",
        )

    def get_replies(self, obj):
        # Never expose internal staff notes to customers.
        qs = obj.replies.filter(is_internal_note=False)
        return TicketReplySerializer(qs, many=True, context=self.context).data


class CreateReplySerializer(serializers.Serializer):
    body = serializers.CharField()

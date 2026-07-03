from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class EventLog(BaseModel):
    """Lightweight first-party event/page tracking. Anonymous events allowed."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="events",
    )
    name = models.CharField(max_length=80)            # e.g. "page_view", "booking_created"
    path = models.CharField(max_length=300, blank=True)
    session_id = models.CharField(max_length=64, blank=True, db_index=True)
    props = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["name", "created_at"]),
        ]

    def __str__(self):
        return f"{self.name} @ {self.created_at:%Y-%m-%d %H:%M}"

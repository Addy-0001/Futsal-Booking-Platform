from django.conf import settings
from django.db import models

from apps.common.models import BaseModel
from apps.futsals.models import Court


class Match(BaseModel):
    """An open pickup match players can join — replaces the Facebook-group hunt."""

    class Format(models.TextChoices):
        FIVES = "5s", "5-a-side"
        SEVENS = "7s", "7-a-side"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        FULL = "FULL", "Full"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"

    host = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="hosted_matches"
    )
    court = models.ForeignKey(
        Court, on_delete=models.SET_NULL, null=True, blank=True, related_name="matches"
    )
    city = models.CharField(max_length=100, blank=True)
    proposed_start = models.DateTimeField()
    proposed_end = models.DateTimeField(null=True, blank=True)
    format = models.CharField(max_length=6, choices=Format.choices, default=Format.FIVES)
    skill_level = models.CharField(max_length=50, blank=True)
    max_players = models.PositiveSmallIntegerField(default=10)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    notes = models.CharField(max_length=300, blank=True)
    booking = models.OneToOneField(
        "bookings.Booking", on_delete=models.SET_NULL, null=True, blank=True, related_name="match"
    )

    class Meta:
        ordering = ["proposed_start"]
        indexes = [models.Index(fields=["status", "proposed_start"]), models.Index(fields=["city"])]

    def __str__(self):
        return f"{self.format} @ {self.proposed_start:%Y-%m-%d %H:%M} [{self.status}]"

    @property
    def joined_count(self):
        return self.players.filter(status=MatchPlayer.Status.JOINED).count()

    @property
    def is_joinable(self):
        return self.status == self.Status.OPEN


class MatchPlayer(BaseModel):
    class Status(models.TextChoices):
        JOINED = "JOINED", "Joined"
        LEFT = "LEFT", "Left"
        REMOVED = "REMOVED", "Removed"

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="players")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="match_memberships"
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.JOINED)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["match", "user"], name="uniq_match_player"),
        ]

    def __str__(self):
        return f"{self.user} in {self.match_id} [{self.status}]"

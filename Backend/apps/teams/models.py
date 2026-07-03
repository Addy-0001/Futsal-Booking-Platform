from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.common.models import BaseModel
from apps.futsals.models import Court, Futsal


class Team(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    logo = models.URLField(blank=True)
    description = models.TextField(blank=True)
    captain = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="captained_teams"
    )
    home_futsal = models.ForeignKey(
        Futsal, on_delete=models.SET_NULL, null=True, blank=True, related_name="home_teams"
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "team"
            slug, i = base, 1
            while Team.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    def is_captain(self, user):
        return bool(user and user.is_authenticated and self.captain_id == user.id)

    def is_active_member(self, user):
        if not user or not user.is_authenticated:
            return False
        return self.memberships.filter(user=user, status=TeamMembership.Status.ACTIVE).exists()


class TeamMembership(BaseModel):
    class Role(models.TextChoices):
        CAPTAIN = "CAPTAIN", "Captain"
        MEMBER = "MEMBER", "Member"

    class Status(models.TextChoices):
        INVITED = "INVITED", "Invited"
        ACTIVE = "ACTIVE", "Active"
        LEFT = "LEFT", "Left"

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="team_memberships"
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.INVITED)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["team", "user"], name="uniq_team_member"),
        ]

    def __str__(self):
        return f"{self.user} {self.role} @ {self.team} [{self.status}]"


class MatchChallenge(BaseModel):
    """Team-vs-team challenge — the 'war declaration' flow."""

    class Status(models.TextChoices):
        PROPOSED = "PROPOSED", "Proposed"
        ACCEPTED = "ACCEPTED", "Accepted"
        DECLINED = "DECLINED", "Declined"
        SCHEDULED = "SCHEDULED", "Scheduled"
        PLAYED = "PLAYED", "Played"
        CANCELLED = "CANCELLED", "Cancelled"

    challenger_team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="challenges_sent"
    )
    opponent_team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="challenges_received"
    )
    court = models.ForeignKey(
        Court, on_delete=models.SET_NULL, null=True, blank=True, related_name="challenges"
    )
    proposed_start = models.DateTimeField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PROPOSED)
    # Free-form result, e.g. "3-2". Populated when PLAYED.
    challenger_score = models.PositiveSmallIntegerField(null=True, blank=True)
    opponent_score = models.PositiveSmallIntegerField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_challenges"
    )
    responded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="responded_challenges",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "proposed_start"])]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(challenger_team=models.F("opponent_team")),
                name="challenge_distinct_teams",
            ),
        ]

    def __str__(self):
        return f"{self.challenger_team} vs {self.opponent_team} [{self.status}]"

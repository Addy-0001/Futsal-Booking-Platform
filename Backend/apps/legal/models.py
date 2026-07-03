from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class Policy(BaseModel):
    """
    A versioned legal page (privacy / terms / cookies / refund). Keeping versions
    lets you prove exactly which text a user consented to.
    """

    class Slug(models.TextChoices):
        PRIVACY = "privacy", "Privacy Policy"
        TERMS = "terms", "Terms & Conditions"
        COOKIES = "cookies", "Cookie Policy"
        REFUND = "refund", "Refund & Cancellation"

    slug = models.CharField(max_length=30, choices=Slug.choices)
    title = models.CharField(max_length=150)
    body = models.TextField()
    version = models.PositiveIntegerField(default=1)
    is_current = models.BooleanField(default=True)
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["slug", "-version"]
        constraints = [
            models.UniqueConstraint(fields=["slug", "version"], name="uniq_policy_slug_version"),
            models.UniqueConstraint(
                fields=["slug"], condition=models.Q(is_current=True),
                name="uniq_current_policy_per_slug",
            ),
        ]

    def __str__(self):
        return f"{self.title} v{self.version}"


class ConsentRecord(BaseModel):
    """Audit trail of who accepted which policy version, and when."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="consents",
    )
    policy = models.ForeignKey(Policy, on_delete=models.PROTECT, related_name="consents")
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "policy"])]

    def __str__(self):
        return f"{self.user or 'anon'} accepted {self.policy}"

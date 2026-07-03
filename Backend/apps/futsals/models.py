from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.common.models import BaseModel


class Futsal(BaseModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending review"
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    # Venue-local timezone; bookings are stored UTC and converted at the edges.
    timezone = models.CharField(max_length=64, default="Asia/Kathmandu")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_futsals"
    )

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["status"]), models.Index(fields=["city"])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._unique_slug()
        super().save(*args, **kwargs)

    def _unique_slug(self):
        base = slugify(self.name) or "futsal"
        slug, i = base, 1
        while Futsal.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            i += 1
            slug = f"{base}-{i}"
        return slug

    def role_for(self, user):
        """Return this user's role on the futsal (OWNER/MANAGER) or None."""
        if not user or not user.is_authenticated:
            return None
        role = self.roles.filter(user=user).order_by("role").values_list("role", flat=True).first()
        return role

    def is_staff_member(self, user):
        return self.role_for(user) in (FutsalRole.Role.OWNER, FutsalRole.Role.MANAGER)

    def is_owner(self, user):
        return self.role_for(user) == FutsalRole.Role.OWNER


class FutsalRole(BaseModel):
    """
    Contextual RBAC: a role is always *for a specific futsal*, never global.
    Cleanly supports one owner -> many futsals, one futsal -> many owners, and managers.
    """

    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        MANAGER = "MANAGER", "Manager"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="futsal_roles"
    )
    futsal = models.ForeignKey(Futsal, on_delete=models.CASCADE, related_name="roles")
    role = models.CharField(max_length=10, choices=Role.choices)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="granted_roles",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "futsal", "role"], name="uniq_user_futsal_role"),
        ]
        indexes = [models.Index(fields=["futsal", "role"])]

    def __str__(self):
        return f"{self.user} = {self.role} @ {self.futsal}"


class Court(BaseModel):
    """A single playable ground inside a futsal venue. Bookings are per court."""

    class Surface(models.TextChoices):
        ARTIFICIAL = "ARTIFICIAL", "Artificial turf"
        NATURAL = "NATURAL", "Natural grass"
        INDOOR = "INDOOR", "Indoor"

    futsal = models.ForeignKey(Futsal, on_delete=models.CASCADE, related_name="courts")
    name = models.CharField(max_length=100, default="Court A")
    surface_type = models.CharField(max_length=12, choices=Surface.choices, default=Surface.ARTIFICIAL)
    # Guaranteed fallback price (NPR) when no PriceRule matches a slot.
    default_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["futsal", "name"], name="uniq_court_name_per_futsal"),
        ]

    def __str__(self):
        return f"{self.futsal.name} – {self.name}"


class OperatingHours(BaseModel):
    """Availability window per weekday for a court. 0=Mon … 6=Sun (Python weekday)."""

    court = models.ForeignKey(Court, on_delete=models.CASCADE, related_name="operating_hours")
    weekday = models.PositiveSmallIntegerField()  # 0..6
    open_time = models.TimeField()
    close_time = models.TimeField()

    class Meta:
        ordering = ["weekday", "open_time"]
        constraints = [
            models.UniqueConstraint(fields=["court", "weekday"], name="uniq_court_weekday_hours"),
            models.CheckConstraint(check=models.Q(open_time__lt=models.F("close_time")),
                                   name="hours_open_before_close"),
        ]

    @property
    def futsal(self):
        return self.court.futsal

    def __str__(self):
        return f"{self.court} wd{self.weekday} {self.open_time}-{self.close_time}"


class FutsalImage(BaseModel):
    """A venue can have many photos. `is_primary` marks the card/hero image."""

    futsal = models.ForeignKey(Futsal, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="futsals/%Y/%m/")
    caption = models.CharField(max_length=150, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-is_primary", "order", "created_at"]

    def __str__(self):
        return f"Image for {self.futsal.name}"


class CourtImage(BaseModel):
    """A court can have multiple photos."""

    court = models.ForeignKey(Court, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="courts/%Y/%m/")
    caption = models.CharField(max_length=150, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-is_primary", "order", "created_at"]

    @property
    def futsal(self):
        return self.court.futsal

    def __str__(self):
        return f"Image for {self.court}"


class ClosureException(BaseModel):
    """One-off closure (holiday/maintenance) overriding normal operating hours."""

    court = models.ForeignKey(Court, on_delete=models.CASCADE, related_name="closures")
    date = models.DateField()
    reason = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(fields=["court", "date"], name="uniq_court_closure_date"),
        ]

    @property
    def futsal(self):
        return self.court.futsal

    def __str__(self):
        return f"{self.court} closed {self.date}"

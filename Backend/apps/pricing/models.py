from django.db import models

from apps.common.models import BaseModel
from apps.futsals.models import Court

from .utils import ALL_DAYS, days_from_mask


class PriceRule(BaseModel):
    """
    A dynamic-pricing rule: for a court, on certain weekdays, within a time bracket,
    charge `price`. Highest `priority` wins on overlap. Falls back to Court.default_price
    when nothing matches. Enables morning/day/night + weekend surge with no code changes.
    """

    court = models.ForeignKey(Court, on_delete=models.CASCADE, related_name="price_rules")
    name = models.CharField(max_length=100)
    days_mask = models.PositiveSmallIntegerField(default=ALL_DAYS)  # bit 0=Mon … 6=Sun
    start_time = models.TimeField()
    end_time = models.TimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    priority = models.IntegerField(default=0)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-priority", "start_time"]
        indexes = [models.Index(fields=["court", "is_active"])]
        constraints = [
            models.CheckConstraint(check=models.Q(start_time__lt=models.F("end_time")),
                                   name="pricerule_start_before_end"),
            models.CheckConstraint(check=models.Q(price__gte=0), name="pricerule_price_nonneg"),
        ]

    def __str__(self):
        return f"{self.court} {self.name} ({self.start_time}-{self.end_time}) NPR {self.price}"

    @property
    def futsal(self):
        return self.court.futsal

    @property
    def days(self):
        return days_from_mask(self.days_mask)

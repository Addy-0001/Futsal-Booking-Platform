import uuid

from django.db import models


class UUIDModel(models.Model):
    """Primary key is a non-enumerable UUID (security requirement: don't leak/scan IDs)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimeStampedModel):
    """Default base for domain models: UUID PK + created/updated timestamps."""

    class Meta:
        abstract = True

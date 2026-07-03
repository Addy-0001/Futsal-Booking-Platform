from django.db.models import Q
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from .models import (
    ClosureException,
    Court,
    CourtImage,
    Futsal,
    FutsalImage,
    FutsalRole,
    OperatingHours,
)
from .permissions import (
    IsFutsalStaffOrReadOnly,
    require_futsal_owner,
    require_futsal_staff,
)
from .serializers import (
    ClosureExceptionSerializer,
    CourtImageSerializer,
    CourtSerializer,
    FutsalImageSerializer,
    FutsalRoleSerializer,
    FutsalSerializer,
    OperatingHoursSerializer,
)


class FutsalViewSet(viewsets.ModelViewSet):
    serializer_class = FutsalSerializer
    permission_classes = [IsFutsalStaffOrReadOnly]
    lookup_field = "slug"
    filterset_fields = ["city", "status"]
    search_fields = ["name", "city", "address"]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        qs = Futsal.objects.prefetch_related("courts__operating_hours", "roles")
        user = self.request.user
        if user.is_authenticated:
            # Public ACTIVE venues + any futsal the user has a role on (even if pending/inactive).
            return qs.filter(Q(status=Futsal.Status.ACTIVE) | Q(roles__user=user)).distinct()
        return qs.filter(status=Futsal.Status.ACTIVE)

    def perform_create(self, serializer):
        # Creator becomes the first OWNER.
        futsal = serializer.save(created_by=self.request.user)
        FutsalRole.objects.create(
            user=self.request.user, futsal=futsal,
            role=FutsalRole.Role.OWNER, granted_by=self.request.user,
        )


class _FutsalScopedViewSet(viewsets.ModelViewSet):
    """Base for court-scoped resources: enforces staff role on the parent futsal for writes."""

    permission_classes = [IsFutsalStaffOrReadOnly]

    def _futsal_from_validated(self, serializer):
        raise NotImplementedError

    def perform_create(self, serializer):
        require_futsal_staff(self.request.user, self._futsal_from_validated(serializer))
        serializer.save()

    def perform_update(self, serializer):
        require_futsal_staff(self.request.user, self._futsal_from_validated(serializer))
        serializer.save()


class CourtViewSet(_FutsalScopedViewSet):
    serializer_class = CourtSerializer
    queryset = Court.objects.select_related("futsal").prefetch_related("operating_hours")
    filterset_fields = ["futsal", "is_active"]

    def get_queryset(self):
        # Public sees active courts of active futsals; staff see their own.
        user = self.request.user
        if user.is_authenticated:
            return self.queryset.filter(
                Q(futsal__status=Futsal.Status.ACTIVE) | Q(futsal__roles__user=user)
            ).distinct()
        return self.queryset.filter(is_active=True, futsal__status=Futsal.Status.ACTIVE)

    def _futsal_from_validated(self, serializer):
        return serializer.validated_data.get("futsal") or serializer.instance.futsal


class OperatingHoursViewSet(_FutsalScopedViewSet):
    serializer_class = OperatingHoursSerializer
    queryset = OperatingHours.objects.select_related("court__futsal")
    filterset_fields = ["court", "weekday"]

    def _futsal_from_validated(self, serializer):
        court = serializer.validated_data.get("court")
        return court.futsal if court else serializer.instance.court.futsal


class ClosureExceptionViewSet(_FutsalScopedViewSet):
    serializer_class = ClosureExceptionSerializer
    queryset = ClosureException.objects.select_related("court__futsal")
    filterset_fields = ["court", "date"]

    def _futsal_from_validated(self, serializer):
        court = serializer.validated_data.get("court")
        return court.futsal if court else serializer.instance.court.futsal


class FutsalImageViewSet(_FutsalScopedViewSet):
    serializer_class = FutsalImageSerializer
    queryset = FutsalImage.objects.select_related("futsal")
    filterset_fields = ["futsal"]

    def _futsal_from_validated(self, serializer):
        return serializer.validated_data.get("futsal") or serializer.instance.futsal


class CourtImageViewSet(_FutsalScopedViewSet):
    serializer_class = CourtImageSerializer
    queryset = CourtImage.objects.select_related("court__futsal")
    filterset_fields = ["court"]

    def _futsal_from_validated(self, serializer):
        court = serializer.validated_data.get("court")
        return court.futsal if court else serializer.instance.court.futsal


class FutsalRoleViewSet(viewsets.ModelViewSet):
    """Owners manage who else owns/manages their futsal. Guards the last owner."""

    serializer_class = FutsalRoleSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["futsal", "role"]

    def get_queryset(self):
        user = self.request.user
        # Only roles for futsals the user is staff of (or platform admin).
        qs = FutsalRole.objects.select_related("user", "futsal")
        if user.is_staff:
            return qs
        return qs.filter(futsal__roles__user=user).distinct()

    def perform_create(self, serializer):
        futsal = serializer.validated_data["futsal"]
        require_futsal_owner(self.request.user, futsal)
        serializer.save(granted_by=self.request.user)

    def perform_destroy(self, instance):
        require_futsal_owner(self.request.user, instance.futsal)
        if instance.role == FutsalRole.Role.OWNER:
            owners = instance.futsal.roles.filter(role=FutsalRole.Role.OWNER).count()
            if owners <= 1:
                raise ValidationError("Cannot remove the last owner of a futsal.")
        instance.delete()

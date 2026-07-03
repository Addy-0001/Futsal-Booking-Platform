from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

from .models import Futsal, FutsalRole


def require_futsal_staff(user, futsal):
    """Raise unless the user is an owner/manager of the futsal (or platform staff)."""
    if user.is_staff or futsal.is_staff_member(user):
        return
    raise PermissionDenied("You don't manage this futsal.")


def require_futsal_owner(user, futsal):
    if user.is_staff or futsal.is_owner(user):
        return
    raise PermissionDenied("Only an owner can perform this action.")


class IsFutsalStaffOrReadOnly(permissions.BasePermission):
    """
    Reads are public. Writes require an owner/manager role on the object's futsal;
    deletes require owner. Resolves the futsal from the object generically.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        futsal = obj if isinstance(obj, Futsal) else obj.futsal
        if request.user.is_staff:
            return True
        if request.method == "DELETE":
            return futsal.is_owner(request.user)
        return futsal.is_staff_member(request.user)

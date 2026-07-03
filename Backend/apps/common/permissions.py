from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Object-level guard: a user may only act on rows they own.
    Works with any model exposing a `user` FK; override `owner_field` if different.
    Core security requirement: lock users to their own data unless RBAC says otherwise.
    """

    owner_field = "user"

    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, getattr(view, "owner_field", self.owner_field), None)
        return owner == request.user


class IsSelf(permissions.BasePermission):
    """For user-detail endpoints: the object *is* the requesting user."""

    def has_object_permission(self, request, view, obj):
        return obj == request.user

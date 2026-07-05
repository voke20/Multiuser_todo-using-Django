from rest_framework import permissions


class Owner(permissions.BasePermission):
    """Custom Permission."""

    def has_object_permission(self, request, view, obj):
        """Allow access to user."""
        return obj.owner == request.user

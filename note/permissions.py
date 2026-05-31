from rest_framework import permissions

class Owner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
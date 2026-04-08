from rest_framework.permissions import BasePermission


class IsTutorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role in {"tutor", "admin"})
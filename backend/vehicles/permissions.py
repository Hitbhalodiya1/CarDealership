from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Grants access only to authenticated users whose role is 'admin'."""

    message = "This action is restricted to dealership admins."

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, "role", None) == "admin")

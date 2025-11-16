from rest_framework.permissions import BasePermission

class IsOwner(BasePermission):
    """
    Доступ к объектам только владельцу
    """
    def has_object_permission(self, request, view, obj):
        return obj.owner_id == getattr(request.user, "id", None)
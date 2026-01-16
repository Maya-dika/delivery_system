from functools import wraps
from core.utils import render_not_found
from django.http import JsonResponse


def role_required(allowed_roles=None, employee_types=None):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if user_has_role(request.user, allowed_roles, employee_types):
                return view_func(request, *args, **kwargs)

            # Decide JSON vs HTML by Accept / path
            wants_json = "application/json" == getattr(request, "content_type", "") or "application/json" == getattr(request, "accepted_media_type", "")
            if wants_json or request.path.startswith("/api/"):
                return JsonResponse({"success": False, "error": "You do not have access to this resource."}, status=403)
            
            return render_not_found(request, "You do not have access to this page.")
        return _wrapped
    return decorator


def user_has_role(user, allowed_roles=None, employee_types=None) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if allowed_roles and user.user_type not in allowed_roles:
        return False
    if user.user_type == "employee" and employee_types:
        return user.employee_user.filter(employee_type__in=employee_types).exists()
    return True

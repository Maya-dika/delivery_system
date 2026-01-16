from core.menus import get_user_menus
from core.models import Company
from users.models import Employee

def menu_context(request):
    if request.user.is_authenticated:
        return {"menus": get_user_menus(request.user)}
    return {}


def company_profile(request):
    try:
        return {"company_profile": Company.objects.first()}
    except Company.DoesNotExist:
        return {"company_profile": None}


def user_flags(request):
    if not request.user.is_authenticated:
        return {}
    is_driver = Employee.objects.filter(user=request.user, employee_type='driver', active=True).exists()
    return {
        'is_driver': is_driver,
    }

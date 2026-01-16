from django.contrib import admin

from .models import User, Supplier, Customer, Employee
from .forms import CustomUserAdminForm



@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    form = CustomUserAdminForm
    list_display = ('username', 'first_name', 'last_name', 'user_type', 'email', 'phone_number')
    list_filter = ('user_type', 'gender')
    search_fields = ('first_name', 'last_name', 'phone_number', 'email')


admin.site.register(Supplier)
admin.site.register(Customer)
admin.site.register(Employee)
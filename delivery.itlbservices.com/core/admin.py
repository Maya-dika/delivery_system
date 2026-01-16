from django.contrib import admin
from .models import Address, Company, Warehouse, Currency
from .forms import CustomCompanyAdminForm

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    form = CustomCompanyAdminForm


admin.site.register(Address)
admin.site.register(Warehouse)
admin.site.register(Currency)
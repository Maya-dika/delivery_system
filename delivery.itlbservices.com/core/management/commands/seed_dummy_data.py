"""
Management command to seed the database with dummy data for development and testing.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction

from core.models import Company, Currency, Address, Warehouse, StockLocation
from users.models import Employee, EmployeeTypes, Supplier, Customer, UserTypes

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with dummy data including super admin, companies, warehouses, etc.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to seed dummy data...'))

        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            # Note: Be careful with this in production!
            User.objects.filter(is_superuser=False).delete()
            Employee.objects.all().delete()
            Supplier.objects.all().delete()
            Customer.objects.all().delete()
            Warehouse.objects.all().delete()
            Company.objects.all().delete()
            Currency.objects.all().delete()
            Address.objects.all().delete()

        # 1. Create Currency
        self.stdout.write('Creating currencies...')
        usd_currency, _ = Currency.objects.get_or_create(
            name='US Dollar',
            defaults={'symbol': 'USD'}
        )
        eur_currency, _ = Currency.objects.get_or_create(
            name='Euro',
            defaults={'symbol': 'EUR'}
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created currencies: {usd_currency}, {eur_currency}'))

        # 2. Create Company Address
        self.stdout.write('Creating company address...')
        company_address, _ = Address.objects.get_or_create(
            country='US',
            city='New York',
            defaults={
                'street': '123 Main Street',
                'building': 'Building A',
                'zip_code': '10001'
            }
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created company address: {company_address}'))

        # 3. Create Company
        self.stdout.write('Creating company...')
        company, _ = Company.objects.get_or_create(
            name='Delivery Express Inc.',
            defaults={
                'phone_number': '+1-555-0100',
                'address': company_address,
                'currency': usd_currency,
                'active': True,
                'order_request_prefix': 'RQ',
                'order_request_seq_length': 5,
                'order_prefix': '',
                'order_seq_length': 6,
            }
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created company: {company}'))

        # 4. Create Warehouse Address
        self.stdout.write('Creating warehouse address...')
        warehouse_address, _ = Address.objects.get_or_create(
            country='US',
            city='New York',
            street='456 Warehouse Blvd',
            defaults={
                'building': 'Warehouse Building 1',
                'zip_code': '10002'
            }
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created warehouse address: {warehouse_address}'))

        # 5. Create Super Admin User
        self.stdout.write('Creating super admin user...')
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'full_name': 'Super Admin',
                'email': 'admin@delivery.com',
                'phone_number': '+1-555-0001',
                'gender': 'male',
                'user_type': UserTypes.EMPLOYEE,
                'company': company,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Created super admin user: {admin_user.username} (password: admin123)'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ Super admin user already exists: {admin_user.username}'))

        # 6. Create Admin Employee
        self.stdout.write('Creating admin employee...')
        admin_employee, _ = Employee.objects.get_or_create(
            name='Super Admin',
            defaults={
                'email': 'admin@delivery.com',
                'phone_number': '+1-555-0001',
                'employee_type': EmployeeTypes.ADMIN,
                'company': company,
                'user': admin_user,
                'active': True,
            }
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created admin employee: {admin_employee}'))

        # 7. Create Warehouse
        self.stdout.write('Creating warehouse...')
        warehouse, _ = Warehouse.objects.get_or_create(
            name='Main Warehouse',
            defaults={
                'company': company,
                'address': warehouse_address,
                'warehouse_manager': admin_employee,
                'active': True,
            }
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created warehouse: {warehouse}'))

        # Update admin employee warehouse
        admin_employee.warehouse = warehouse
        admin_employee.save()

        # 8. Create Stock Locations
        self.stdout.write('Creating stock locations...')
        supplier_location, _ = StockLocation.objects.get_or_create(
            name='Supplier Location',
            location_type='supplier',
            defaults={
                'company': company,
                'active': True,
            }
        )
        warehouse_location, _ = StockLocation.objects.get_or_create(
            name='Main Warehouse Location',
            location_type='warehouse',
            warehouse=warehouse,
            defaults={
                'company': company,
                'active': True,
            }
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created stock locations: {supplier_location}, {warehouse_location}'))

        # 9. Create Warehouse Manager Employee
        self.stdout.write('Creating warehouse manager...')
        wh_manager_user, _ = User.objects.get_or_create(
            username='wh_manager',
            defaults={
                'full_name': 'John Warehouse Manager',
                'email': 'wh.manager@delivery.com',
                'phone_number': '+1-555-0002',
                'gender': 'male',
                'user_type': UserTypes.EMPLOYEE,
                'company': company,
                'is_staff': False,
                'is_superuser': False,
                'is_active': True,
            }
        )
        if wh_manager_user.password == '' or not wh_manager_user.check_password('manager123'):
            wh_manager_user.set_password('manager123')
            wh_manager_user.save()

        wh_manager_employee, _ = Employee.objects.get_or_create(
            name='John Warehouse Manager',
            defaults={
                'email': 'wh.manager@delivery.com',
                'phone_number': '+1-555-0002',
                'employee_type': EmployeeTypes.WAREHOUSE_MANAGER,
                'company': company,
                'warehouse': warehouse,
                'user': wh_manager_user,
                'active': True,
            }
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created warehouse manager: {wh_manager_employee} (username: wh_manager, password: manager123)'))

        # 10. Create Driver Employee
        self.stdout.write('Creating driver...')
        driver_user, _ = User.objects.get_or_create(
            username='driver1',
            defaults={
                'full_name': 'Mike Driver',
                'email': 'driver1@delivery.com',
                'phone_number': '+1-555-0003',
                'gender': 'male',
                'user_type': UserTypes.EMPLOYEE,
                'company': company,
                'is_staff': False,
                'is_superuser': False,
                'is_active': True,
            }
        )
        if driver_user.password == '' or not driver_user.check_password('driver123'):
            driver_user.set_password('driver123')
            driver_user.save()

        driver_employee, _ = Employee.objects.get_or_create(
            name='Mike Driver',
            defaults={
                'email': 'driver1@delivery.com',
                'phone_number': '+1-555-0003',
                'employee_type': EmployeeTypes.DRIVER,
                'company': company,
                'warehouse': warehouse,
                'user': driver_user,
                'commission': 5.00,
                'active': True,
            }
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created driver: {driver_employee} (username: driver1, password: driver123)'))

        # 11. Create Internal User Employee
        self.stdout.write('Creating internal user...')
        internal_user_obj, _ = User.objects.get_or_create(
            username='internal_user',
            defaults={
                'full_name': 'Sarah Internal User',
                'email': 'internal@delivery.com',
                'phone_number': '+1-555-0004',
                'gender': 'female',
                'user_type': UserTypes.EMPLOYEE,
                'company': company,
                'is_staff': False,
                'is_superuser': False,
                'is_active': True,
            }
        )
        if internal_user_obj.password == '' or not internal_user_obj.check_password('user123'):
            internal_user_obj.set_password('user123')
            internal_user_obj.save()

        internal_employee, _ = Employee.objects.get_or_create(
            name='Sarah Internal User',
            defaults={
                'email': 'internal@delivery.com',
                'phone_number': '+1-555-0004',
                'employee_type': EmployeeTypes.INTERNAL_USER,
                'company': company,
                'warehouse': warehouse,
                'user': internal_user_obj,
                'active': True,
            }
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created internal user: {internal_employee} (username: internal_user, password: user123)'))

        # 12. Create Supplier Address
        self.stdout.write('Creating supplier address...')
        supplier_address, _ = Address.objects.get_or_create(
            country='US',
            city='Los Angeles',
            street='789 Supplier Street',
            defaults={
                'building': 'Supplier Building',
                'zip_code': '90001'
            }
        )

        # 13. Create Supplier User
        supplier_user, _ = User.objects.get_or_create(
            username='supplier1',
            defaults={
                'full_name': 'ABC Suppliers',
                'email': 'supplier1@example.com',
                'phone_number': '+1-555-0101',
                'gender': 'male',
                'user_type': UserTypes.SUPPLIER,
                'company': company,
                'is_staff': False,
                'is_superuser': False,
                'is_active': True,
            }
        )
        if supplier_user.password == '' or not supplier_user.check_password('supplier123'):
            supplier_user.set_password('supplier123')
            supplier_user.save()

        # 14. Create Supplier
        self.stdout.write('Creating supplier...')
        supplier, _ = Supplier.objects.get_or_create(
            name='ABC Suppliers',
            defaults={
                'email': 'supplier1@example.com',
                'phone_number': '+1-555-0101',
                'domain_description': 'Electronics and Gadgets',
                'warehouse': warehouse,
                'address': supplier_address,
                'user': supplier_user,
                'company': company,
                'created_by': admin_user,
                'updated_by': admin_user,
                'created_at': timezone.now(),
                'active': True,
            }
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created supplier: {supplier} (username: supplier1, password: supplier123)'))

        # 15. Create Customer Address
        self.stdout.write('Creating customer address...')
        customer_address, _ = Address.objects.get_or_create(
            country='US',
            city='Chicago',
            street='321 Customer Avenue',
            defaults={
                'building': 'Apt 5B',
                'zip_code': '60601'
            }
        )

        # 16. Create Customer User
        customer_user, _ = User.objects.get_or_create(
            username='customer1',
            defaults={
                'full_name': 'John Customer',
                'email': 'customer1@example.com',
                'phone_number': '+1-555-0201',
                'gender': 'male',
                'user_type': UserTypes.CUSTOMER,
                'company': company,
                'is_staff': False,
                'is_superuser': False,
                'is_active': True,
            }
        )
        if customer_user.password == '' or not customer_user.check_password('customer123'):
            customer_user.set_password('customer123')
            customer_user.save()

        # 17. Create Customer
        self.stdout.write('Creating customer...')
        customer, created = Customer.objects.get_or_create(
            name='John Customer',
            defaults={
                'email': 'customer1@example.com',
                'phone_number': '+1-555-0201',
                'user': customer_user,
                'company': company,
                'created_by': admin_user,
                'updated_by': admin_user,
                'created_at': timezone.now(),
                'active': True,
            }
        )
        if created or not customer.addresses.filter(pk=customer_address.pk).exists():
            customer.addresses.add(customer_address)
        self.stdout.write(self.style.SUCCESS(f'✓ Created customer: {customer} (username: customer1, password: customer123)'))

        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('✓ Dummy data seeding completed successfully!'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('\n📋 Summary of created data:'))
        self.stdout.write(self.style.SUCCESS(f'  • Company: {company.name}'))
        self.stdout.write(self.style.SUCCESS(f'  • Currencies: {usd_currency}, {eur_currency}'))
        self.stdout.write(self.style.SUCCESS(f'  • Warehouse: {warehouse.name}'))
        self.stdout.write(self.style.SUCCESS(f'  • Stock Locations: {supplier_location.name}, {warehouse_location.name}'))
        self.stdout.write(self.style.SUCCESS(f'  • Employees: {Employee.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  • Suppliers: {Supplier.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  • Customers: {Customer.objects.count()}'))
        self.stdout.write(self.style.SUCCESS('\n🔑 Login Credentials:'))
        self.stdout.write(self.style.SUCCESS('  • Super Admin: admin / admin123'))
        self.stdout.write(self.style.SUCCESS('  • Warehouse Manager: wh_manager / manager123'))
        self.stdout.write(self.style.SUCCESS('  • Driver: driver1 / driver123'))
        self.stdout.write(self.style.SUCCESS('  • Internal User: internal_user / user123'))
        self.stdout.write(self.style.SUCCESS('  • Supplier: supplier1 / supplier123'))
        self.stdout.write(self.style.SUCCESS('  • Customer: customer1 / customer123'))
        self.stdout.write(self.style.SUCCESS('\n'))


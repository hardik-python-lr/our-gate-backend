# Package imports
from django.conf import settings
from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, 
    AbstractBaseUser, 
    PermissionsMixin
)
from django.core.validators import MinLengthValidator
from django.utils.translation import gettext_lazy as _
import uuid
import os
from decimal import Decimal
from django.core.validators import MinValueValidator


# Start image upload configuration
def attendance_file_path(instance, filename):
    """ Generate file path for an attendance selfie file """

    # Strip the extension from the file name
    ext = filename.split('.')[-1]

    # Create the filename
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join('uploads/attendance/', filename)


def user_image_path(instance, filename):
    """ Generate file path for an user file """

    # Strip the extension from the file name
    ext = filename.split('.')[-1]

    # Create the filename
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join('uploads/user/', filename)


def service_image_path(instance, filename):
    """ Generate file path for service image file """

    # Strip the extension from the file name
    ext = filename.split('.')[-1]

    # Create the filename
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join('uploads/service/', filename)
# End image upload configuration


class Role(models.Model):
    """ Model: Role """
    """ Populated by `role.json` fixture """

    # Field declarations
    name = models.CharField(max_length=255)


# Start Super-Admin related models
class UserManager(BaseUserManager):
    """ Manager: User model """

    def create_user(self, phone, password='password', **extra_fields):
        """ Create and save a new user """

        user = self.model(phone=phone, **extra_fields)
        # Set password with hash
        user.set_password(password)
        user.save(using=self._db)
        return user


    def create_superuser(self, phone, password, first_name, last_name, email):
        """ Create and save a new superuser """

        user = self.create_user(
            phone=phone,
            password='password',
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """ Model: User """

    # Key declarations
    role = models.ManyToManyField(
        'Role',
        through='UserRole',
        through_fields=('user', 'role'),
        related_name='role',
    )

    # Field declarations
    phone = models.CharField(validators=[MinLengthValidator(10)], max_length=10, unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, blank=True, null=True, unique=True)
    profile_image=models.ImageField(upload_to=user_image_path, null=True)
    # This field will be used for OTP based logic
    otp_counter = models.IntegerField(default=0, blank=True)

    is_active = models.BooleanField(default=True)

    # Additional field declarations
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)     

    # Set Django defaults
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    # Reference custom manager
    objects = UserManager()
    # Unique identifier field - phone instead if username
    USERNAME_FIELD = 'phone'
    # Fields for superuser creation
    REQUIRED_FIELDS = ['first_name', 'last_name', 'email']

    # String representation of model
    def __str__(self):
        return self.phone


class UserDetail(models.Model):
    """ Model: UserDetail """

    # Key declarations
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_details',
        related_query_name='user_detail',
    )

    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        related_name='users',
        related_query_name='user',
        null=True,
    )

    user_employee_categories = models.ManyToManyField(
        'EmployeeCategory',
        through='UserEmployeeCategory',
        through_fields=('user_detail', 'employee_category'),
        related_name='user_employee_categories',
    )

    # Additional field declarations
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class UserRole(models.Model):
    """ Model: UserRole (Many-To-Many through model) """

    # Key declarations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_roles',
        related_query_name='user_role',
    )

    role = models.ForeignKey(
        'Role',
        on_delete=models.CASCADE,
        related_name='users',
        related_query_name='user',
    )

    # Additional field declarations
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'role',)


class EmployeeCategory(models.Model):
    """ Model: EmployeeCategory """

    # Key declarations
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        related_name='employee_categories',
        related_query_name='employee_category'
    )

    # Field declarations
    name = models.CharField(max_length=255)

    # Additional field declarations
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class UserEmployeeCategory(models.Model):
    """ Model: UserEmployeeCategory (Many-To-Many through model) """

    # Key declarations
    user_detail = models.ForeignKey(
        'UserDetail',
        on_delete=models.CASCADE,
        related_name='employee_categories',
        related_query_name='employee_category',
    )

    employee_category = models.ForeignKey(
        'EmployeeCategory',
        on_delete=models.CASCADE,
        related_name='users',
        related_query_name='user',
    )

    # Additional field declarations
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_detail', 'employee_category',)


class Organization(models.Model):
    """ Model: Organization """

    # Key declarations
    owner_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_organizations',
        related_query_name='owned_organization',
    )

    address = models.OneToOneField(
        'Address',
        on_delete=models.SET_NULL,
        related_name='organizations',
        related_query_name='organization',
        null=True,
    )

    # Field declarations
    name = models.CharField(max_length=255)

    is_active = models.BooleanField(default=True)

    # Additional field declarations
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
# End Super-Admin related models


# Start Organization-Administrator related models
class Address(models.Model):
    """ Model: Address """

    # Field declarations
    address_line_1 = models.TextField()
    address_line_2 = models.TextField(blank=True)
    pincode = models.CharField(max_length=8, blank=True)
    city = models.CharField(max_length=255, blank=True)
    state = models.CharField(max_length=255, blank=True)

    # Additional field declarations
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class Location(models.Model):
    """ Model: Location """

    # Field declarations
    latitude = models.DecimalField(max_digits=22, decimal_places=16)
    longitude = models.DecimalField(max_digits=22, decimal_places=16)
    address = models.TextField()

    # Additional field declarations
    created = models.DateTimeField(auto_now_add=True)


class Establishment(models.Model):
    """ Model: Establishment """

    # Key declarations
    owner_organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        related_name='owned_establishments',
        related_query_name='owned_establishment'
    )

    establishment_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='administered_establishments',
        related_query_name='administered_establishment',
        null=True
    )

    location = models.OneToOneField(
        'Location',
        on_delete=models.SET_NULL,
        related_name='establishments',
        related_query_name='establishment',
        null=True,
    )

    address = models.OneToOneField(
        'Address',
        on_delete=models.SET_NULL,
        related_name='establishments',
        related_query_name='establishment',
        null=True,
    )

    guards = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='EstablishmentGuard',
        through_fields=('establishment', 'user'),
        related_name='guards',
    )

    management_committee = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ManagementCommittee',
        through_fields=('establishment', 'user'),
        related_name='management_committee',
    )

    # Field declarations
    name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()

    attendance_radius = models.PositiveIntegerField()

    water_bill_link = models.TextField(blank=True)
    pipe_gas_bill_link = models.TextField(blank=True)
    electricity_bill_link = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    # Additional field declarations
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class EstablishmentGuard(models.Model):
    """ Model: EstablishmentGuard (Many-To-Many through model) """

    # Key declarations
    establishment = models.ForeignKey(
        'Establishment',
        on_delete=models.CASCADE,
        related_name='establishment_guards',
        related_query_name='establishment_guard'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='guard_establishments',
        related_query_name='guard_establishment'
    )

    # Field declarations
    is_active = models.BooleanField(default=True)

    # Additional field declarations
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('establishment', 'user',)


class ServiceCategory(models.Model):
    """ Model: ServiceCategory """

    # Key declarations
    owner_organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        related_name='owned_service_categories',
        related_query_name='owned_service_category'
    )

    # Field declarations
    name = models.CharField(max_length=255)

    is_active = models.BooleanField(default=True)

    # Additional field declarations
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class ServiceSubCategory(models.Model):
    """ Model: ServiceSubCategory """

    # Key declarations
    owner_organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        related_name='owned_service_sub_categories',
        related_query_name='owned_service_sub_category'
    )

    category = models.ForeignKey(
        'ServiceCategory', 
        on_delete=models.CASCADE,
        related_name='service_sub_categories',
        related_query_name='service_sub_category'
    )

    # Field declarations
    name = models.CharField(max_length=255)

    is_active = models.BooleanField(default=True)

    # Additional field declarations
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class Service(models.Model):
    """ Model: Service """

    # Key declarations
    owner_organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        related_name='owned_services',
        related_query_name='owned_service'
    )

    subcategory = models.ForeignKey(
        'ServiceSubCategory', 
        on_delete=models.CASCADE,
        related_name='services',
        related_query_name='service'
    )

    # Field declarations
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to=service_image_path, null=True)
    price = models.PositiveIntegerField()

    is_active = models.BooleanField(default=True)

    # Additional field declarations
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class ServiceSlot(models.Model):
    """ Model: ServiceSlot """

    # Key declarations
    service = models.ForeignKey(
        'Service', 
        on_delete=models.CASCADE,
        related_name='service_slots',
        related_query_name='service_slot'
    )

    # Field declarations
    start_time = models.TimeField()
    end_time = models.TimeField()
    day_of_week = models.PositiveSmallIntegerField()

    is_active = models.BooleanField(default=True)

    # Additional field declarations
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class ServiceExclusion(models.Model):
    """ Model: ServiceExclusion """

    # Key declarations
    service = models.ForeignKey(
        'Service', 
        on_delete=models.CASCADE,
        related_name='service_exclusions',
        related_query_name='service_exclusion'
    )

    # Field declarations
    exclusion_date = models.DateField()

    # Additional field declarations
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('service', 'exclusion_date',)
# End Organization-Administrator related models


# Start Establishment-Admin related models
class ManagementCommittee(models.Model):
    """ Model: ManagementCommittee (Many-To-Many through model) """

    # ENUM declarations
    class ManagementRole(models.TextChoices):
        CHAIRMAN_ROLE = 'Chairman', _('Chairman')
        SECRETARY_ROLE = 'Secretary', _('Secretary')
        TREASURER_ROLE = 'Treasurer', _('Treasurer')

    # Key declarations
    establishment = models.ForeignKey(
        'Establishment', 
        on_delete=models.CASCADE,
        related_name='management_committees_members',
        related_query_name='management_committees_member'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='managed_establishments',
        related_query_name='managed_establishment'
    )    

    # Key declarations
    committee_role = models.CharField(
        max_length=20,
        choices=ManagementRole.choices,
    )

    is_active = models.BooleanField(default=True)

    # Key declarations
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('establishment', 'user',)


class EstablishmentGuardAttendanceRecord(models.Model):
    """ Model: EstablishmentGuardAttendanceRecord """

    # Key declarations
    establishment_guard = models.ForeignKey(
        'EstablishmentGuard',
        on_delete=models.CASCADE,
        related_name='attendance_records',
        related_query_name='attendance_record',
    )
    sign_in_location = models.OneToOneField(
        'Location',
        on_delete=models.CASCADE,
        related_name='sign_in_location',
        related_query_name='sign_in_location'
    )
    sign_in_device_id = models.ForeignKey(
        'DeviceId',
        on_delete=models.SET_NULL,
        related_name='sign_in_device_ids',
        related_query_name='sign_in_device_id',
        null=True
    )
    sign_out_location = models.OneToOneField(
        'Location',
        on_delete=models.CASCADE,
        related_name='sign_out_location',
        related_query_name='sign_out_location',
        null=True
    )
    sign_out_device_id = models.ForeignKey(
        'DeviceId',
        on_delete=models.SET_NULL,
        related_name='sign_out_device_ids',
        related_query_name='sign_out_device_id',
        null=True
    )

    # Field declarations
    sign_in_image = models.ImageField(upload_to=attendance_file_path, null=True, blank=True)
    sign_in_time = models.DateTimeField()
    sign_out_time = models.DateTimeField(null=True)
    sign_out_image = models.ImageField(upload_to=attendance_file_path, null=True, blank=True)
    
    # Additional field declarations
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class DeviceId(models.Model):
    """ Model: DeviceId """

    # Field declarations
    device_id = models.CharField(max_length=255)

    # Additional field declarations
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
# End Establishment-Admin related models 


# Start Resident related models
class FlatMember(models.Model):
    """ Model: FlatMember (Many-To-Many through model) """

    # ENUM declarations
    class MemberRole(models.TextChoices):
        OWNER_ROLE = 'Owner', _('Owner')
        TENANT_ROLE = 'Tenant', _('Tenant')
        FAMILY_MEMBER_ROLE = 'Family-Member', _('Family-Member')

    # Key declarations
    flat = models.ForeignKey(
        'Flat',
        on_delete=models.CASCADE,
        related_name='flat_members',
        related_query_name='flat_member'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='flats',
        related_query_name='flat'
    )

    # Field declarations
    member_role = models.CharField(
        max_length=20,
        choices=MemberRole.choices,
    )

    is_active = models.BooleanField(default=True)
    is_current_flat = models.BooleanField(default=False)

    # Additional field declarations
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('flat', 'user',)


class ServiceRequest(models.Model):
    """ Model: ServiceRequest """

    # ENUM declarations
    class ServiceRequestStatus(models.TextChoices):
        PENDING = 'Pending', _('Pending')
        APPROVED = 'Approved', _('Approved')
        ASSIGNED = 'Assigned', _('Assigned')
        COMPLETED = 'Completed', _('Completed')
        REJECTED = 'Rejected', _('Rejected')

    # Key declarations
    flat = models.ForeignKey(
        'Flat',
        on_delete=models.CASCADE,
        related_name='requested_services',
        related_query_name='requested_service'
    )

    service = models.ForeignKey(
        'Service', 
        on_delete=models.CASCADE,
        related_name='requested_services',
        related_query_name='requested_service'
    )

    requested_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='requested_users',
        related_query_name='requested_user'
    )

    assigned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='service_providers',
        related_query_name='service_provider',
        null=True
    )

    payment_info = models.ForeignKey(
        'Payment', 
        on_delete=models.CASCADE,
        related_name='service_request_payments',
        related_query_name='service_request_payment',
        null=True
    )

    requested_service_slots = models.ManyToManyField(
        'ServiceSlot',
        through='ServiceRequestServiceSlot',
        through_fields=('service_request', 'service_slot'),
        related_name='requested_service_slots',
    )

    # Field declarations
    requested_date = models.DateField()
    amount = models.PositiveIntegerField(default=0)
    service_request_status = models.CharField(
        max_length=20,
        choices=ServiceRequestStatus.choices
    )
    # Out of five (Feedback of the service)
    rating = models.PositiveSmallIntegerField(null=True)

    is_active = models.BooleanField(default=False)

    # Additional field declarations
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)


class ServiceRequestServiceSlot(models.Model):
    """ Model: ServiceRequestServiceSlot (Many-To-Many through model) """

    # Key declarations
    service_request = models.ForeignKey(
        'ServiceRequest',
        on_delete=models.CASCADE,
        related_name='service_slots',
        related_query_name='service_slot'
    )

    service_slot = models.ForeignKey(
        'ServiceSlot',
        on_delete=models.CASCADE,
        related_name='service_requests',
        related_query_name='service_request'
    )

    # Field declarations
    start_time = models.TimeField()
    end_time = models.TimeField()

    # Additional field declarations
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('service_request', 'service_slot',)
# End Resident related models


# Start Payment model
class Payment(models.Model):
    """ Model: Payment """

    # ENUM declarations
    class PaymentStatus(models.TextChoices):
        PENDING = 'Pending', _('Pending')
        SUCCESS = 'Success', _('Success')
        FAIL = 'Fail', _('Fail')

    # Field declarations
    order_id = models.CharField(max_length=255)
    payment_id = models.CharField(max_length=255, blank=True)
    signature = models.TextField(blank=True)
    amount = models.CharField(max_length=255)

    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices
    )

    # Additional field declarations
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
# End Payment model

# Start Notification models
class PushNotificationToken(models.Model):
    """ Model: PushNotificationToken """

    # Key declarations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='push_notification_records',
        related_query_name='push_notification_record',
    )

    # Field declarations
    device_id = models.CharField(max_length=255, blank=True)
    current_token = models.CharField(max_length=255, blank=True)

    # Additional field declarations
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
# End Notification models

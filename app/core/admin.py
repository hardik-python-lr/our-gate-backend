from django.contrib import admin
from app.core.models import *
# Register your models here.


admin.site.register(Role)
admin.site.register(User)
admin.site.register(UserDetail)
admin.site.register(UserRole)
admin.site.register(EmployeeCategory)
admin.site.register(UserEmployeeCategory)
admin.site.register(Organization)
admin.site.register(Address)
admin.site.register(Location)
admin.site.register(Establishment)
admin.site.register(EstablishmentGuard)
admin.site.register(ServiceCategory)
admin.site.register(ServiceSubCategory)
admin.site.register(Service)
admin.site.register(Building)
admin.site.register(Flat)
admin.site.register(ManagementCommittee)
admin.site.register(Announcement)
admin.site.register(Amenity)

from import_export.admin import ImportExportModelAdmin

class abc(ImportExportModelAdmin):
    pass
admin.site.register(AmenitySlot, abc)
admin.site.register(AmenityExclusion)
admin.site.register(Visitor)
admin.site.register(Visit)
admin.site.register(WorkCategory)
admin.site.register(DailyHelp)
admin.site.register(AssignedFlat)
admin.site.register(FlatMember)
admin.site.register(Vehicle)
admin.site.register(AmenityBooking)
admin.site.register(Bill)
admin.site.register(ServiceRequest)
admin.site.register(PushNotificationToken)
admin.site.register(VisitFlat)
admin.site.register(DailyHelpAttendanceRecord)
admin.site.register(EstablishmentGuardAttendanceRecord)
admin.site.register(DeviceId)
admin.site.register(ServiceSlot)
admin.site.register(ServiceExclusion)
admin.site.register(ServiceRequestServiceSlot)
admin.site.register(Payment)
admin.site.register(AmenityBookingAmenitySlot)
admin.site.register(BillPayment)
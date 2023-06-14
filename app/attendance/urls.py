from django.urls import path
from app.attendance.views import (
    # Check-In view
    AttendanceRecordCheckInView,

    # Check-Out view
    AttendanceRecordCheckOutView,

    # Attendance Current Status view
    AttendanceCurrentStatus,
)


urlpatterns = [
    # Check-In
    path('user-check-in/', AttendanceRecordCheckInView.as_view(), name='user-check-in'),

    # Check-Out
    path('user-check-out/', AttendanceRecordCheckOutView.as_view(), name='user-check-out'),

    # CurrentStatusAttendance
    path('attendance-current-status/', AttendanceCurrentStatus.as_view(), name='attendance-current-status'),
]

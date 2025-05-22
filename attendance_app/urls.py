from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # Student
    path('student/register/', views.register_student, name='student_register'),
    path('scan/', views.scan_qr_and_attend, name='scan_qr'),
    path('student/<str:student_id>/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('view_attendance/', views.view_attendance, name='view_attendance'),

    # Teacher
    path('teacher/login/', views.teacher_login, name='teacher_login'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('generate_qr/', views.generate_qr, name='generate_qr'),
    path('attendance/summary/', views.attendance_summary, name='attendance_summary'),
]

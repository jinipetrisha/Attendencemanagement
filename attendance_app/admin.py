from django.contrib import admin
from .models import Student, Attendance

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'student_id')
    search_fields = ('name', 'student_id')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'class_id', 'subject', 'date', 'time')
    list_filter = ('subject', 'date')
    search_fields = ('student__name', 'class_id')

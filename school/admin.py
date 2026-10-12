from django.contrib import admin
from .models import Attendance, StudentExtra, TeacherExtra, Notice

# Register your models here.
class StudentExtraAdmin(admin.ModelAdmin):
    list_display = ('get_name', 'roll', 'cl', 'mobile', 'fee', 'status')
    list_filter = ('cl', 'status')
    search_fields = ('user__first_name', 'user__last_name', 'roll', 'mobile')

admin.site.register(StudentExtra, StudentExtraAdmin)

class TeacherExtraAdmin(admin.ModelAdmin):
    list_display = ('get_name', 'salary', 'mobile', 'status', 'joindate')
    list_filter = ('status', 'joindate')
    search_fields = ('user__first_name', 'user__last_name', 'mobile')

admin.site.register(TeacherExtra, TeacherExtraAdmin)

class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('roll', 'cl', 'date', 'present_status')
    list_filter = ('cl', 'date', 'present_status')
    search_fields = ('roll', 'cl')

admin.site.register(Attendance, AttendanceAdmin)

class NoticeAdmin(admin.ModelAdmin):
    list_display = ('by', 'date', 'message')
    list_filter = ('date', 'by')
    search_fields = ('message', 'by')

admin.site.register(Notice, NoticeAdmin)


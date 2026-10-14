from django.contrib import admin

from .models import Department, Student


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("roll_no", "full_name", "department", "status", "cgpa", "admission_year")
    list_filter = ("department", "status", "gender", "admission_year")
    search_fields = ("roll_no", "first_name", "last_name", "email")
    list_select_related = ("department",)

from django.urls import path

from . import views

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("students/", views.StudentListView.as_view(), name="student_list"),
    path("students/add/", views.StudentCreateView.as_view(), name="student_add"),
    path("students/export/", views.StudentExportView.as_view(), name="student_export"),
    path("students/<int:pk>/edit/", views.StudentUpdateView.as_view(), name="student_edit"),
    path("students/<int:pk>/delete/", views.StudentDeleteView.as_view(), name="student_delete"),
]


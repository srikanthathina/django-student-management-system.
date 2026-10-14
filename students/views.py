import csv
from datetime import date

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, Q
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from .forms import StudentForm
from .models import Department, Student

# Whitelist: the sort key from the URL is never passed to the database directly
SORTS = {
    "roll": "roll_no", "-roll": "-roll_no",
    "name": "first_name", "-name": "-first_name",
    "cgpa": "cgpa", "-cgpa": "-cgpa",
    "year": "admission_year", "-year": "-admission_year",
}


class StudentFilterMixin:
    """Search + filter + sort, shared by the list page and the CSV export so both always agree."""

    def filtered_queryset(self):
        params = self.request.GET
        qs = Student.objects.select_related("department")

        for term in params.get("q", "").split():          # every word must match somewhere
            qs = qs.filter(
                Q(first_name__icontains=term) | Q(last_name__icontains=term)
                | Q(roll_no__icontains=term) | Q(email__icontains=term)
            )
        if params.get("department", "").isdigit():
            qs = qs.filter(department_id=params["department"])
        if params.get("status") in Student.Status.values:
            qs = qs.filter(status=params["status"])
        if params.get("gender") in Student.Gender.values:
            qs = qs.filter(gender=params["gender"])
        if params.get("year", "").isdigit():
            qs = qs.filter(admission_year=params["year"])
        return qs.order_by(SORTS.get(params.get("sort"), "roll_no"), "id")


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        buckets = [("Below 5", None, 5), ("5-6", 5, 6), ("6-7", 6, 7), ("7-8", 7, 8), ("8-9", 8, 9), ("9-10", 9, None)]
        bucket_aggs = {}
        for i, (_, low, high) in enumerate(buckets):
            cond = Q(cgpa__isnull=False)
            if low is not None:
                cond &= Q(cgpa__gte=low)
            if high is not None:
                cond &= Q(cgpa__lt=high)
            bucket_aggs[f"b{i}"] = Count("id", filter=cond)

        # One query computes every card number and every CGPA bucket
        stats = Student.objects.aggregate(
            total=Count("id"),
            active=Count("id", filter=Q(status=Student.Status.ACTIVE)),
            graduated=Count("id", filter=Q(status=Student.Status.GRADUATED)),
            this_year=Count("id", filter=Q(admission_year=date.today().year)),
            avg_cgpa=Avg("cgpa"),
            **bucket_aggs,
        )
        avg = stats["avg_cgpa"]
        status_labels = dict(Student.Status.choices)

        ctx["stats"] = {**stats, "avg_cgpa": round(float(avg), 2) if avg is not None else None}
        ctx["chart_data"] = {
            "departments": list(
                Department.objects.annotate(n=Count("students")).order_by("code").values("id", "code", "name", "n")
            ),
            "status": [
                {"key": r["status"], "label": status_labels[r["status"]], "n": r["n"]}
                for r in Student.objects.values("status").annotate(n=Count("id")).order_by("status")
            ],
            "years": list(
                Student.objects.values("admission_year").annotate(n=Count("id")).order_by("admission_year")
            ),
            "cgpa": {"labels": [b[0] for b in buckets], "values": [stats[f"b{i}"] for i in range(len(buckets))]},
        }
        ctx["top_students"] = (
            Student.objects.filter(cgpa__isnull=False).select_related("department").order_by("-cgpa", "roll_no")[:5]
        )
        ctx["recent_students"] = Student.objects.select_related("department").order_by("-created_at", "-id")[:5]
        return ctx


class StudentListView(LoginRequiredMixin, StudentFilterMixin, ListView):
    template_name = "students/student_list.html"
    context_object_name = "students"
    paginate_by = 10

    def get_queryset(self):
        return self.filtered_queryset()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["querystring"] = params.urlencode()          # keeps filters when paging
        ctx["departments"] = Department.objects.all()
        ctx["statuses"] = Student.Status.choices
        ctx["genders"] = Student.Gender.choices
        ctx["years"] = Student.objects.order_by("-admission_year").values_list("admission_year", flat=True).distinct()
        ctx["f"] = {k: self.request.GET.get(k, "") for k in ("q", "department", "status", "gender", "year", "sort")}
        ctx["has_filters"] = any(ctx["f"][k] for k in ("q", "department", "status", "gender", "year"))
        return ctx


class StudentCreateView(LoginRequiredMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = "students/student_form.html"
    success_url = reverse_lazy("student_list")
    extra_context = {"title": "Add student", "submit_label": "Save student"}

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Added {self.object.full_name} ({self.object.roll_no}).")
        return response


class StudentUpdateView(LoginRequiredMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = "students/student_form.html"
    success_url = reverse_lazy("student_list")
    extra_context = {"title": "Edit student", "submit_label": "Save changes"}

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Updated {self.object.full_name}.")
        return response


class StudentDeleteView(LoginRequiredMixin, DeleteView):
    """GET shows a confirmation page (works without JavaScript); POST deletes."""
    model = Student
    template_name = "students/student_confirm_delete.html"
    success_url = reverse_lazy("student_list")

    def form_valid(self, form):
        name = self.object.full_name
        response = super().form_valid(form)
        messages.success(self.request, f"Deleted {name}.")
        return response


def _safe_cell(value) -> str:
    """Stop spreadsheet formula injection: Excel runs cells that start with = + - @."""
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


class StudentExportView(LoginRequiredMixin, StudentFilterMixin, View):
    def get(self, request):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="students-{date.today():%Y-%m-%d}.csv"'
        response.write("\ufeff")                         # BOM so Excel opens UTF-8 correctly
        writer = csv.writer(response)
        writer.writerow(["Roll No", "First Name", "Last Name", "Email", "Phone", "Date of Birth",
                         "Gender", "Department", "Admission Year", "Status", "CGPA"])
        for s in self.filtered_queryset().iterator():
            writer.writerow([_safe_cell(v) for v in (
                s.roll_no, s.first_name, s.last_name, s.email, s.phone, s.date_of_birth,
                s.get_gender_display(), s.department.code, s.admission_year, s.get_status_display(), s.cgpa,
            )])
        return response

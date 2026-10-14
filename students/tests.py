import csv
import io
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Department, Student


def make_student(dept, n, **overrides):
    data = dict(
        roll_no=f"S{n:05d}", first_name=f"First{n}", last_name=f"Last{n}", email=f"s{n}@x.edu",
        date_of_birth=date(2003, 1, 1), gender="M", department=dept, admission_year=2024, cgpa=Decimal("8.00"),
    )
    data.update(overrides)
    return Student.objects.create(**data)


class BaseCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("tester", password="pass12345")
        cls.cse = Department.objects.create(code="CSE", name="Computer Science")
        cls.ece = Department.objects.create(code="ECE", name="Electronics")

    def login(self):
        self.client.login(username="tester", password="pass12345")


class AccessTests(BaseCase):
    def test_pages_require_login(self):
        for name in ("dashboard", "student_list", "student_add", "student_export"):
            resp = self.client.get(reverse(name))
            self.assertEqual(resp.status_code, 302, name)
            self.assertIn("/accounts/login/", resp["Location"])


class DashboardTests(BaseCase):
    def test_stats_and_chart_data(self):
        make_student(self.cse, 1, cgpa=Decimal("9.50"))
        make_student(self.cse, 2, status="GRADUATED", cgpa=Decimal("6.50"))
        make_student(self.ece, 3, cgpa=None)
        self.login()
        resp = self.client.get(reverse("dashboard"))
        self.assertEqual(resp.status_code, 200)
        stats = resp.context["stats"]
        self.assertEqual((stats["total"], stats["active"], stats["graduated"]), (3, 2, 1))
        self.assertEqual(stats["avg_cgpa"], 8.0)            # NULL cgpa is ignored by the average
        self.assertEqual(resp.context["chart_data"]["cgpa"]["values"], [0, 0, 1, 0, 0, 1])
        counts = {d["code"]: d["n"] for d in resp.context["chart_data"]["departments"]}
        self.assertEqual(counts, {"CSE": 2, "ECE": 1})


class ListTests(BaseCase):
    def setUp(self):
        for i in range(1, 26):
            make_student(self.cse if i % 2 else self.ece, i)
        make_student(self.cse, 100, first_name="Srikanth", last_name="Athini", status="SUSPENDED")
        self.login()

    def test_pagination(self):
        resp = self.client.get(reverse("student_list"))
        self.assertEqual(len(resp.context["students"]), 10)
        self.assertEqual(resp.context["page_obj"].paginator.count, 26)

    def test_search_matches_full_name(self):
        resp = self.client.get(reverse("student_list"), {"q": "srikanth athini"})
        self.assertEqual([s.roll_no for s in resp.context["students"]], ["S00100"])

    def test_filter_by_department_and_status(self):
        resp = self.client.get(reverse("student_list"), {"department": self.ece.id})
        self.assertTrue(all(s.department_id == self.ece.id for s in resp.context["students"]))
        resp = self.client.get(reverse("student_list"), {"status": "SUSPENDED"})
        self.assertEqual(resp.context["page_obj"].paginator.count, 1)

    def test_bad_filter_values_are_ignored_not_errors(self):
        resp = self.client.get(reverse("student_list"), {"department": "abc", "status": "NOPE", "sort": "; DROP"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["page_obj"].paginator.count, 26)


class CrudTests(BaseCase):
    def payload(self, **overrides):
        data = {
            "roll_no": "s777", "first_name": "Asha", "last_name": "Rao", "email": "asha@x.edu", "phone": "9876543210",
            "date_of_birth": "2003-05-17", "gender": "F", "department": self.cse.id,
            "admission_year": 2024, "status": "ACTIVE", "cgpa": "8.5",
        }
        data.update(overrides)
        return data

    def test_create(self):
        self.login()
        resp = self.client.post(reverse("student_add"), self.payload(), follow=True)
        self.assertRedirects(resp, reverse("student_list"))
        self.assertEqual(Student.objects.get().roll_no, "S777")      # normalised to upper case
        self.assertContains(resp, "Added Asha Rao")

    def test_duplicate_roll_no_rejected(self):
        make_student(self.cse, 777, roll_no="S777")
        self.login()
        resp = self.client.post(reverse("student_add"), self.payload(email="other@x.edu"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Student.objects.count(), 1)

    def test_future_birth_date_rejected(self):
        self.login()
        resp = self.client.post(reverse("student_add"), self.payload(date_of_birth="2999-01-01"))
        self.assertEqual(Student.objects.count(), 0)
        self.assertContains(resp, "must be in the past")

    def test_edit(self):
        s = make_student(self.cse, 1)
        self.login()
        self.client.post(reverse("student_edit", args=[s.pk]), self.payload(roll_no=s.roll_no, email=s.email, first_name="Changed"))
        s.refresh_from_db()
        self.assertEqual(s.first_name, "Changed")

    def test_delete_needs_post_and_confirmation_page_exists(self):
        s = make_student(self.cse, 1)
        self.login()
        self.assertEqual(self.client.get(reverse("student_delete", args=[s.pk])).status_code, 200)
        self.assertEqual(Student.objects.count(), 1)                 # GET never deletes
        self.client.post(reverse("student_delete", args=[s.pk]))
        self.assertEqual(Student.objects.count(), 0)


class ExportTests(BaseCase):
    def rows(self, **params):
        resp = self.client.get(reverse("student_export"), params)
        self.assertEqual(resp["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("attachment", resp["Content-Disposition"])
        return list(csv.reader(io.StringIO(resp.content.decode("utf-8-sig"))))

    def test_export_rows_and_filter(self):
        make_student(self.cse, 1)
        make_student(self.ece, 2)
        self.login()
        self.assertEqual(len(self.rows()), 3)                         # header + 2
        filtered = self.rows(department=self.ece.id)
        self.assertEqual([r[0] for r in filtered[1:]], ["S00002"])

    def test_formula_injection_is_neutralised(self):
        make_student(self.cse, 1, first_name="=HYPERLINK(\"http://evil\")")
        self.login()
        self.assertTrue(self.rows()[1][1].startswith("'="))

import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from students.models import Department, Student

DEPARTMENTS = [
    ("CSE", "Computer Science and Engineering"),
    ("AIDS", "Artificial Intelligence and Data Science"),
    ("ECE", "Electronics and Communication Engineering"),
    ("EEE", "Electrical and Electronics Engineering"),
    ("MECH", "Mechanical Engineering"),
    ("CIVIL", "Civil Engineering"),
]
FIRST = ("Srikanth Anil Sai Harsha Pavan Ramesh Naveen Teja Vamsi Charan Sravani Meghana Divya Keerthi "
         "Bhavana Lavanya Swathi Pooja Anusha Harini").split()
LAST = ("Kumar Reddy Naidu Sharma Rao Varma Prasad Chowdary Yadav Goud Babu Raju Singh Patel Mohan "
        "Krishna Das Nair Iyer Verma").split()


class Command(BaseCommand):
    help = "Create departments and demo students (safe to run repeatedly: does nothing if students exist)."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=150, help="number of students to create")
        parser.add_argument("--clear", action="store_true", help="delete all existing students first")

    @transaction.atomic
    def handle(self, *args, **opts):
        departments = [Department.objects.get_or_create(code=c, defaults={"name": n})[0] for c, n in DEPARTMENTS]
        if opts["clear"]:
            Student.objects.all().delete()
        elif Student.objects.exists():
            self.stdout.write("Students already exist - nothing to do (use --clear to reseed).")
            return

        rng = random.Random(42)                          # same demo data on every run
        students = []
        for i in range(1, opts["count"] + 1):
            first, last = rng.choice(FIRST), rng.choice(LAST)
            year = rng.randint(2021, 2025)
            if year <= 2022:
                status = Student.Status.GRADUATED
            else:
                status = rng.choices(
                    [Student.Status.ACTIVE, Student.Status.SUSPENDED, Student.Status.DROPPED], [94, 3, 3]
                )[0]
            students.append(Student(
                roll_no=f"S{i:05d}",
                first_name=first,
                last_name=last,
                email=f"{first}.{last}{i}@student.college.edu".lower(),
                phone="9" + "".join(rng.choice("0123456789") for _ in range(9)),
                date_of_birth=date(2001, 1, 1) + timedelta(days=rng.randint(0, 1800)),
                gender=rng.choice(Student.Gender.values),
                department=rng.choice(departments),
                admission_year=year,
                status=status,
                cgpa=round(min(9.9, max(4.0, rng.gauss(7.3, 1.1))), 2),
            ))
        Student.objects.bulk_create(students, batch_size=500)
        self.stdout.write(self.style.SUCCESS(f"Created {len(students)} students in {len(departments)} departments."))

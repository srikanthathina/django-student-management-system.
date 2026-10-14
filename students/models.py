from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models


class Department(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code


class Student(models.Model):
    class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"
        OTHER = "O", "Other"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        GRADUATED = "GRADUATED", "Graduated"
        SUSPENDED = "SUSPENDED", "Suspended"
        DROPPED = "DROPPED", "Dropped"

    roll_no = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=15,
        blank=True,
        validators=[RegexValidator(r"^[0-9+]{7,15}$", "Enter 7-15 digits (a leading + is allowed).")],
    )
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=Gender.choices)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="students")
    admission_year = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2100)]
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    cgpa = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["roll_no"]
        indexes = [
            models.Index(fields=["department", "status"]),
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["admission_year"]),
        ]

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.roll_no} - {self.full_name}"

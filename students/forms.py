from datetime import date

from django import forms

from .models import Student


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            "roll_no", "first_name", "last_name", "email", "phone", "date_of_birth",
            "gender", "department", "admission_year", "status", "cgpa",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "cgpa": forms.NumberInput(attrs={"step": "0.01", "min": "0", "max": "10"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "input")
        self.fields["date_of_birth"].input_formats = ["%Y-%m-%d"]

    def clean_date_of_birth(self):
        dob = self.cleaned_data["date_of_birth"]
        if dob >= date.today():
            raise forms.ValidationError("Date of birth must be in the past.")
        return dob

    def clean_roll_no(self):
        return self.cleaned_data["roll_no"].strip().upper()

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Homework, Submission


class RegisterForm(UserCreationForm):
    role = forms.ChoiceField(choices=[
        ("teacher", "Teacher"),
        ("student", "Student"),
    ])

    class Meta:
        model = User
        fields = ["username", "role", "password1", "password2"]


class HomeworkForm(forms.ModelForm):
    class Meta:
        model = Homework
        fields = ["title", "subject", "description", "due_date"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"})
        }


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ["file"]

    def clean_file(self):
        uploaded_file = self.cleaned_data.get("file")
        allowed = (".pdf", ".doc", ".docx", ".txt", ".jpg", ".jpeg", ".png")

        if uploaded_file:
            if not uploaded_file.name.lower().endswith(allowed):
                raise forms.ValidationError(
                    "Upload PDF, Word, text or image files only."
                )

            if uploaded_file.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Maximum file size is 5 MB.")

        return uploaded_file
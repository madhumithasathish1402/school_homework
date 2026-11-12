from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import HomeworkSerializer

from .models import Profile, Homework, Submission, Notification
from .forms import RegisterForm, HomeworkForm, SubmissionForm


def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            profile = Profile.objects.filter(user=request.user).first()

            if not profile or profile.role != role:
                return HttpResponseForbidden("You do not have permission.")

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator


def home(request):
    if request.user.is_authenticated:
        profile = Profile.objects.filter(user=request.user).first()

        if profile and profile.role == "teacher":
            return redirect("teacher_dashboard")

        if profile and profile.role == "student":
            return redirect("student_dashboard")

    return render(request, "base.html")


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            Profile.objects.create(
                user=user,
                role=form.cleaned_data["role"]
            )
            messages.success(request, "Account created. Please login.")
            return redirect("login")
    else:
        form = RegisterForm()

    return render(request, "register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(
            request, username=username, password=password
        )

        if user is not None:
            profile = Profile.objects.filter(user=user).first()

            if profile is None:
                messages.error(request, "Your account has no role.")
            else:
                login(request, user)

                if profile.role == "teacher":
                    return redirect("teacher_dashboard")

                return redirect("student_dashboard")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "login.html")


@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("login")

    return redirect("home")


@role_required("teacher")
def teacher_dashboard(request):
    homework_list = Homework.objects.filter(
        teacher=request.user
    ).order_by("-created_at")

    submissions = Submission.objects.filter(
        homework__teacher=request.user
    ).select_related("homework", "student").order_by("-submitted_at")

    return render(request, "teacher_dashboard.html", {
        "homework_list": homework_list,
        "submissions": submissions,
    })


@role_required("teacher")
def add_homework(request):
    if request.method == "POST":
        form = HomeworkForm(request.POST)

        if form.is_valid():
            homework = form.save(commit=False)
            homework.teacher = request.user
            homework.save()

            students = User.objects.filter(
                profile__role="student"
            )

            for student in students:
                Notification.objects.create(
                    user=student,
                    message=f"New homework: {homework.title}"
                )

            messages.success(request, "Homework sent to students.")
            return redirect("teacher_dashboard")
    else:
        form = HomeworkForm()

    return render(request, "add_homework.html", {"form": form})


@role_required("teacher")
def edit_homework(request, homework_id):
    homework = get_object_or_404(
        Homework, id=homework_id, teacher=request.user
    )

    if request.method == "POST":
        form = HomeworkForm(request.POST, instance=homework)

        if form.is_valid():
            form.save()
            messages.success(request, "Homework updated.")
            return redirect("teacher_dashboard")
    else:
        form = HomeworkForm(instance=homework)

    return render(request, "add_homework.html", {
        "form": form,
        "editing": True,
    })


@role_required("teacher")
def delete_homework(request, homework_id):
    homework = get_object_or_404(
        Homework, id=homework_id, teacher=request.user
    )

    if request.method == "POST":
        homework.delete()
        messages.success(request, "Homework deleted.")

    return redirect("teacher_dashboard")


@role_required("student")
def student_dashboard(request):
    homework_list = Homework.objects.all().order_by("-created_at")

    submitted_ids = Submission.objects.filter(
        student=request.user
    ).values_list("homework_id", flat=True)

    return render(request, "student_dashboard.html", {
        "homework_list": homework_list,
        "submitted_ids": list(submitted_ids),
    })


@role_required("student")
def submit_homework(request, homework_id):
    homework = get_object_or_404(Homework, id=homework_id)

    existing = Submission.objects.filter(
        homework=homework,
        student=request.user
    ).first()

    if request.method == "POST":
        form = SubmissionForm(
            request.POST,
            request.FILES,
            instance=existing
        )

        if form.is_valid():
            submission = form.save(commit=False)
            submission.homework = homework
            submission.student = request.user
            submission.save()

            Notification.objects.create(
                user=homework.teacher,
                message=(
                    f"{request.user.username} submitted "
                    f"homework: {homework.title}"
                )
            )

            messages.success(request, "Homework submitted successfully.")
            return redirect("student_dashboard")
    else:
        form = SubmissionForm(instance=existing)

    return render(request, "submit_homework.html", {
        "form": form,
        "homework": homework,
    })


@login_required
def notifications_view(request):
    if request.method == "POST":
        Notification.objects.filter(
            user=request.user
        ).update(is_read=True)

        return redirect("notifications")

    notification_list = Notification.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(request, "notifications.html", {
        "notification_list": notification_list,
    })

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def api_homeworks(request):
    if request.method == "GET":
        homework_list = Homework.objects.all().order_by("-created_at")
        serializer = HomeworkSerializer(homework_list, many=True)
        return Response(serializer.data)

    profile = Profile.objects.filter(user=request.user).first()

    if not profile or profile.role != "teacher":
        return Response(
            {"error": "Only teachers can create homework."},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = HomeworkSerializer(data=request.data)

    if serializer.is_valid():
        homework = serializer.save(teacher=request.user)

        students = User.objects.filter(profile__role="student")

        for student in students:
            Notification.objects.create(
                user=student,
                message=f"New homework: {homework.title}"
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def api_homework_detail(request, homework_id):
    homework = get_object_or_404(Homework, id=homework_id)

    if request.method == "GET":
        serializer = HomeworkSerializer(homework)
        return Response(serializer.data)

    profile = Profile.objects.filter(user=request.user).first()

    if (
        not profile
        or profile.role != "teacher"
        or homework.teacher_id != request.user.id
    ):
        return Response(
            {"error": "Only the homework's teacher can edit or delete it."},
            status=status.HTTP_403_FORBIDDEN
        )

    if request.method == "DELETE":
        homework.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = HomeworkSerializer(
        homework,
        data=request.data,
        partial=(request.method == "PATCH")
    )

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
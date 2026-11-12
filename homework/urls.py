from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("teacher/", views.teacher_dashboard, name="teacher_dashboard"),
    path("homework/add/", views.add_homework, name="add_homework"),
    path(
        "homework/edit/<int:homework_id>/",
        views.edit_homework,
        name="edit_homework",
    ),
    path(
        "homework/delete/<int:homework_id>/",
        views.delete_homework,
        name="delete_homework",
    ),

    path("student/", views.student_dashboard, name="student_dashboard"),
    path(
        "homework/submit/<int:homework_id>/",
        views.submit_homework,
        name="submit_homework",
    ),
    path("notifications/", views.notifications_view, name="notifications"),
    path("api/homeworks/", views.api_homeworks, name="api_homeworks"),
    path(
        "api/homeworks/<int:homework_id>/",
        views.api_homework_detail,
        name="api_homework_detail",
    ),
]
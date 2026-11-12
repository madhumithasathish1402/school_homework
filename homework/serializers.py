from rest_framework import serializers
from .models import Homework


class HomeworkSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(
        source="teacher.username",
        read_only=True
    )

    class Meta:
        model = Homework
        fields = [
            "id",
            "title",
            "subject",
            "description",
            "due_date",
            "teacher_name",
            "created_at",
        ]
        read_only_fields = ["id", "teacher_name", "created_at"]
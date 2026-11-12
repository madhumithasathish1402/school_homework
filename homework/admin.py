from django.contrib import admin
from .models import Profile, Homework, Submission, Notification

admin.site.register(Profile)
admin.site.register(Homework)
admin.site.register(Submission)
admin.site.register(Notification)
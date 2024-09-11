from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from . import models
# Register your models here.

admin.site.register(models.Room)
admin.site.register(models.Department)
admin.site.register(models.Comment)
admin.site.register(models.Judgement)
admin.site.unregister(User)


class InterviewerInline(admin.StackedInline):
    model = models.Interviewer
    can_delete = False
    verbose_name_plural = 'interviewer'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (InterviewerInline,)


@admin.register(models.Interviewee)
class IntervieweeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'majar_text', 'interview_status',
                    'first_preference', 'second_preference', 'admitted_department')
    list_filter = (
        "interview_status",
        "first_preference",
        "second_preference",
        "admitted_department",
    )

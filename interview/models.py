from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm, Form
# Create your models here.


class Department(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Room(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class Interviewer(models.Model):
    INTERVIEW_IDENTITY = (
        (1, "侯场教室"),
        (2, "面试教室")
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    interview_identity = models.IntegerField(choices=INTERVIEW_IDENTITY)
    department = models.ForeignKey(
        Department, blank=True, null=True, on_delete=models.SET_NULL)
    room = models.ForeignKey(
        Room, blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.user.first_name


class Interviewee(models.Model):
    INTERVIEWEE_STATUS = (
        (1, "未签到"),
        (2, "已签到候场"),
        (3, "已经出发"),
        (4, "面试开始"),
        (5, "面试结束"),
        (6, "第一志愿队列"),
        (7, "第二志愿队列"),
        (8, "最终队列"),
        (9, "已录取")
    )
    name = models.CharField(max_length=30)
    sex = models.CharField(max_length=10)
    phone_number = models.CharField(max_length=20)
    student_id = models.CharField(max_length=15)
    majar_text = models.CharField(max_length=30)
    introduction_text = models.TextField()
    interview_status = models.IntegerField(choices=INTERVIEWEE_STATUS)
    accept_adjust = models.BooleanField()
    first_preference = models.ForeignKey(
        Department, blank=True, null=True, related_name="first_preference", on_delete=models.SET_NULL)
    second_preference = models.ForeignKey(
        Department, blank=True, null=True, related_name="second_preference", on_delete=models.SET_NULL)
    admitted_department = models.ForeignKey(
        Department, blank=True, null=True, related_name="admitted_department", on_delete=models.SET_NULL)
    assigned_room = models.ForeignKey(
        Room, blank=True, null=True, on_delete=models.SET_NULL)
    assigned_datetime = models.DateTimeField()

    def __str__(self):
        return self.name


class Comment(models.Model):
    content = models.TextField()
    interviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    interviewee = models.ForeignKey(Interviewee, on_delete=models.CASCADE)

    def __str__(self):
        return '%s-%s' % (self.interviewee, self.interviewer.first_name)


class PartialCommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['content']

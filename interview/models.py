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
    WAITING_ROOM = 1
    INTERVIEW_ROOM = 2
    OBSERVER = 3
    INTERVIEW_IDENTITY = (
        (WAITING_ROOM, "候场教室"),
        (INTERVIEW_ROOM, "面试教室"),
        (OBSERVER, "observer")
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
    NOT_CHECKED_IN = 1
    CHECKED_IN = 2
    INTERVIEW_READY = 3
    INTERVIEW_STARTED = 4
    INTERVIEW_END = 5
    FIRST_PREFERENCE_QUEUE = 6
    SECOND_PREFERENCE_QUEUE = 7
    FINAL_QUEUE = 8
    ADMITTED = 9
    INTERVIEWEE_STATUS = (
        (NOT_CHECKED_IN, "未签到"),
        (CHECKED_IN, "已签到候场"),
        (INTERVIEW_READY, "已分配教室准备出发"),
        (INTERVIEW_STARTED, "面试开始"),
        (INTERVIEW_END, "面试结束"),
        (FIRST_PREFERENCE_QUEUE, "第一志愿队列"),
        (SECOND_PREFERENCE_QUEUE, "第二志愿队列"),
        (FINAL_QUEUE, "最终队列"),
        (ADMITTED, "已录取")
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

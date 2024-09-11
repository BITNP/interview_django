from django.urls import path

from . import views

app_name = 'interview_api'

urlpatterns = [
     path('interviewees/<int:interviewee_id>/comment',
         views.interviewee_comment_api, name='interviewee_comment_api'),
    path('interviewees/<int:interviewee_id>/judge',
         views.interviewee_judge_api, name='interviewee_judge_api'),
     path('interviewees/',
         views.interviewee_list_api, name='interviewee_list_api')
]

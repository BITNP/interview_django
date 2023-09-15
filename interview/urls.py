from django.urls import path

from . import views

app_name = 'interview'

urlpatterns = [
    path('', views.index, name='index'),
    path('public',
         views.public_index, name='public_index'),

    path('interviewees',
         views.interviewee_index, name='interviewee_index'),
    path('interviewees/<int:interviewee_id>/checkin',
         views.interviewee_checkin, name='interviewee_checkin'),

    path('rooms/<int:room_id>/interviewees/<int:interviewee_id>/assign',
         views.interviewee_assign, name='interviewee_assign'),
    path('rooms/<int:room_id>/interviewees',
         views.room_index, name='room_index'),
    path('rooms/<int:room_id>/interviewees/<int:interviewee_id>',
         views.room_interviewee_detail, name='room_interviewee_detail'),
    path('rooms/<int:room_id>/interviewees/<int:interviewee_id>/start',
         views.room_interviewee_start, name='room_interviewee_start'),
    path('rooms/<int:room_id>/interviewees/<int:interviewee_id>/end',
         views.room_interviewee_end, name='room_interviewee_end'),
    path('rooms/<int:room_id>/interviewees/<int:interviewee_id>/comment',
         views.room_interviewee_comment, name='room_interviewee_comment'),
     path('api/interviewees/<int:interviewee_id>/comment',
         views.interviewee_comment_api, name='interviewee_comment_api')
]

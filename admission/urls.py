from django.urls import path

from . import views

app_name = "admission"

urlpatterns = [
    path("", views.index, name="index"),
    path(
        "admission_start", views.admission_start_adminview, name="admission_start_admin"
    ),
    path(
        "departments/<int:department_id>/interviewees",
        views.department_index,
        name="department_index",
    ),
    path(
        "departments/<int:department_id>/interviewees/<int:interviewee_id>",
        views.interviewee_detail,
        name="interviewee_detail",
    ),
    path(
        "departments/<int:department_id>/interviewees/<int:interviewee_id>/admit",
        views.interviewee_admit,
        name="interviewee_admit",
    ),
    path(
        "departments/<int:department_id>/interviewees/<int:interviewee_id>/reject",
        views.interviewee_reject,
        name="interviewee_reject",
    ),
    path(
        "departments/<int:department_id>/admitted",
        views.department_admitted,
        name="department_admitted",
    ),
    path(
        "departments/<int:department_id>/admitted/download_csv",
        views.department_admitted_csv,
        name="department_admitted_csv",
    ),
    path("final_queue", views.final_queue_index, name="final_queue_index"),
    path(
        "final_queue_detail/<int:interviewee_id>/interviewees",
        views.final_queue_detail,
        name="final_queue_detail",
    ),
    path(
        "final_queue_admit/<int:department_id>/<int:interviewee_id>",
        views.final_queue_admit,
        name="final_queue_admit",
    ),
]

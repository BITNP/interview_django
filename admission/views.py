from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.views import generic
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils.html import escape
from django.db.models import Q
import csv
from interview.models import *


def Forbidden(msg=None):
    if msg is None:
        msg = "If you think that this is a bug, please contact the project maintainer."
    return HttpResponseForbidden(f"<h1>Forbidden</h1><p>{msg}</p><p><button onclick='window.history.back()'>返回</button></p>")


def index(request):
    gconf = Global.get()
    if gconf.status == Global.INTERVIEW:
        return Forbidden(f"当前状态为 <b> {gconf.get_status_display()} </b><br/> 请联系超管更改状态！")
    return render(request, "admission/index.html")


@login_required()
def admission_start_adminview(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return Forbidden()
    interviewees = Interviewee.objects.filter(
        interview_status=Interviewee.INTERVIEW_END
    )
    if request.method == "POST":
        interviewees.update(interview_status=Interviewee.FIRST_PREFERENCE_QUEUE)
        gconf = Global.get()
        gconf.status = Global.ADMISSION
        gconf.save()
        return HttpResponse("done")
    interviewee_list = interviewees.all()
    return render(
        request,
        "admission/admission_start_admin.html",
        context={"interviewee_list": interviewee_list},
    )


@login_required()
def department_index(request, department_id):
    user_department_id = request.user.interviewer.department_id
    if user_department_id != department_id:
        return Forbidden()
    department = get_object_or_404(Department, pk=department_id)
    interviewee_list = Interviewee.objects.filter(
        Q(
            first_preference=department,
            interview_status=Interviewee.FIRST_PREFERENCE_QUEUE,
        )
        | Q(
            second_preference=department,
            interview_status=Interviewee.SECOND_PREFERENCE_QUEUE,
        )
    ).all()
    context = {"department_id": department_id, "interviewee_list": interviewee_list}
    return render(request, "admission/department_index.html", context=context)


@login_required()
def department_admitted(request, department_id):
    department = get_object_or_404(Department, pk=department_id)
    department_list = Department.objects.all()
    interviewee_list = Interviewee.objects.filter(
        admitted_department=department, interview_status=Interviewee.ADMITTED
    ).all()
    context = {
        "department_id": department_id,
        "interviewee_list": interviewee_list,
        "department_list": department_list,
    }
    return render(request, "admission/department_admitted.html", context=context)


@login_required()
def interviewee_detail(request, department_id, interviewee_id):
    user_department_id = request.user.interviewer.department_id
    if user_department_id != department_id:
        return Forbidden()
    interviewee = get_object_or_404(Interviewee, pk=interviewee_id)
    if (
        interviewee.interview_status < Interviewee.FIRST_PREFERENCE_QUEUE
        or interviewee.interview_status > Interviewee.SECOND_PREFERENCE_QUEUE
    ):
        return Forbidden()
    comment_list = Comment.objects.filter(interviewee=interviewee)
    judgement_list = Judgement.objects.filter(interviewee=interviewee)
    context = {
        "department_id": department_id,
        "interviewee": interviewee,
        "comment_list": comment_list,
        "judgement_list": judgement_list,
    }
    return render(request, "admission/interviewee_detail.html", context=context)


@login_required()
def interviewee_admit(request, department_id, interviewee_id):
    user_department_id = request.user.interviewer.department_id
    if user_department_id != department_id:
        return Forbidden()
    department = get_object_or_404(Department, pk=department_id)
    interviewee = get_object_or_404(Interviewee, pk=interviewee_id)
    if interviewee.interview_status == Interviewee.FIRST_PREFERENCE_QUEUE:
        if interviewee.first_preference != department:
            return Forbidden()
        interviewee.admitted_department = department
        interviewee.interview_status = Interviewee.ADMITTED
        interviewee.save()
    elif interviewee.interview_status == Interviewee.SECOND_PREFERENCE_QUEUE:
        if interviewee.second_preference != department:
            return Forbidden()
        interviewee.admitted_department = department
        interviewee.interview_status = Interviewee.ADMITTED
        interviewee.save()
    else:
        return Forbidden()
    return HttpResponseRedirect(
        reverse("admission:department_index", args=(department_id,))
    )


@login_required()
def interviewee_reject(request, department_id, interviewee_id):
    user_department_id = request.user.interviewer.department_id
    if user_department_id != department_id:
        return Forbidden()
    department = get_object_or_404(Department, pk=department_id)
    interviewee = get_object_or_404(Interviewee, pk=interviewee_id)
    if interviewee.interview_status == Interviewee.FIRST_PREFERENCE_QUEUE:
        if interviewee.first_preference != department:
            return Forbidden()
        if interviewee.accept_adjust:
            interviewee.interview_status = Interviewee.SECOND_PREFERENCE_QUEUE
        else:
            interviewee.interview_status = Interviewee.FINAL_QUEUE
        interviewee.save()
    elif interviewee.interview_status == Interviewee.SECOND_PREFERENCE_QUEUE:
        if interviewee.second_preference != department:
            return Forbidden()
        interviewee.interview_status = Interviewee.FINAL_QUEUE
        interviewee.save()
    else:
        return Forbidden()
    return HttpResponseRedirect(
        reverse("admission:department_index", args=(department_id,))
    )


@login_required()
def final_queue_index(request):
    interviewee_list = Interviewee.objects.filter(
        interview_status=Interviewee.FINAL_QUEUE
    ).all()
    context = {"interviewee_list": interviewee_list}
    return render(request, "admission/final_queue_index.html", context=context)


@login_required()
def final_queue_detail(request, interviewee_id):
    department = request.user.interviewer.department
    interviewee = get_object_or_404(Interviewee, pk=interviewee_id)
    comment_list = Comment.objects.filter(interviewee=interviewee)
    context = {
        "interviewee": interviewee,
        "department": department,
        "comment_list": comment_list,
    }
    return render(request, "admission/final_queue_detail.html", context=context)


@login_required()
def final_queue_admit(request, department_id, interviewee_id):
    user_department_id = request.user.interviewer.department_id
    department = get_object_or_404(Department, pk=department_id)
    interviewee = get_object_or_404(Interviewee, pk=interviewee_id)
    if user_department_id != department_id:
        return Forbidden()
    if interviewee.interview_status != Interviewee.FINAL_QUEUE:
        return Forbidden()
    interviewee.admitted_department = department
    interviewee.interview_status = Interviewee.ADMITTED
    interviewee.save()
    return HttpResponseRedirect(reverse("admission:final_queue_index"))


@login_required()
def department_admitted_csv(request, department_id):
    department = get_object_or_404(Department, pk=department_id)
    interviewee_list = Interviewee.objects.filter(
        admitted_department=department, interview_status=Interviewee.ADMITTED
    ).all()
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename={department.id}.csv"

    writer = csv.writer(response)
    writer.writerow(
        ("name", "sex", "student_id", "phone_number", "admitted_department")
    )
    for it in interviewee_list:
        writer.writerow(
            (it.name, it.sex, it.student_id, it.phone_number, it.admitted_department)
        )
    return response

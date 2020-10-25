from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.views import generic
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from interview import models
from django.utils.html import escape
from django.db.models import Q
# Create your views here.


def Forbidden():
    return HttpResponseForbidden("403 Forbidden. What are you doing?")


def index(request):
    return render(request, 'admission/index.html')


@login_required()
def admission_start_adminview(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return Forbidden()
    interviewees = models.Interviewee.objects.filter(interview_status=5)
    if request.method == 'POST':
        interviewees.update(interview_status=6)
        return HttpResponse("done")
    interviewee_list = interviewees.all()
    return render(request, "admission/admission_start_admin.html", context={'interviewee_list': interviewee_list})


@login_required()
def department_index(request, department_id):
    if request.user.interviewer.department_id != department_id:
        return Forbidden()
    department = get_object_or_404(models.Department, pk=department_id)
    interviewee_list = models.Interviewee.objects.filter(
        Q(first_preference=department, interview_status=6) | Q(second_preference=department, interview_status=7)).all()
    context = {
        'department_id': department_id,
        'interviewee_list': interviewee_list
    }
    return render(request, 'admission/department_index.html', context=context)


@login_required()
def department_admitted(request, department_id):
    department_list = models.Department.objects.all()
    interviewee_list = models.Interviewee.objects.filter(
        admitted_department_id=department_id, interview_status=9).all()
    context = {
        'department_id': department_id,
        'interviewee_list': interviewee_list,
        'department_list': department_list
    }
    return render(request, 'admission/department_admitted.html', context=context)


@login_required()
def interviewee_detail(request, department_id, interviewee_id):
    if request.user.interviewer.department_id != department_id:
        return Forbidden()
    interviewee = get_object_or_404(models.Interviewee, pk=interviewee_id)
    if interviewee.interview_status < 6 or interviewee.interview_status > 8:
        return Forbidden()
    context = {
        'department_id': department_id,
        'interviewee': interviewee
    }
    return render(request, 'admission/interviewee_detail.html', context=context)


@login_required()
def interviewee_admit(request, department_id, interviewee_id):
    if request.user.interviewer.department_id != department_id:
        return Forbidden()
    department = get_object_or_404(models.Department, pk=department_id)
    interviewee = get_object_or_404(models.Interviewee, pk=interviewee_id)
    if interviewee.interview_status == 6:
        if interviewee.first_preference != department:
            return Forbidden()
        interviewee.admitted_department = department
        interviewee.interview_status = 9
        interviewee.save()
    elif interviewee.interview_status == 7:
        if interviewee.second_preference != department:
            return Forbidden()
        interviewee.admitted_department = department
        interviewee.interview_status = 9
        interviewee.save()
    else:
        return Forbidden()
    return HttpResponseRedirect(reverse('admission:department_index', args=(department_id, )))


@login_required()
def interviewee_reject(request, department_id, interviewee_id):
    if request.user.interviewer.department_id != department_id:
        return Forbidden()
    department = get_object_or_404(models.Department, pk=department_id)
    interviewee = get_object_or_404(models.Interviewee, pk=interviewee_id)
    if interviewee.interview_status == 6:
        if interviewee.first_preference != department:
            return Forbidden()
        if interviewee.accept_adjust:
            interviewee.interview_status = 7
        else:
            interviewee.interview_status = 8
        interviewee.save()
    elif interviewee.interview_status == 7:
        if interviewee.second_preference != department:
            return Forbidden()
        interviewee.interview_status = 8
    else:
        return Forbidden()
    return HttpResponseRedirect(reverse('admission:department_index', args=(department_id, )))


@login_required()
def final_queue_index(request):
    interviewee_list = models.Interviewee.objects.filter(
        interview_status=8).all()
    context = {
        'interviewee_list': interviewee_list
    }
    return render(request, 'admission/final_queue_index.html', context=context)


@login_required()
def final_queue_detail(request, interviewee_id):
    department_list = models.Department.objects.all()
    interviewee = get_object_or_404(models.Interviewee, pk=interviewee_id)
    context = {
        'interviewee': interviewee,
        'department_list': department_list
    }
    return render(request, 'admission/final_queue_detail.html', context=context)


@login_required()
def final_queue_admit(request, department_id, interviewee_id):
    department = get_object_or_404(models.Department, pk=department_id)
    interviewee = get_object_or_404(models.Interviewee, pk=interviewee_id)
    if interviewee.interview_status != 8:
        return Forbidden()
    interviewee.admitted_department = department
    interviewee.interview_status = 9
    interviewee.save()
    return HttpResponseRedirect(reverse('admission:final_queue_index'))

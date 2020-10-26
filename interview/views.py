from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.views import generic
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from . import models

# Create your views here.


def Forbidden():
    return HttpResponseForbidden("403 Forbidden. What are you doing?")


def index(request):
    return render(request, 'interview/index.html')


def public_index(request):
    interviewee_list = models.Interviewee.objects.filter(
        interview_status__lt=5).order_by('-interview_status', 'assigned_datetime').all()
    context = {
        'interviewee_list': interviewee_list
    }
    return render(request, 'interview/public_index.html', context=context)


@login_required
def interviewee_index(request):
    if request.user.interviewer.interview_identity != 1:
        return Forbidden()
    room_list = models.Room.objects.all()
    interviewee_list = models.Interviewee.objects.filter(
        interview_status__lt=5).order_by('-interview_status', 'assigned_datetime').all()
    context = {
        'interviewee_list': interviewee_list,
        'room_list': room_list
    }
    return render(request, 'interview/interviewee_index.html', context=context)


@login_required
def interviewee_checkin(request, interviewee_id):
    if request.user.interviewer.interview_identity != 1:
        return Forbidden()
    interviewee = get_object_or_404(models.Interviewee, pk=interviewee_id)
    if interviewee.interview_status == 1:
        interviewee.interview_status = 2
        interviewee.save()
    else:
        return Forbidden()
    return HttpResponseRedirect(reverse('interview:interviewee_index'))


@login_required()
def room_index(request, room_id):
    if request.user.interviewer.interview_identity != 2:
        return Forbidden()
    if request.user.interviewer.room.id != room_id:
        return Forbidden()
    room = get_object_or_404(models.Room, pk=room_id)
    interviewee_list = models.Interviewee.objects.filter(Q(assigned_room=room) | Q(
        interview_status=2)).order_by('interview_status', 'assigned_datetime').all()
    context = {
        'room_id': room_id,
        'interviewee_list': interviewee_list
    }
    return render(request, 'interview/room_index.html', context=context)


@login_required()
def room_interviewee_detail(request, room_id, interviewee_id):
    if request.user.interviewer.interview_identity != 2:
        return Forbidden()
    if request.user.interviewer.room.id != room_id:
        return Forbidden()
    interviewee = get_object_or_404(models.Interviewee, pk=interviewee_id)
    if interviewee.interview_status < 3:
        return Forbidden()
    if interviewee.assigned_room.id != room_id:
        return Forbidden()
    comment_list = models.Comment.objects.filter(interviewee=interviewee).all()
    comment_form = models.PartialCommentForm()
    context = {
        'room_id': room_id,
        'interviewee': interviewee,
        'comment_list': comment_list,
        'comment_form': comment_form
    }
    return render(request, 'interview/room_interviewee_detail.html', context=context)


@login_required
def interviewee_assign(request, room_id, interviewee_id):
    if request.user.interviewer.interview_identity != 2:
        return Forbidden()
    if request.user.interviewer.room.id != room_id:
        return Forbidden()
    room = get_object_or_404(models.Room, pk=room_id)
    interviewee = get_object_or_404(models.Interviewee, pk=interviewee_id)
    if interviewee.interview_status == 2:
        interviewee.assigned_room = room
        interviewee.interview_status = 3
        interviewee.save()
    else:
        return Forbidden()
    return HttpResponseRedirect(reverse('interview:room_interviewee_detail', args=(room_id, interviewee_id)))


@login_required()
def room_interviewee_start(request, room_id, interviewee_id):
    if request.user.interviewer.interview_identity != 2:
        return Forbidden()
    if request.user.interviewer.room.id != room_id:
        return Forbidden()
    interviewee = get_object_or_404(models.Interviewee, pk=interviewee_id)
    if interviewee.assigned_room.id != room_id:
        return Forbidden()
    if interviewee.interview_status == 3:
        interviewee.interview_status = 4
        interviewee.save()
    else:
        return Forbidden()
    return HttpResponseRedirect(reverse('interview:room_interviewee_detail', args=(room_id, interviewee_id)))


@login_required()
def room_interviewee_end(request, room_id, interviewee_id):
    if request.user.interviewer.interview_identity != 2:
        return Forbidden()
    if request.user.interviewer.room.id != room_id:
        return Forbidden()
    interviewee = get_object_or_404(models.Interviewee, pk=interviewee_id)
    if interviewee.assigned_room.id != room_id:
        return Forbidden()
    if interviewee.interview_status == 4:
        interviewee.interview_status = 5
        interviewee.save()
    else:
        return Forbidden()
    return HttpResponseRedirect(reverse('interview:room_index', args=(room_id, )))


@login_required()
def room_interviewee_comment(request, room_id, interviewee_id):
    if request.user.interviewer.interview_identity != 2:
        return Forbidden()
    if request.user.interviewer.room.id != room_id:
        return Forbidden()
    if request.method == 'POST':
        interviewee = get_object_or_404(models.Interviewee, pk=interviewee_id)
        if interviewee.assigned_room.id != room_id:
            return Forbidden()
        if interviewee.interview_status < 4:
            return Forbidden()
        form = models.PartialCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.interviewer = request.user
            comment.interviewee = interviewee
            comment.save()
    return HttpResponseRedirect(reverse('interview:room_interviewee_detail', args=(room_id, interviewee_id)))

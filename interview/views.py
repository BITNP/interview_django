from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, JsonResponse
from django.views import generic
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from .models import *
from django.utils import timezone

# Create your views here.


def Forbidden():
    return HttpResponseForbidden("<h1>Forbidden</h1><p>If you think that this is a bug, please contact the project maintainer.</p>")


def index(request):
    room_list = Room.objects.all()
    context = {'room_list': room_list}
    return render(request, 'interview/index.html', context=context)


def public_index(request):
    """
    候场教室显示的面试当前状态视图，公开
    """
    interviewee_list = Interviewee.objects \
        .filter(interview_status__lt=Interviewee.INTERVIEW_END) \
        .order_by('-interview_status', 'assigned_datetime').all()
    context = {
        'interviewee_list': interviewee_list
    }
    return render(request, 'interview/public_index.html', context=context)


@login_required
def interviewee_index(request):
    """
    候场教室工作人员，提供更详细的信息和签到功能
    列表显示面试未结束的人员，按照面试状态降序，时间升序
    """
    return render(request, 'interview/interviewee_index.html')


@login_required
def interviewee_checkin(request, interviewee_id):
    """
    签到
    """
    user_identity = request.user.interviewer.interview_identity
    if user_identity != Interviewer.WAITING_ROOM:
        return Forbidden()

    interviewee = get_object_or_404(Interviewee, pk=interviewee_id)

    if interviewee.interview_status == Interviewee.NOT_CHECKED_IN:
        interviewee.interview_status = Interviewee.CHECKED_IN
        interviewee.assigned_datetime = timezone.now()
        interviewee.save()
    return HttpResponseRedirect(reverse('interview:interviewee_index'))


@login_required()
def room_index(request, room_id):
    """
    面试教室面试官的面试者列表，只显示候场者和被拉来属于本教室的面试者
    按照面试状态升序，分配时间降序排列
    提供拉人功能和面试详情入口
    """
    user_identity = request.user.interviewer.interview_identity
    user_room_id = request.user.interviewer.room_id
    if user_identity == Interviewer.INTERVIEW_ROOM and user_room_id == room_id:
        readonly = False
    else:
        readonly = True

    room = get_object_or_404(Room, pk=room_id)
    interviewee_list = Interviewee.objects\
        .filter(Q(assigned_room=room) | Q(interview_status=Interviewee.CHECKED_IN))\
        .order_by('interview_status', 'assigned_datetime').all()
    context = {
        'room_id': room_id,
        'interviewee_list': interviewee_list,
        "readonly": readonly
    }
    return render(request, 'interview/room_index.html', context=context)


@login_required()
def room_interviewee_detail(request, room_id, interviewee_id):
    """
    面试官的面试者详情页面，提供评论和面试开始/结束
    """
    user_identity = request.user.interviewer.interview_identity
    user_room_id = request.user.interviewer.room_id
    if user_identity == Interviewer.INTERVIEW_ROOM and user_room_id == room_id:
        readonly = False
    else:
        readonly = True

    room = get_object_or_404(Room, pk=room_id)
    interviewee = get_object_or_404(Interviewee, pk=interviewee_id)
    if interviewee.interview_status < Interviewee.INTERVIEW_READY:
        return Forbidden()
    if interviewee.assigned_room_id != room.id:
        return Forbidden()

    comment_form = PartialCommentForm()
    context = {
        'room_id': room_id,
        'interviewee': interviewee,
        'comment_form': comment_form,
        "readonly": readonly
    }
    return render(request, 'interview/room_interviewee_detail.html', context=context)


@login_required
def interviewee_assign(request, room_id, interviewee_id):
    """
    将面试者分配到教室
    """
    user_identity = request.user.interviewer.interview_identity
    user_room_id = request.user.interviewer.room_id
    if user_identity != Interviewer.INTERVIEW_ROOM:
        return Forbidden()
    if user_room_id != room_id:
        return Forbidden()

    room = get_object_or_404(Room, pk=room_id)
    interviewee = get_object_or_404(Interviewee, pk=interviewee_id)
    if interviewee.interview_status < Interviewee.CHECKED_IN:
        return Forbidden()

    if interviewee.interview_status == Interviewee.CHECKED_IN:
        current_interviewee = Interviewee.objects\
            .filter(Q(interview_status=Interviewee.INTERVIEW_READY) | Q(interview_status=Interviewee.INTERVIEW_STARTED))\
            .filter(assigned_room=room).first()
        if not current_interviewee:
            interviewee.assigned_room = room
            interviewee.interview_status = Interviewee.INTERVIEW_READY
            interviewee.save()
        else:
            return HttpResponseRedirect(reverse('interview:room_index', args=(room_id, )))

    return HttpResponseRedirect(reverse('interview:room_interviewee_detail', args=(room_id, interviewee_id)))


@login_required()
def room_interviewee_start(request, room_id, interviewee_id):
    """
    面试者到教室，开始面试
    """
    user_identity = request.user.interviewer.interview_identity
    user_room_id = request.user.interviewer.room_id
    if user_identity != Interviewer.INTERVIEW_ROOM:
        return Forbidden()
    if user_room_id != room_id:
        return Forbidden()

    room = get_object_or_404(Room, pk=room_id)
    interviewee = get_object_or_404(Interviewee, pk=interviewee_id)
    if interviewee.interview_status < Interviewee.INTERVIEW_READY:
        return Forbidden()
    if interviewee.assigned_room.id != room.id:
        return Forbidden()

    if interviewee.interview_status == Interviewee.INTERVIEW_READY:
        interviewee.interview_status = Interviewee.INTERVIEW_STARTED
        interviewee.save()

    return HttpResponseRedirect(reverse('interview:room_interviewee_detail', args=(room_id, interviewee_id)))


@login_required()
def room_interviewee_end(request, room_id, interviewee_id):
    """
    结束面试
    """
    user_identity = request.user.interviewer.interview_identity
    user_room_id = request.user.interviewer.room_id
    if user_identity != Interviewer.INTERVIEW_ROOM:
        return Forbidden()
    if user_room_id != room_id:
        return Forbidden()

    room = get_object_or_404(Room, pk=room_id)
    interviewee = get_object_or_404(Interviewee, pk=interviewee_id)
    if interviewee.assigned_room.id != room.id:
        return Forbidden()

    if interviewee.interview_status == Interviewee.INTERVIEW_STARTED:
        interviewee.interview_status = Interviewee.INTERVIEW_END
        interviewee.save()

    return HttpResponseRedirect(reverse('interview:room_index', args=(room_id, )))


@login_required()
def room_interviewee_comment(request, room_id, interviewee_id):
    """
    给面试者添加评论
    """
    user_identity = request.user.interviewer.interview_identity
    user_room_id = request.user.interviewer.room_id
    if user_identity != Interviewer.INTERVIEW_ROOM:
        return Forbidden()
    if user_room_id != room_id:
        return Forbidden()

    if request.method == 'POST':
        interviewee = get_object_or_404(Interviewee, pk=interviewee_id)
        if interviewee.assigned_room.id != room_id:
            return Forbidden()
        if interviewee.interview_status < Interviewee.INTERVIEW_READY:
            return Forbidden()

        form = PartialCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.interviewer = request.user
            comment.interviewee = interviewee
            comment.save()
    return HttpResponseRedirect(reverse('interview:room_interviewee_detail', args=(room_id, interviewee_id)))

@login_required()
def interviewee_comment_api(request, interviewee_id):
    """
    获取评论的api
    """
    interviewee = get_object_or_404(Interviewee, pk=interviewee_id)
    if interviewee.interview_status < Interviewee.INTERVIEW_READY:
        return Forbidden()

    comment_list = Comment.objects.filter(interviewee=interviewee).all()
    resp = []
    for comment in comment_list:
        comment_dict = {"content": comment.content, "name": comment.interviewer.first_name}
        resp.append(comment_dict)
    return JsonResponse(resp, safe=False)

@login_required()
def interviewee_list_api(request):
    """
    获取面试者的api
    """
    user_identity = request.user.interviewer.interview_identity
    if user_identity == Interviewer.WAITING_ROOM:
        readonly = False
    else:
        readonly = True

    interviewee_list = Interviewee.objects\
        .filter(interview_status__lt=Interviewee.INTERVIEW_END)\
        .order_by('-interview_status', 'assigned_datetime').all()
    resp = []
    for interviewee in interviewee_list:
        interviewee_dict = {"readonly": readonly,
                            "id": interviewee.id,
                            "assigned_datetime": interviewee.assigned_datetime.astimezone().strftime("%Y-%m-%d %H:%M:%S"),
                            "name": interviewee.name,
                            "sex": interviewee.sex,
                            "student_id": interviewee.student_id,
                            "interview_status": interviewee.interview_status,
                            "interview_status_display": interviewee.get_interview_status_display(),
                            "first_preference": interviewee.first_preference.name,
                            "second_preference": interviewee.second_preference.name,
                            "assigned_room": interviewee.assigned_room}
        resp.append(interviewee_dict)
    return JsonResponse(resp, safe=False)

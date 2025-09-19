from django.shortcuts import render, get_object_or_404
from django.http import (
    HttpResponse,
    HttpResponseRedirect,
    HttpResponseForbidden,
    JsonResponse,
    StreamingHttpResponse,
)

from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from .models import *
from django.utils import timezone
import json
import time


def Forbidden(msg=None):
    if msg is None:
        msg = "If you think that this is a bug, please contact the project maintainer."
    return HttpResponseForbidden(f"<h1>Forbidden</h1><p>{msg}</p>")


def index(request):
    gconf = Global.get()
    if gconf is None:
        return Forbidden("请联系超管先加载全局状态数据！")
    room_list = Room.objects.all()
    department_list = Department.objects.all()

    # 传递当前用户身份信息供模板使用
    current_identity = None
    if request.user.is_authenticated and hasattr(request.user, 'interviewer'):
        current_identity = request.user.interviewer.interview_identity

    context = {
        "room_list": room_list,
        "department_list": department_list,
        "current_identity": current_identity,
        "OBSERVER": Interviewer.OBSERVER,
    }
    return render(request, "interview/index.html", context=context)


def public_index(request):
    """
    候场教室显示的面试当前状态视图，公开
    """
    interviewee_list = (
        Interviewee.objects.filter(
            interview_status__lt=Interviewee.INTERVIEW_END)
        .order_by("-interview_status", "assigned_datetime")
        .all()
    )
    context = {"interviewee_list": interviewee_list}
    return render(request, "interview/public_index.html", context=context)


@login_required
def interviewee_index(request):
    """
    候场教室工作人员，提供更详细的信息和签到功能
    列表显示面试未结束的人员，按照面试状态降序，时间升序
    """
    return render(request, "interview/interviewee_index.html")


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
    return HttpResponseRedirect(reverse("interview:interviewee_index"))


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
    interviewee_list = (
        Interviewee.objects.filter(
            Q(assigned_room=room) | Q(interview_status=Interviewee.CHECKED_IN)
        )
        .order_by("interview_status", "assigned_datetime")
        .all()
    )
    context = {
        "room_id": room_id,
        "interviewee_list": interviewee_list,
        "readonly": readonly,
    }
    return render(request, "interview/room_index.html", context=context)


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

    # 检查当前用户是否已经提交过评价
    existing_judgement = Judgement.objects.filter(
        interviewee=interviewee,
        interviewer=request.user
    ).first()

    comment_form = PartialCommentForm()
    # 如果已有评价，用现有数据初始化表单
    if existing_judgement:
        judgement_form = JudgementForm(instance=existing_judgement)
    else:
        judgement_form = JudgementForm()

    context = {
        "room_id": room_id,
        "interviewee": interviewee,
        "judge_form": judgement_form,
        "comment_form": comment_form,
        "readonly": readonly,
        "existing_judgement": existing_judgement,
    }
    return render(request, "interview/room_interviewee_detail.html", context=context)


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
        current_interviewee = (
            Interviewee.objects.filter(
                Q(interview_status=Interviewee.INTERVIEW_READY)
                | Q(interview_status=Interviewee.INTERVIEW_STARTED)
            )
            .filter(assigned_room=room)
            .first()
        )
        if not current_interviewee:
            interviewee.assigned_room = room
            interviewee.interview_status = Interviewee.INTERVIEW_READY
            interviewee.save()

            # Create a broadcast event in the database
            message = {
                'type': 'room_assignment',
                'data': {
                    'name': interviewee.name,
                    'room': room.name,
                    'timestamp': timezone.now().isoformat()
                }
            }
            BroadcastEvent.objects.create(message=message)
        else:
            return HttpResponseRedirect(
                reverse("interview:room_index", args=(room_id,))
            )

    return HttpResponseRedirect(
        reverse("interview:room_interviewee_detail",
                args=(room_id, interviewee_id))
    )


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
        interviewee.start_datetime = timezone.now()
        interviewee.save()

    return HttpResponseRedirect(
        reverse("interview:room_interviewee_detail",
                args=(room_id, interviewee_id))
    )


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
        interviewee.end_datetime = timezone.now()
        interviewee.save()

    return HttpResponseRedirect(reverse("interview:room_index", args=(room_id,)))


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

    if request.method == "POST":
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

            # 如果是Ajax请求，返回JSON响应
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'message': '评论添加成功'})
        else:
            # 如果是Ajax请求且表单无效，返回错误信息
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': '评论内容无效'}, status=400)

    return HttpResponseRedirect(
        reverse("interview:room_interviewee_detail",
                args=(room_id, interviewee_id))
    )


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
        comment_dict = {
            "content": comment.content,
            "name": comment.interviewer.first_name,
        }
        resp.append(comment_dict)
    return JsonResponse(resp, safe=False)


@login_required()
def room_interviewee_judge(request, room_id, interviewee_id):
    user_identity = request.user.interviewer.interview_identity
    user_room_id = request.user.interviewer.room_id
    if user_identity != Interviewer.INTERVIEW_ROOM:
        return Forbidden()
    if user_room_id != room_id:
        return Forbidden()

    if request.method == "POST":
        interviewee = get_object_or_404(Interviewee, pk=interviewee_id)
        if interviewee.assigned_room.id != room_id:
            return Forbidden()
        if interviewee.interview_status < Interviewee.INTERVIEW_READY:
            return Forbidden()

        # 检查是否已存在该用户对该面试者的评价
        existing_judgement = Judgement.objects.filter(
            interviewer=request.user,
            interviewee=interviewee
        ).first()

        if existing_judgement:
            # 更新现有评价
            form = JudgementForm(request.POST, instance=existing_judgement)
            if form.is_valid():
                form.save()
                # 如果是Ajax请求，返回JSON响应
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'success', 'message': '评价更新成功'})
            else:
                # 如果是Ajax请求且表单无效，返回错误信息
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': '评价数据无效'}, status=400)
        else:
            # 创建新评价
            form = JudgementForm(request.POST)
            if form.is_valid():
                judgement = form.save(commit=False)
                judgement.interviewer = request.user
                judgement.interviewee = interviewee
                judgement.save()
                # 如果是Ajax请求，返回JSON响应
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'success', 'message': '评价提交成功'})
            else:
                # 如果是Ajax请求且表单无效，返回错误信息
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': '评价数据无效'}, status=400)

    return HttpResponseRedirect(
        reverse("interview:room_interviewee_detail",
                args=(room_id, interviewee_id))
    )


@login_required()
def interviewee_judge_api(request, interviewee_id):
    interviewee = get_object_or_404(Interviewee, pk=interviewee_id)
    if interviewee.interview_status < Interviewee.INTERVIEW_READY:
        return Forbidden()

    # 获取该面试者的所有评价（所有面试官的评价）
    judgement_list = Judgement.objects.filter(interviewee=interviewee).all()
    resp = []

    if len(judgement_list) != 0:
        # 计算平均分
        total_representation = sum(j.representation for j in judgement_list)
        total_ability = sum(j.ability for j in judgement_list)
        total_cognition = sum(j.cognition for j in judgement_list)
        count = len(judgement_list)

        avg_representation = round(total_representation / count, 1)
        avg_ability = round(total_ability / count, 1)
        avg_cognition = round(total_cognition / count, 1)

        # 将平均分转换为星星显示
        def stars_display(rating):
            full_stars = int(rating)
            half_star = 1 if (rating - full_stars) >= 0.5 else 0
            empty_stars = 5 - full_stars - half_star

            result = "★" * full_stars
            if half_star:
                result += "☆"  # 可以考虑用其他符号表示半星，如 ⭐
            result += "☆" * empty_stars
            return result

        resp = [
            {"name": "表达能力",
                "content": f"{stars_display(avg_representation)} ({avg_representation}/5) - {count}人评价"},
            {"name": "专业能力",
                "content": f"{stars_display(avg_ability)} ({avg_ability}/5) - {count}人评价"},
            {"name": "对网协的认识",
                "content": f"{stars_display(avg_cognition)} ({avg_cognition}/5) - {count}人评价"},
        ]
    return JsonResponse(resp, safe=False)


@login_required()
def interviewee_list_api(request):
    """
    获取面试者的api，支持分页和搜索
    """
    user_identity = request.user.interviewer.interview_identity
    if user_identity == Interviewer.WAITING_ROOM:
        readonly = False
    else:
        readonly = True

    # 获取分页参数
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))

    # 获取搜索参数
    search_query = request.GET.get('search', '').strip()

    # 计算偏移量
    offset = (page - 1) * page_size

    # 构建查询集
    queryset = Interviewee.objects.filter(
        interview_status__lt=Interviewee.INTERVIEW_END)

    # 如果有搜索条件，添加搜索过滤（只搜索学号末四位）
    if search_query:
        # 确保搜索条件是数字且长度合理
        if search_query.isdigit() and len(search_query) >= 3:
            queryset = queryset.filter(student_id__endswith=search_query)

    # 获取总数
    total_count = queryset.count()

    # 获取分页数据
    interviewee_list = queryset.order_by(
        "-interview_status", "assigned_datetime")[offset:offset + page_size]

    data = []
    for interviewee in interviewee_list:
        fpn = interviewee.first_preference.name if interviewee.first_preference else ""
        spn = (
            interviewee.second_preference.name if interviewee.second_preference else ""
        )
        rn = interviewee.assigned_room.name if interviewee.assigned_room else ""
        interviewee_dict = {
            "readonly": readonly,
            "id": interviewee.id,
            "assigned_datetime": interviewee.assigned_datetime.astimezone().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "name": interviewee.name,
            "sex": interviewee.sex,
            "student_id": interviewee.student_id,
            "email": interviewee.email,
            "interview_status": interviewee.interview_status,
            "interview_status_display": interviewee.get_interview_status_display(),
            "first_preference": fpn,
            "second_preference": spn,
            "assigned_room": rn,
        }
        data.append(interviewee_dict)

    # 计算总页数
    total_pages = (total_count + page_size - 1) // page_size

    # 返回分页信息
    resp = {
        "data": data,
        "pagination": {
            "current_page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1
        },
        "search": search_query
    }

    return JsonResponse(resp, safe=False)


@login_required()
def interviewer_change_room(request, room_id):
    user_identity = request.user.interviewer.interview_identity
    if user_identity != Interviewer.INTERVIEW_ROOM:
        Forbidden()

    request.user.interviewer.room = Room.objects.get(pk=room_id)
    request.user.interviewer.save()

    return HttpResponseRedirect(reverse("interview:index"))


@login_required()
def interviewer_change_identity(request, identity_id):
    """
    切换面试官身份
    """
    # 验证身份ID是否有效
    valid_identities = [choice[0] for choice in Interviewer.INTERVIEW_IDENTITY]
    if identity_id not in valid_identities:
        return Forbidden("无效的身份ID")

    # 如果用户没有面试身份，创建一个
    if not hasattr(request.user, 'interviewer') or not request.user.interviewer:
        Interviewer.objects.create(
            user=request.user,
            interview_identity=identity_id,
            department=Department.objects.first()  # 设置一个默认部门
        )
    else:
        # 更新现有身份
        request.user.interviewer.interview_identity = identity_id
        request.user.interviewer.save()

    return HttpResponseRedirect(reverse("interview:index"))


@login_required()
def setup_interviewer(request):
    """
    设置面试官身份和部门的视图
    """
    if request.method == 'POST':
        interview_identity = request.POST.get('interview_identity')
        department_id = request.POST.get('department')

        # 验证身份ID是否有效
        valid_identities = [choice[0]
                            for choice in Interviewer.INTERVIEW_IDENTITY]
        try:
            identity_id = int(interview_identity)
            if identity_id not in valid_identities:
                return Forbidden("无效的身份ID")
        except (ValueError, TypeError):
            return Forbidden("无效的身份ID")

        # 验证部门ID是否有效
        try:
            department = Department.objects.get(id=department_id)
        except Department.DoesNotExist:
            return Forbidden("无效的部门ID")

        # 如果用户没有面试身份，创建一个
        if not hasattr(request.user, 'interviewer') or not request.user.interviewer:
            Interviewer.objects.create(
                user=request.user,
                interview_identity=identity_id,
                department=department
            )
        else:
            # 更新现有身份和部门
            request.user.interviewer.interview_identity = identity_id
            request.user.interviewer.department = department
            request.user.interviewer.save()

        return HttpResponseRedirect(reverse("interview:index"))

    # GET请求重定向到首页
    return HttpResponseRedirect(reverse("interview:index"))

def assignment_events_sse(request):
    """
    SSE端点，用于通过数据库轮询实时推送教室分配事件
    """
    def event_stream():
        last_id = 0
        if BroadcastEvent.objects.exists():
            last_id = BroadcastEvent.objects.latest('id').id

        # Send connection established message
        yield f"data: {json.dumps({'type': 'connected', 'message': 'SSE connection established using db-polling'})}\n\n"

        while True:
            events = BroadcastEvent.objects.filter(id__gt=last_id).order_by('id')

            if events.exists():
                for event in events:
                    yield f"data: {json.dumps(event.message)}\n\n"
                    last_id = event.id
            else:
                # Send a heartbeat to keep the connection alive
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': timezone.now().isoformat()})}\n\n"

            # Sleep for a short duration before polling again
            time.sleep(2)

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Headers'] = 'Cache-Control'
    return response

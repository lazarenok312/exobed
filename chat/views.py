from django.contrib.auth.models import User
from django.db.models import Q
from django.http.response import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from chat.models import Message
from chat.serializers import MessageSerializer, UserSerializer


@csrf_exempt
def message_list(request, sender=None, receiver=None):
    if request.method == 'GET':
        messages = Message.objects.filter(sender_id=sender, receiver_id=receiver, is_read=False)
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        for message in messages:
            message.is_read = True
            message.save()
        return JsonResponse(serializer.data, safe=False)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = MessageSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)


def chat_view(request):
    if request.method == "GET":
        users = User.objects.exclude(username=request.user.username)

        support_users = [user for user in users if user.is_staff]
        regular_users = [user for user in users if not user.is_staff]

        support_displayed = False
        user_displayed = False

        for user in users:
            latest_message = Message.objects.filter(
                Q(sender=request.user, receiver=user) | Q(sender=user, receiver=request.user)
            ).last()
            user.latest_message = latest_message
            not_read_count = Message.objects.filter(sender=user, receiver=request.user, is_read=False).count()
            user.not_read_count = not_read_count

        if 'user_id' in request.GET:
            user_id = request.GET.get('user_id')
            sender = get_object_or_404(User, id=user_id)
            Message.objects.filter(sender=sender, receiver=request.user, is_read=False).update(is_read=True)

        unread_messages_count = Message.objects.filter(receiver=request.user, is_read=False).count()

        context = {
            'unread_messages_count': unread_messages_count,
            'users': users,
            'support_users': support_users,
            'regular_users': regular_users,
            'support_displayed': support_displayed,
            'user_displayed': user_displayed,
        }
        return render(request, 'chat/chat.html', context)

def message_view(request, sender, receiver):
    if request.method == "GET":
        current_user = request.user

        current_user = request.user
        receiver_user = get_object_or_404(User, id=receiver)

        messages = Message.objects.filter(
            (Q(sender=current_user, receiver=receiver_user) | Q(sender=receiver_user, receiver=current_user))
        )

        messages.filter(receiver=current_user, is_read=False).update(is_read=True)

        users = User.objects.exclude(username=current_user.username)

        for user in users:
            latest_message = Message.objects.filter(
                Q(sender=current_user, receiver=user) | Q(sender=user, receiver=current_user)
            ).last()
            user.latest_message = latest_message
            not_read_count = Message.objects.filter(sender=user, receiver=current_user, is_read=False).count()
            user.not_read_count = not_read_count

        unread_messages_count = Message.objects.filter(receiver=current_user, is_read=False).count()

        context = {
            'users': users,
            'receiver': receiver_user,
            'messages': messages,
            'unread_messages_count': unread_messages_count,
        }
        return render(request, "chat/messages.html", context)

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


# def chat_view(request):
#     if request.method == "GET":
#         latest_message = Message.objects.filter(
#             Q(sender=request.user) | Q(receiver=request.user)
#         ).last()
#         users = User.objects.exclude(username=request.user.username)
#         context = {
#             'latest_message': latest_message,
#             'users': users,
#         }
#         return render(request, 'chat/chat.html', context)

def chat_view(request):
    if request.method == "GET":
        users = User.objects.exclude(username=request.user.username)

        for user in users:
            latest_message = Message.objects.filter(
                Q(sender=request.user, receiver=user) | Q(sender=user, receiver=request.user)
            ).last()
            not_read_count = Message.objects.filter(sender=user, receiver=request.user, is_read=False).count()
            user.latest_message = latest_message
            user.not_read_count = not_read_count

        # Помечаем все сообщения от текущего пользователя к выбранным пользователем как прочитанные
        # при открытии чата с данным пользователем
        if 'user_id' in request.GET:
            user_id = request.GET.get('user_id')
            sender = get_object_or_404(User, id=user_id)
            Message.objects.filter(sender=sender, receiver=request.user, is_read=False).update(is_read=True)

        unread_messages_count = Message.objects.filter(receiver=request.user, is_read=False).count()

        context = {
            'unread_messages_count': unread_messages_count,
            'users': users,
        }
        return render(request, 'chat/chat.html', context)


def message_view(request, sender, receiver):
    if request.method == "GET":
        current_user = request.user

        users = User.objects.exclude(username=current_user.username)
        receiver_user = User.objects.get(id=receiver)
        messages = Message.objects.filter(
            (Q(sender=current_user, receiver=receiver_user) | Q(sender=receiver_user, receiver=current_user))
        )

        last_messages = []
        receivers = User.objects.exclude(id=current_user.id)
        for receiver in receivers:
            last_message = Message.objects.filter(
                (Q(sender=current_user, receiver=receiver) | Q(sender=receiver, receiver=current_user))
            ).order_by('-timestamp').first()
            last_messages.append(last_message)

        context = {
            'users': users,
            'receiver': receiver_user,
            'messages': messages,
            'last_messages': last_messages,
        }
        return render(request, "chat/messages.html", context)

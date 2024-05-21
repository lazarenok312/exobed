from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from .forms import LoginForm, UserRegistrationForm, ProfileEditForm
from django.contrib import messages
from django.shortcuts import render, redirect
import random
import string
from .models import RegistrationCode


def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            user_form.save()
            messages.success(request, 'Регистрация прошла успешно.')
            return redirect('login')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        user_form = UserRegistrationForm()
    return render(request, 'account/register.html', {'user_form': user_form})


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(username=cd['username'], password=cd['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponse('Authenticated successfully')
                else:
                    return HttpResponse('Disabled account')
            else:
                return HttpResponse('Invalid login')
    else:
        form = LoginForm()
    return render(request, 'registration/login.html', {'form': form})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('password_change_done')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'registration/password_change_form.html', {'form': form})


@login_required
def edit(request, slug):
    if request.method == 'POST':
        profile_form = ProfileEditForm(instance=request.user.profile, data=request.POST, files=request.FILES)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Профиль обновлен!')
            return redirect('profiles:profile_detail', slug=request.user.profile.slug)
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        profile_form = ProfileEditForm(instance=request.user.profile)

    return render(request, 'profile/profile_edit.html', {'profile_form': profile_form})


def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))


def generate_code_view(request):
    if request.method == 'POST':
        code = generate_code()
        max_usages = int(request.POST.get('max_usages', 1))
        new_code = RegistrationCode.objects.create(code=code, max_usages=max_usages)
        messages.success(request,
                         f'Сгенерированный код: {new_code.code}, Максимальное количество использований: {new_code.max_usages}')
        return redirect('generate_code')

    codes = RegistrationCode.objects.all()
    return render(request, 'account/generate_code.html', {'codes': codes})

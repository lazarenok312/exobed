from django import forms
from django.contrib.auth.models import User
from .models import Profile, RegistrationCode


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput)
    code = forms.CharField(label='Registration Code', required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'email')

    def clean_code(self):
        code = self.cleaned_data['code']
        try:
            registration_code = RegistrationCode.objects.get(code=code)
        except RegistrationCode.DoesNotExist:
            raise forms.ValidationError('Неверный код регистрации.')

        if registration_code.usage_count >= registration_code.max_usages:
            raise forms.ValidationError('Код регистрации уже использован максимальное количество раз.')

        return code

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            registration_code = RegistrationCode.objects.get(code=self.cleaned_data['code'])
            registration_code.usage_count += 1
            registration_code.save()
        return user

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Пользователь с таким логином уже существует.')
        return username

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Пароли не совпадают.')
        return cd['password2']


class ProfileEditForm(forms.ModelForm):
    phone_number = forms.CharField(max_length=15, required=False)

    class Meta:
        model = Profile
        fields = ('name', 'surnames', 'phone_number', 'email', 'photo')

    def save(self, commit=True):
        profile = super().save(commit=False)
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            profile.work_phone = phone_number
        if commit:
            profile.save()
        return profile

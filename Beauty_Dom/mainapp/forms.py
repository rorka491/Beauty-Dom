from django import forms
from .models import *
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import UserCreationForm
import uuid
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['notes', 'rating']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Ваш комментарий'}),
            'rating': forms.RadioSelect( attrs={'class': 'form-control'},),
        }


class CustomerSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Обязательно введите действующий адрес электронной почты.", )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'first_name', 'last_name', ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Установка плейсхолдеров для всех полей
        self.fields['username'].widget.attrs['placeholder'] = 'Имя пользователя'
        self.fields['email'].widget.attrs['placeholder'] = 'Ваша почта'
        self.fields['password1'].widget.attrs['placeholder'] = 'Пароль'
        self.fields['password2'].widget.attrs['placeholder'] = 'Подтвердите пароль'
        self.fields['first_name'].widget.attrs['placeholder'] = 'Введите ваше имя'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Введите вашу фaмилию'
        
        # Установить пустые метки
        for field in self.fields.values():
            field.help_text = ''
            field.label = ''

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError("Этот ник уже занят.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Этот адрес электронной почты уже используется.")
        return email
    
class CustomerLoginForm(AuthenticationForm):
        
    username = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Имя пользователя'}),
        label=''
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Пароль'}),
        label=''
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if username:
            # Удаляем лишние пробелы в начале и конце строки
            cleaned_data["username"] = username.strip()

        if password:
            # Удаляем лишние пробелы в начале и конце строки
            cleaned_data["password"] = password.strip()

        return cleaned_data


# """Многоступенчатая форма"""

class DateForm(forms.Form):
    date = forms.DateField(label='', error_messages={'required': ' Выберите день приема'},
        widget=forms.DateInput(
            attrs={
                'type': 'text',
                'id': 'datepicker',
                'placeholder': 'Выберите дату'
            }
        )
    )

class StartTimeForm(forms.Form):
    start_time = forms.ChoiceField(
        label='', 
        choices=[],
        widget=forms.RadioSelect(
            attrs={'class': 'radio-box'}
        )
    )
    
    def __init__(self, *args, choices, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_time'].choices = choices


class RecoverPasswordFormStep1(forms.Form):

    email = forms.EmailField(
        widget=forms.TextInput(attrs={'placeholder': 'Введите ваш email'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        
        if email:
            cleaned_data['email'] = email.strip()

class RecoverPasswordFormStep2(forms.Form):

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Введите новый пароль'}),
        max_length=128,
        label=''
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Повторите новый пароль'}),
        max_length=128,
        label=''
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2:
            cleaned_data['password1'] = password1.strip()
            cleaned_data['password2'] = password2.strip()


class VideoForm(forms.ModelForm):

    class Meta:
        model = VideoFile
        fields = '__all__'


class CommentForm(forms.ModelForm):

    class Meta:
        model = BlogPostComment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Напишите ваш комментарий',
                'rows': 3,
                'id': 'comment',
            }),
        }
        labels = {
            'text': ''
        }








    

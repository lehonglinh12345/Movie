from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User

class LoginForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
class AvatarForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['avatar']
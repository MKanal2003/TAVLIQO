from django import forms
from django.contrib.auth import authenticate
from .models import User

class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'your@email.com',
            'class': 'w-full px-4 py-3 border border-[#E7E7E0] rounded-xl text-sm focus:border-[#0BA6A0] focus:ring-2 focus:ring-[#0BA6A0]/20 outline-none transition-all'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Your password',
            'class': 'w-full px-4 py-3 border border-[#E7E7E0] rounded-xl text-sm focus:border-[#0BA6A0] focus:ring-2 focus:ring-[#0BA6A0]/20 outline-none transition-all'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            try:
                user = User.objects.get(email=email)
                self.user = authenticate(username=user.username, password=password)
                if self.user is None:
                    raise forms.ValidationError('Invalid email or password.')
            except User.DoesNotExist:
                raise forms.ValidationError('Invalid email or password.')

        return cleaned_data

    def get_user(self):
        return getattr(self, 'user', None)
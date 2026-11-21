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


class AdminCreateRestaurantForm(forms.Form):
    """
    Super Admin creates a Restaurant Admin user + Restaurant in one atomic step.
    """
    # Owner (User) fields
    owner_email = forms.EmailField(
        label="Owner email",
        widget=forms.EmailInput(attrs={
            'placeholder': 'owner@example.com',
            'class': 'w-full px-4 py-3 border border-[#E7E7E0] rounded-xl text-sm focus:border-[#0BA6A0] focus:ring-2 focus:ring-[#0BA6A0]/20 outline-none transition-all'
        })
    )
    owner_phone = forms.CharField(
        max_length=20, required=False, label="Owner phone",
        widget=forms.TextInput(attrs={
            'placeholder': '+91 …',
            'class': 'w-full px-4 py-3 border border-[#E7E7E0] rounded-xl text-sm focus:border-[#0BA6A0] focus:ring-2 focus:ring-[#0BA6A0]/20 outline-none transition-all'
        })
    )
    password = forms.CharField(
        label="Temporary password", min_length=8,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Minimum 8 characters',
            'class': 'w-full px-4 py-3 border border-[#E7E7E0] rounded-xl text-sm focus:border-[#0BA6A0] focus:ring-2 focus:ring-[#0BA6A0]/20 outline-none transition-all'
        })
    )

    # Restaurant fields
    restaurant_name = forms.CharField(
        max_length=255, label="Restaurant name",
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. Subedar Family Restaurant',
            'class': 'w-full px-4 py-3 border border-[#E7E7E0] rounded-xl text-sm focus:border-[#0BA6A0] focus:ring-2 focus:ring-[#0BA6A0]/20 outline-none transition-all'
        })
    )
    restaurant_phone = forms.CharField(
        max_length=20, required=False, label="Restaurant phone",
        widget=forms.TextInput(attrs={
            'placeholder': '+91 …',
            'class': 'w-full px-4 py-3 border border-[#E7E7E0] rounded-xl text-sm focus:border-[#0BA6A0] focus:ring-2 focus:ring-[#0BA6A0]/20 outline-none transition-all'
        })
    )
    address = forms.CharField(
        label="Restaurant address",
        widget=forms.Textarea(attrs={
            'rows': 3, 'placeholder': 'Full address',
            'class': 'w-full px-4 py-3 border border-[#E7E7E0] rounded-xl text-sm focus:border-[#0BA6A0] focus:ring-2 focus:ring-[#0BA6A0]/20 outline-none transition-all resize-none'
        })
    )
    description = forms.CharField(
        required=False, label="Short description (optional)",
        widget=forms.Textarea(attrs={
            'rows': 2, 'placeholder': 'Cuisine, specialities, etc.',
            'class': 'w-full px-4 py-3 border border-[#E7E7E0] rounded-xl text-sm focus:border-[#0BA6A0] focus:ring-2 focus:ring-[#0BA6A0]/20 outline-none transition-all resize-none'
        })
    )

    def clean_owner_email(self):
        email = self.cleaned_data['owner_email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email
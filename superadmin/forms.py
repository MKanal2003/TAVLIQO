from django import forms
from restaurants.models import Restaurant

class SuperAdminRestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = [
            'is_active', 
            'is_tax_enabled', 
            'cgst_percentage', 
            'sgst_percentage',
            'is_online_payment_enabled',
            'razorpay_key_id',
            'razorpay_key_secret'
        ]
        widgets = {
            'cgst_percentage': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'w-full px-4 py-3 border border-[#E7E7E0] rounded-xl focus:border-[#0BA6A0] outline-none'}),
            'sgst_percentage': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'w-full px-4 py-3 border border-[#E7E7E0] rounded-xl focus:border-[#0BA6A0] outline-none'}),
            'razorpay_key_id': forms.TextInput(attrs={'placeholder': 'rzp_test_...', 'class': 'w-full px-4 py-3 border border-[#E7E7E0] rounded-xl focus:border-[#0BA6A0] outline-none'}),
            'razorpay_key_secret': forms.PasswordInput(attrs={'placeholder': '••••••••••••', 'class': 'w-full px-4 py-3 border border-[#E7E7E0] rounded-xl focus:border-[#0BA6A0] outline-none'}),
        }
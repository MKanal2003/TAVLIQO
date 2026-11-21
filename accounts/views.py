from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib import messages
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit
from .forms import LoginForm
from .models import StaffUser
from restaurants.models import Restaurant

@ratelimit(key='ip', rate='10/m', block=True)
def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:login_redirect')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.email}!")
            return redirect('core:login_redirect')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})

@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "You've been logged out successfully.")
    return redirect('core:landing')

@ratelimit(key='ip', rate='5/m', block=True)
def staff_login_view(request, slug):
    restaurant = get_object_or_404(Restaurant, slug=slug)
    
    if request.method == 'POST':
        pin = request.POST.get('pin', '').strip()
        staff = StaffUser.objects.filter(restaurant=restaurant, pin=pin, is_active=True).first()
        
        if staff:
            request.session['staff_id'] = staff.id
            request.session['staff_restaurant_id'] = restaurant.id
            return redirect('restaurants:staff_dashboard')
        else:
            messages.error(request, "Invalid PIN. Please try again.")
            
    return render(request, 'accounts/staff_login.html', {'restaurant': restaurant})
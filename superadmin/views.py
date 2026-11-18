from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from restaurants.models import Restaurant, MenuItem, generate_qr_token
from accounts.models import User
from accounts.forms import AdminCreateRestaurantForm
from .decorators import superadmin_required
from .forms import SuperAdminRestaurantForm


@superadmin_required
def dashboard(request):
    total_restaurants = Restaurant.objects.count()
    active_restaurants = Restaurant.objects.filter(is_active=True).count()
    inactive_restaurants = total_restaurants - active_restaurants
    total_items = MenuItem.objects.count()
    total_users = User.objects.filter(role=User.ROLE_RESTAURANT_ADMIN).count()

    recent_restaurants = (
        Restaurant.objects.select_related('owner').order_by('-created_at')[:8]
    )

    context = {
        'total_restaurants': total_restaurants,
        'active_restaurants': active_restaurants,
        'inactive_restaurants': inactive_restaurants,
        'total_items': total_items,
        'total_users': total_users,
        'recent_restaurants': recent_restaurants,
    }
    return render(request, 'superadmin/dashboard.html', context)


@superadmin_required
def restaurants_list(request):
    query = request.GET.get('q', '')
    restaurants = Restaurant.objects.select_related('owner').all()

    if query:
        restaurants = restaurants.filter(
            Q(name__icontains=query) | Q(owner__email__icontains=query)
        )

    total_count = Restaurant.objects.count()
    active_count = Restaurant.objects.filter(is_active=True).count()
    inactive_count = total_count - active_count

    return render(request, 'superadmin/restaurants.html', {
        'restaurants': restaurants,
        'query': query,
        'total_count': total_count,
        'active_count': active_count,
        'inactive_count': inactive_count,
    })


@superadmin_required
def create_restaurant_admin(request):
    if request.method == 'POST':
        form = AdminCreateRestaurantForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                with transaction.atomic(using='default'):
                    user = User.objects.create_user(
                        username=data['owner_email'],
                        email=data['owner_email'],
                        password=data['password'],
                        role=User.ROLE_RESTAURANT_ADMIN,
                        phone=data.get('owner_phone', ''),
                    )
                    restaurant = Restaurant.objects.create(
                        owner=user,
                        name=data['restaurant_name'],
                        email=data['owner_email'],
                        phone=data.get('restaurant_phone', ''),
                        address=data['address'],
                        description=data.get('description', ''),
                    )
            except Exception as exc:
                messages.error(request, f"Could not create restaurant: {exc}")
            else:
                messages.success(
                    request,
                    f'Restaurant "{restaurant.name}" created. '
                    f'Share credentials with {data["owner_email"]} over a secure channel.'
                )
                return redirect('superadmin:restaurants')
    else:
        form = AdminCreateRestaurantForm()

    return render(request, 'superadmin/create_restaurant_admin.html', {'form': form})


@superadmin_required
def edit_restaurant(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    
    if request.method == 'POST':
        form = SuperAdminRestaurantForm(request.POST, instance=restaurant)
        if form.is_valid():
            form.save()
            messages.success(request, f"Settings updated for {restaurant.name}.")
            return redirect('superadmin:restaurants')
    else:
        form = SuperAdminRestaurantForm(instance=restaurant)
        
    return render(request, 'superadmin/edit_restaurant.html', {
        'restaurant': restaurant, 
        'form': form
    })


@superadmin_required
@require_POST
def toggle_restaurant(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    restaurant.is_active = not restaurant.is_active
    restaurant.save(update_fields=['is_active', 'updated_at'])
    return JsonResponse({'is_active': restaurant.is_active})


@superadmin_required
@require_POST
def regenerate_restaurant_qr(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    restaurant.qr_token = generate_qr_token()
    restaurant.save(update_fields=['qr_token'])
    messages.success(
        request,
        f'QR token regenerated for "{restaurant.name}". '
        f'All previously printed QR codes no longer work.'
    )
    return redirect('superadmin:restaurants')
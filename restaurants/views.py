from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
import datetime

from .models import Restaurant, Category, MenuItem, generate_qr_token
from .forms import RestaurantProfileForm, CategoryForm, MenuItemForm
from .decorators import restaurant_admin_required
from .utils import generate_qr_code
from accounts.models import StaffUser


@restaurant_admin_required
def dashboard(request):
    restaurant = request.user.restaurant
    from orders.models import Order
    pending_count = Order.objects.filter(
        restaurant_id=restaurant.id, status='PENDING_ACCEPTANCE'
    ).count()
    context = {
        'total_items': restaurant.total_items,
        'available_items': restaurant.available_items_count,
        'sold_out_items': restaurant.sold_out_count,
        'total_categories': restaurant.categories.count(),
        'recent_items': restaurant.menu_items.select_related('category')[:8],
        'pending_orders_count': pending_count,
    }
    return render(request, 'restaurants/dashboard.html', context)


@restaurant_admin_required
def profile(request):
    restaurant = request.user.restaurant
    if request.method == 'POST':
        form = RestaurantProfileForm(request.POST, request.FILES, instance=restaurant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('restaurants:profile')
    else:
        form = RestaurantProfileForm(instance=restaurant)
    return render(request, 'restaurants/profile.html', {
        'form': form, 'restaurant': restaurant,
    })


@restaurant_admin_required
def categories(request):
    restaurant = request.user.restaurant
    editing = None
    edit_id = request.GET.get('edit')
    if edit_id:
        editing = get_object_or_404(Category, pk=edit_id, restaurant=restaurant)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=editing) if editing else CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.restaurant = restaurant
            category.save()
            messages.success(request, f'Category "{category.name}" saved.')
            return redirect('restaurants:categories')
    else:
        form = CategoryForm(instance=editing) if editing else CategoryForm()
    categories_list = restaurant.categories.prefetch_related('items').all()
    return render(request, 'restaurants/categories.html', {
        'categories': categories_list, 'form': form, 'editing': editing,
    })


@restaurant_admin_required
def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk, restaurant=request.user.restaurant)
    return redirect(f"{request.path.replace('/edit/', '')}?edit={pk}")


@restaurant_admin_required
@require_POST
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk, restaurant=request.user.restaurant)
    name = category.name
    category.delete()
    messages.success(request, f'Category "{name}" deleted.')
    return redirect('restaurants:categories')


@restaurant_admin_required
def menu_items(request):
    restaurant = request.user.restaurant
    category_filter = request.GET.get('category')
    items = restaurant.menu_items.select_related('category')
    if category_filter:
        items = items.filter(category_id=category_filter)
    categories_list = restaurant.categories.all()
    return render(request, 'restaurants/menu_items.html', {
        'items': items,
        'categories': categories_list,
        'selected_category': int(category_filter) if category_filter else None,
    })


@restaurant_admin_required
def add_item(request):
    restaurant = request.user.restaurant
    if request.method == 'POST':
        form = MenuItemForm(restaurant, request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.restaurant = restaurant
            item.save()
            messages.success(request, f'"{item.name}" added.')
            return redirect('restaurants:menu_items')
    else:
        form = MenuItemForm(restaurant)
    return render(request, 'restaurants/add_item.html', {'form': form})


@restaurant_admin_required
def edit_item(request, pk):
    restaurant = request.user.restaurant
    item = get_object_or_404(MenuItem, pk=pk, restaurant=restaurant)
    if request.method == 'POST':
        form = MenuItemForm(restaurant, request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{item.name}" updated.')
            return redirect('restaurants:menu_items')
    else:
        form = MenuItemForm(restaurant, instance=item)
    return render(request, 'restaurants/edit_item.html', {'form': form, 'item': item})


@restaurant_admin_required
@require_POST
def delete_item(request, pk):
    item = get_object_or_404(MenuItem, pk=pk, restaurant=request.user.restaurant)
    name = item.name
    item.delete()
    messages.success(request, f'"{name}" deleted.')
    return redirect('restaurants:menu_items')


@restaurant_admin_required
@require_POST
def toggle_availability(request, pk):
    try:
        item = get_object_or_404(MenuItem, pk=pk, restaurant=request.user.restaurant)
        item.is_available = not item.is_available
        item.save()
        return JsonResponse({
            'status': 'ok',
            'is_available': item.is_available,
            'item_id': item.pk,
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@restaurant_admin_required
def qr_code_view(request):
    restaurant = request.user.restaurant
    qr_path = generate_qr_code(restaurant, request)
    menu_url = request.build_absolute_uri(restaurant.get_menu_url())
    return render(request, 'restaurants/qr_code.html', {
        'qr_path': qr_path, 'menu_url': menu_url, 'restaurant': restaurant,
    })


@restaurant_admin_required
@require_POST
def regenerate_qr(request):
    restaurant = request.user.restaurant
    restaurant.qr_token = generate_qr_token()
    restaurant.save(update_fields=['qr_token'])
    messages.success(request, 'QR code regenerated. Old QR codes no longer work.')
    return redirect('restaurants:qr_code_view')


@restaurant_admin_required
def analytics(request):
    restaurant = request.user.restaurant
    from orders.models import Order

    now = timezone.now()
    today = now.date()
    this_month = today.replace(day=1)
    this_year = today.replace(month=1, day=1)

    paid_orders = Order.objects.filter(restaurant_id=restaurant.id, status='PAID')

    today_sales = paid_orders.filter(updated_at__date=today).aggregate(Sum('total'))['total__sum'] or 0
    month_sales = paid_orders.filter(updated_at__date__gte=this_month).aggregate(Sum('total'))['total__sum'] or 0
    year_sales = paid_orders.filter(updated_at__date__gte=this_year).aggregate(Sum('total'))['total__sum'] or 0
    
    today_cash = paid_orders.filter(updated_at__date=today, payment_intent='CASH').aggregate(Sum('total'))['total__sum'] or 0
    today_online = paid_orders.filter(updated_at__date=today, payment_intent='ONLINE').aggregate(Sum('total'))['total__sum'] or 0

    total_orders_count = Order.objects.filter(restaurant_id=restaurant.id).count()
    paid_orders_count = paid_orders.count()
    
    seven_days_ago = today - datetime.timedelta(days=6)
    daily_sales = (
        paid_orders.filter(updated_at__date__gte=seven_days_ago)
        .annotate(date=TruncDate('updated_at'))
        .values('date')
        .annotate(total=Sum('total'))
        .order_by('date')
    )
    
    sales_dict = {item['date'].strftime('%Y-%m-%d'): float(item['total']) for item in daily_sales}
    chart_labels = []
    chart_data = []
    for i in range(7):
        d = seven_days_ago + datetime.timedelta(days=i)
        ds = d.strftime('%Y-%m-%d')
        chart_labels.append(d.strftime('%a')) 
        chart_data.append(sales_dict.get(ds, 0))

    daily_tracking_qs = (
        paid_orders.filter(updated_at__date__gte=this_month)
        .annotate(date=TruncDate('updated_at'))
        .values('date')
        .annotate(revenue=Sum('total'), orders=Count('id'))
        .order_by('-date')
    )
    
    daily_tracking = []
    for item in daily_tracking_qs:
        daily_tracking.append({
            'date': item['date'].strftime('%d %b %Y'),
            'orders': item['orders'],
            'revenue': item['revenue']
        })

    context = {
        'today_sales': today_sales,
        'month_sales': month_sales,
        'year_sales': year_sales,
        'today_cash': today_cash,
        'today_online': today_online,
        'total_orders': total_orders_count,
        'paid_orders': paid_orders_count,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'daily_tracking': daily_tracking,
    }
    return render(request, 'restaurants/analytics.html', context)


@restaurant_admin_required
def manage_staff(request):
    restaurant = request.user.restaurant
    
    if request.method == 'POST':
        name = request.POST.get('name')
        pin = request.POST.get('pin')
        if name and pin and len(pin) == 4:
            StaffUser.objects.create(restaurant=restaurant, name=name, pin=pin)
            messages.success(request, f"Staff account created for {name}.")
            return redirect('restaurants:manage_staff')
        else:
            messages.error(request, "Please provide a name and a 4-digit PIN.")
            
    staff_members = StaffUser.objects.filter(restaurant=restaurant).order_by('-created_at')
    staff_login_url = request.build_absolute_uri(f'/accounts/staff-login/{restaurant.slug}/')
    
    return render(request, 'restaurants/manage_staff.html', {
        'staff_members': staff_members,
        'staff_login_url': staff_login_url
    })
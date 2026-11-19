from decimal import Decimal
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Count
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.csrf import ensure_csrf_cookie

from restaurants.models import Restaurant, MenuItem
from restaurants.decorators import restaurant_admin_required
from accounts.decorators import staff_required
from .models import (
    Customer, Order, OrderItem, OrderStatusEvent, ConsentLog,
    ALLOWED_TRANSITIONS, NEXT_STATE,
)

def _cart_key(restaurant_id):
    return f'cart_{restaurant_id}'

def _get_cart(request, restaurant_id):
    return request.session.get(_cart_key(restaurant_id), {})

def _save_cart(request, restaurant_id, cart):
    request.session[_cart_key(restaurant_id)] = cart
    request.session.modified = True

def _resolve_cart(restaurant, cart):
    items = []
    subtotal = Decimal('0')
    for item_id_str, qty in cart.items():
        try:
            mi = MenuItem.objects.get(pk=int(item_id_str), restaurant=restaurant)
            if not mi.is_available:
                continue
        except MenuItem.DoesNotExist:
            continue
        line = mi.price * qty
        subtotal += line
        items.append({'item': mi, 'qty': qty, 'line_total': line})
    return items, subtotal

def cart_add(request, token, item_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    restaurant = get_object_or_404(Restaurant, qr_token=token, is_active=True)
    item = get_object_or_404(MenuItem, pk=item_id, restaurant=restaurant, is_available=True)
    cart = _get_cart(request, restaurant.id)
    key = str(item.id)
    cart[key] = cart.get(key, 0) + 1
    _save_cart(request, restaurant.id, cart)
    return JsonResponse({'ok': True, 'count': sum(cart.values())})

def cart_remove(request, token, item_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    restaurant = get_object_or_404(Restaurant, qr_token=token, is_active=True)
    cart = _get_cart(request, restaurant.id)
    key = str(item_id)
    if key in cart:
        if cart[key] > 1:
            cart[key] -= 1
        else:
            del cart[key]
    _save_cart(request, restaurant.id, cart)
    return JsonResponse({'ok': True, 'count': sum(cart.values())})

@ensure_csrf_cookie
def cart_view(request, token):
    restaurant = get_object_or_404(Restaurant, qr_token=token, is_active=True)
    cart = _get_cart(request, restaurant.id)
    items, subtotal = _resolve_cart(restaurant, cart)
    return render(request, 'menu/cart.html', {
        'restaurant': restaurant,
        'items': items,
        'subtotal': subtotal,
    })

@ensure_csrf_cookie
def checkout(request, token):
    restaurant = get_object_or_404(Restaurant, qr_token=token, is_active=True)
    cart = _get_cart(request, restaurant.id)
    if not cart:
        messages.info(request, "Your basket is empty.")
        return redirect('menu_by_token', token=token)

    items, subtotal = _resolve_cart(restaurant, cart)
    if not items:
        messages.warning(request, "All items in your basket are unavailable.")
        return redirect('menu_by_token', token=token)

    tax_amount = Decimal('0')
    cgst_amount = Decimal('0')
    sgst_amount = Decimal('0')
    
    if restaurant.is_tax_enabled:
        cgst_amount = (subtotal * restaurant.cgst_percentage) / Decimal('100')
        sgst_amount = (subtotal * restaurant.sgst_percentage) / Decimal('100')
        tax_amount = cgst_amount + sgst_amount
    
    total = subtotal + tax_amount

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        table_label = request.POST.get('table_label', '').strip()
        notes = request.POST.get('notes', '').strip()
        payment_intent = request.POST.get('payment_intent', 'CASH')
        terms_accepted = request.POST.get('terms_accepted') == 'on'

        errors = []
        if not name: errors.append("Please enter your name.")
        if not table_label: errors.append("Please enter your table number / takeaway.")
        if not terms_accepted: errors.append("You must accept the terms and conditions.")
        if payment_intent == 'ONLINE' and not restaurant.is_online_payment_enabled:
            errors.append("Online payment is not available.")
        if payment_intent not in ('CASH', 'ONLINE'):
            errors.append("Please choose a payment mode.")

        if errors:
            for e in errors: messages.error(request, e)
            return render(request, 'menu/checkout.html', {
                'restaurant': restaurant, 'items': items, 'subtotal': subtotal, 
                'tax_amount': tax_amount, 'cgst_amount': cgst_amount, 'sgst_amount': sgst_amount, 'total': total,
            })

        with transaction.atomic(using='tenant'):
            customer = Customer.objects.create(restaurant_id=restaurant.id, name=name, phone=phone)
            order = Order.objects.create(
                restaurant_id=restaurant.id,
                customer=customer,
                table_label=table_label,
                payment_intent=payment_intent,
                subtotal=subtotal,
                tax_amount=tax_amount,
                total=total,
                notes=notes,
                staff_name="Customer",
            )
            for row in items:
                OrderItem.objects.create(
                    order=order, menu_item_id=row['item'].id, 
                    name_snapshot=row['item'].name, price_snapshot=row['item'].price, qty=row['qty']
                )
            OrderStatusEvent.objects.create(
                order=order, from_status='', to_status='PENDING_ACCEPTANCE',
                actor_type='customer', actor_id='',
            )
            ConsentLog.objects.create(order=order, terms_version='v1.0')

        _save_cart(request, restaurant.id, {})
        return redirect('orders:order_status', token=token, order_token=order.public_token)

    return render(request, 'menu/checkout.html', {
        'restaurant': restaurant, 'items': items, 'subtotal': subtotal, 
        'tax_amount': tax_amount, 'cgst_amount': cgst_amount, 'sgst_amount': sgst_amount, 'total': total,
    })

def order_status(request, token, order_token):
    restaurant = get_object_or_404(Restaurant, qr_token=token)
    order = get_object_or_404(Order.objects.prefetch_related('items'), public_token=order_token, restaurant_id=restaurant.id)
    return render(request, 'menu/order_status.html', {'restaurant': restaurant, 'order': order})

# API for AJAX Polling
def check_order_status(request, token, order_token):
    restaurant = get_object_or_404(Restaurant, qr_token=token)
    order = get_object_or_404(Order, public_token=order_token, restaurant_id=restaurant.id)
    return JsonResponse({'status': order.status, 'display': order.get_status_display()})

def call_waiter(request, token, order_token):
    # Placeholder for actual notification logic (WhatsApp/SMS/WebSocket)
    # For now, it just logs to the console and returns success
    print(f"!!! WAITER CALLED for Order {order_token} !!!")
    return JsonResponse({'ok': True})

def _transition(order, to_status, actor_type='staff', actor_id='', reason=''):
    from_status = order.status
    if to_status not in ALLOWED_TRANSITIONS.get(from_status, set()):
        raise ValueError(f"Illegal transition {from_status} → {to_status}")
    order.status = to_status
    if reason: order.rejection_reason = reason
    order.save()
    OrderStatusEvent.objects.create(order=order, from_status=from_status, to_status=to_status, actor_type=actor_type, actor_id=str(actor_id), reason=reason)

@restaurant_admin_required
def admin_orders(request):
    restaurant = request.user.restaurant
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    # Auto-expire pending orders
    expired_orders = Order.objects.filter(restaurant_id=restaurant.id, status='PENDING_ACCEPTANCE', created_at__lt=timezone.now() - timedelta(minutes=15))
    for order in expired_orders:
        _transition(order, 'EXPIRED', actor_type='system')

    orders = Order.objects.filter(restaurant_id=restaurant.id, created_at__gte=seven_days_ago).exclude(status__in=['CLOSED', 'REJECTED', 'CANCELLED', 'EXPIRED']).prefetch_related('items').order_by('created_at')
    
    # Split into Kanban columns
    new_orders = [o for o in orders if o.status == 'PENDING_ACCEPTANCE']
    preparing_orders = [o for o in orders if o.status in ['CONFIRMED', 'PREPARING']]
    ready_orders = [o for o in orders if o.status == 'SERVED']

    return render(request, 'restaurants/orders.html', {
        'new_orders': new_orders,
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders,
        'now': timezone.now()
    })

@restaurant_admin_required
def admin_order_accept(request, pk):
    if request.method != 'POST': return JsonResponse({'error': 'POST required'}, status=405)
    order = get_object_or_404(Order, pk=pk, restaurant_id=request.user.restaurant.id)
    try:
        _transition(order, 'CONFIRMED', actor_id=request.user.id)
        messages.success(request, f'Order #{order.id} accepted.')
    except ValueError as e: messages.error(request, str(e))
    return redirect('restaurants:orders')

@restaurant_admin_required
def admin_order_reject(request, pk):
    if request.method != 'POST': return JsonResponse({'error': 'POST required'}, status=405)
    order = get_object_or_404(Order, pk=pk, restaurant_id=request.user.restaurant.id)
    reason = request.POST.get('reason', '').strip() or 'No reason provided'
    try:
        _transition(order, 'REJECTED', actor_id=request.user.id, reason=reason)
        messages.success(request, f'Order #{order.id} rejected.')
    except ValueError as e: messages.error(request, str(e))
    return redirect('restaurants:orders')

@restaurant_admin_required
def admin_order_advance(request, pk):
    if request.method != 'POST': return JsonResponse({'error': 'POST required'}, status=405)
    order = get_object_or_404(Order, pk=pk, restaurant_id=request.user.restaurant.id)
    to_status = NEXT_STATE.get(order.status)
    if not to_status:
        messages.error(request, f'Cannot advance order #{order.id} from {order.status}.')
        return redirect('restaurants:orders')
    try:
        _transition(order, to_status, actor_id=request.user.id)
        messages.success(request, f'Order #{order.id} → {to_status}.')
    except ValueError as e: messages.error(request, str(e))
    return redirect('restaurants:orders')

@restaurant_admin_required
def order_receipt(request, pk):
    restaurant = request.user.restaurant
    order = get_object_or_404(Order.objects.prefetch_related('items'), pk=pk, restaurant_id=restaurant.id)
    return render(request, 'restaurants/receipt.html', {'order': order, 'restaurant': restaurant})

@staff_required
def staff_dashboard(request):
    restaurant = request.staff.restaurant
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    expired_orders = Order.objects.filter(restaurant_id=restaurant.id, status='PENDING_ACCEPTANCE', created_at__lt=timezone.now() - timedelta(minutes=15))
    for order in expired_orders:
        _transition(order, 'EXPIRED', actor_type='system')

    orders = Order.objects.filter(restaurant_id=restaurant.id, created_at__gte=seven_days_ago).exclude(status__in=['CLOSED', 'REJECTED', 'CANCELLED', 'EXPIRED']).prefetch_related('items').order_by('created_at')
    
    new_orders = [o for o in orders if o.status == 'PENDING_ACCEPTANCE']
    preparing_orders = [o for o in orders if o.status in ['CONFIRMED', 'PREPARING']]
    ready_orders = [o for o in orders if o.status == 'SERVED']

    return render(request, 'restaurants/staff_dashboard.html', {
        'new_orders': new_orders,
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders,
        'now': timezone.now()
    })

@staff_required
def staff_create_order(request):
    restaurant = request.staff.restaurant
    menu_items = MenuItem.objects.filter(restaurant=restaurant, is_available=True)

    if request.method == 'POST':
        table_label = request.POST.get('table_label')
        payment_intent = request.POST.get('payment_intent', 'CASH')
        item_ids = request.POST.getlist('items')
        
        if not table_label or not item_ids:
            messages.error(request, "Please select a table and at least one item.")
            return redirect('restaurants:staff_order')

        cart_items = []
        for item_id in item_ids:
            item = get_object_or_404(MenuItem, pk=item_id, restaurant=restaurant)
            if not item.is_available: continue
            qty = int(request.POST.get(f'qty_{item_id}', 1))
            if qty <= 0: continue
            cart_items.append((item, qty))

        with transaction.atomic(using='tenant'):
            customer = Customer.objects.create(restaurant_id=restaurant.id, name="Staff Order", phone="")
            order = Order.objects.create(
                restaurant_id=restaurant.id, customer=customer, table_label=table_label,
                payment_intent=payment_intent, subtotal=0, tax_amount=0, total=0, status='CONFIRMED',
                staff_id=request.staff.id, staff_name=request.staff.name,
            )
            
            total = 0
            for item, qty in cart_items:
                total += item.price * qty
                OrderItem.objects.create(order=order, menu_item_id=item.id, name_snapshot=item.name, price_snapshot=item.price, qty=qty)
                
            tax_amount = Decimal('0')
            if restaurant.is_tax_enabled:
                tax_amount = (total * (restaurant.cgst_percentage + restaurant.sgst_percentage)) / Decimal('100')
            
            order.subtotal = total
            order.tax_amount = tax_amount
            order.total = total + tax_amount
            order.save()
            OrderStatusEvent.objects.create(order=order, from_status='', to_status='CONFIRMED', actor_type='staff', actor_id=str(request.staff.id))
            
        messages.success(request, f"Order #{order.id} sent to kitchen for {table_label}.")
        return redirect('restaurants:staff_dashboard')

    # Group by category for the UI
    categories = restaurant.categories.prefetch_related('items').all()
    return render(request, 'restaurants/staff_order.html', {'categories': categories, 'menu_items': menu_items})

@staff_required
def staff_advance_order(request, pk):
    if request.method != 'POST': return JsonResponse({'error': 'POST required'}, status=405)
    restaurant = request.staff.restaurant
    order = get_object_or_404(Order, pk=pk, restaurant_id=restaurant.id)
    to_status = NEXT_STATE.get(order.status)
    
    if not to_status:
        messages.error(request, f'Cannot advance order #{order.id}.')
        return redirect('restaurants:staff_dashboard')
    try:
        _transition(order, to_status, actor_type='staff', actor_id=request.staff.id)
        messages.success(request, f'{order.table_label} → {to_status}.')
    except ValueError as e: messages.error(request, str(e))
    return redirect('restaurants:staff_dashboard')

@staff_required
def staff_accept_order(request, pk):
    if request.method != 'POST': return JsonResponse({'error': 'POST required'}, status=405)
    restaurant = request.staff.restaurant
    order = get_object_or_404(Order, pk=pk, restaurant_id=restaurant.id)
    try:
        _transition(order, 'CONFIRMED', actor_type='staff', actor_id=request.staff.id)
        messages.success(request, f'Order #{order.id} accepted.')
    except ValueError as e: messages.error(request, str(e))
    return redirect('restaurants:staff_dashboard')

@staff_required
def staff_reject_order(request, pk):
    if request.method != 'POST': return JsonResponse({'error': 'POST required'}, status=405)
    restaurant = request.staff.restaurant
    order = get_object_or_404(Order, pk=pk, restaurant_id=restaurant.id)
    try:
        _transition(order, 'REJECTED', actor_type='staff', actor_id=request.staff.id, reason="Rejected by staff")
        messages.success(request, f'Order #{order.id} rejected.')
    except ValueError as e: messages.error(request, str(e))
    return redirect('restaurants:staff_dashboard')

@staff_required
def staff_order_receipt(request, pk):
    restaurant = request.staff.restaurant
    order = get_object_or_404(Order.objects.prefetch_related('items'), pk=pk, restaurant_id=restaurant.id)
    return render(request, 'restaurants/receipt.html', {'order': order, 'restaurant': restaurant})
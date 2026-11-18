from django.shortcuts import render, redirect
from django.http import Http404
from django.views.decorators.csrf import ensure_csrf_cookie
from restaurants.models import Restaurant


@ensure_csrf_cookie
def menu_viewer_by_token(request, token):
    try:
        restaurant = Restaurant.objects.prefetch_related('categories__items').get(qr_token=token)
    except Restaurant.DoesNotExist:
        raise Http404("Restaurant not found")
    return _render_menu(request, restaurant)


def menu_viewer(request, slug):
    try:
        restaurant = Restaurant.objects.get(slug=slug)
    except Restaurant.DoesNotExist:
        raise Http404("Restaurant not found")
    return redirect('menu_by_token', token=restaurant.qr_token, permanent=True)


def _render_menu(request, restaurant):
    if not restaurant.is_active:
        return render(request, 'menu/unavailable.html', {'restaurant': restaurant}, status=200)
    categories = restaurant.categories.prefetch_related('items').all()
    all_items = restaurant.menu_items.select_related('category').all()
    cart = request.session.get(f'cart_{restaurant.id}', {})
    return render(request, 'menu/viewer.html', {
        'restaurant': restaurant,
        'categories': categories,
        'all_items': all_items,
        'cart_count': sum(cart.values()) if cart else 0,
    })
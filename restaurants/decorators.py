from functools import wraps
from django.shortcuts import redirect, render
from django.contrib import messages


def restaurant_admin_required(view_func):
    """
    Restricts access to restaurant admin views only.
    Blocks access entirely when restaurant is deactivated.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')

        if request.user.is_superadmin():
            return redirect('superadmin:dashboard')

        if not hasattr(request.user, 'restaurant'):
            messages.error(request, "No restaurant profile found for your account.")
            return redirect('core:landing')

        if not request.user.restaurant.is_active:
            # Block — render deactivated page, no dashboard access
            return render(request, 'restaurants/deactivated.html', {
                'restaurant': request.user.restaurant,
            }, status=403)

        return view_func(request, *args, **kwargs)

    return wrapper
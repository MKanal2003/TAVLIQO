from functools import wraps
from django.shortcuts import redirect
from accounts.models import StaffUser

def staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        staff_id = request.session.get('staff_id')
        if not staff_id:
            return redirect('core:landing')
        try:
            request.staff = StaffUser.objects.get(id=staff_id, is_active=True)
        except StaffUser.DoesNotExist:
            request.session.pop('staff_id', None)
            return redirect('core:landing')
        return view_func(request, *args, **kwargs)
    return wrapper
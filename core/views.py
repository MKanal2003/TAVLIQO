from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

def landing(request):
    return render(request, 'core/landing.html')

@login_required
def login_redirect(request):
    user = request.user
    
    # 1. Super Admin
    if user.is_superadmin():
        return redirect('superadmin:dashboard')
    
    # 2. Restaurant Admin
    if user.is_restaurant_admin():
        if hasattr(user, 'restaurant'):
            return redirect('restaurants:dashboard')
        else:
            return redirect('superadmin:dashboard') 

    # 3. Fallback
    return redirect('core:landing')

def secret_portal(request):
    return render(request, 'core/portal.html')

def terms(request):
    return render(request, 'core/terms.html')

def privacy(request):
    return render(request, 'core/privacy.html')

def robots_txt(request):
    content = "User-agent: *\nDisallow: /dashboard/\nDisallow: /superadmin/\nDisallow: /portal/\n"
    return HttpResponse(content, content_type="text/plain")

# --- NEW: Missing Error Handlers causing the crash ---
def custom_404(request, exception):
    return render(request, '404.html', status=404)

def custom_500(request):
    return render(request, '500.html', status=500)
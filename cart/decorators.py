from functools import wraps
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def custom_login_required(view_func):
    """
    Custom login_required decorator that renders a login_required.html page
    if the user is not authenticated.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return render(request, 'login_required.html', status=403)  # 403 Forbidden
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

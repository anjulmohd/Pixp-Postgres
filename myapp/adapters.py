from allauth.account.adapter import DefaultAccountAdapter
from django.core.exceptions import PermissionDenied

class NoSignupAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return False  # Block manual signups

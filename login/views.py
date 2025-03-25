from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib import messages
from .models import OTPVerification
from django.core.mail import send_mail
from django.utils.timezone import now, timedelta
from django.utils.crypto import get_random_string
from django.utils import timezone
import uuid
import random
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import update_session_auth_hash
from django.utils.datastructures import MultiValueDictKeyError

User = get_user_model()
def login_view(request):
    if request.method == "POST":
        try:
            identifier = request.POST['identifier']  # Can be username or email
            password = request.POST['password']

            # Check if identifier is an email
            if '@' in identifier:
                try:
                    user_obj = User.objects.get(email=identifier)
                    username = user_obj.username  # Convert email to username
                except User.DoesNotExist:
                    messages.error(request, "Invalid email or password.")
                    return redirect('login')
            else:
                username = identifier  # Treat as username

            # Authenticate user
            user = authenticate(request, username=username, password=password)

            if user is not None:
                # Check if user is active (i.e., OTP verified)
                if not user.is_active:
                    messages.error(request, "Your account is not activated. Please verify your OTP.")
                    return redirect('login')

                # Check if the user is blocked
                if hasattr(user, 'is_blocked') and user.is_blocked:
                    messages.error(request, "Your account has been blocked by the admin.")
                    return redirect('login')

                # If authentication is successful, log the user in
                login(request, user)
                return redirect('home')

            else:
                messages.error(request, "Invalid username/email or password.")
                return redirect('login')

        except KeyError:
            messages.error(request, "Please fill in all required fields.")
            return redirect('login')

    return render(request, 'login.html')


def user_logout(request):

    logout(request)

    return redirect('home')  

def user_register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("register")
        else:
            # Create user and set as inactive until OTP verification
            user = User.objects.create_user(username=username, email=email, password=password)
            user.is_active = False
            user.save()

            otp = generate_otp()
            

            # Save OTP in the database (to be used for verification)
            OTPVerification.objects.create(user=user, otp=otp)

            # Send OTP email
            send_mail(
                'Your OTP for Account Verification',
                f'Your OTP is: {otp}',
                'webmaster@localhost',  # Use your email here
                [email],
                fail_silently=False,
            )

            messages.success(request, "Account created. Please enter the OTP to verify your account.")
            # After account creation, render OTP form in the same template
            return render(request, 'otp.html', {'show_otp_form': True, 'user': user})

    return render(request, 'login.html', {'show_otp_form': False})

def verify_otp(request):
    if request.method == 'POST':
        otp_entered = request.POST['otp']
        user = User.objects.get(id=request.POST['user_id'])

        try:
            otp_record = OTPVerification.objects.get(user=user)
            if otp_record.otp == otp_entered:
                # OTP is correct, activate user
                user.is_active = True
                user.save()
                otp_record.delete()  # Delete OTP after successful verification
                messages.success(request, "Your account has been verified successfully! Now Login Here ")
                return redirect('login')  # Redirect to login page
            else:
                messages.error(request, "Invalid OTP. Please try again.")
        except OTPVerification.DoesNotExist:
            messages.error(request, "OTP record not found.")
    
    return render(request, 'otp.html', {'show_otp_form': True})


def generate_otp():
    return get_random_string(length=6, allowed_chars='1234567890')

from datetime import timedelta

def resend_otp(request):
    username = request.POST.get('username')
    user = User.objects.filter(username=username).first()

    if user:
        otp_entry = OTPVerification.objects.filter(user=user).first()

        if otp_entry:
            # Calculate remaining time for the OTP
            remaining_time = max(0, (timezone.now() - otp_entry.created_at).total_seconds())
            if not otp_entry.is_expired():
                messages.error(request, "OTP has not expired yet.")
                return render(request, 'otp.html', {'user': user, 'show_otp_form': True, 'remaining_time': remaining_time})  # Stay on the OTP page

        # Generate a new OTP (e.g., random 6 digits)
        otp = generate_otp()
        otp_entry.otp = otp  # Update the OTP
        otp_entry.created_at = timezone.now()  # Reset the created_at to extend expiry
        otp_entry.save()

        # Send new OTP to the user via email
        send_mail(
            'Your OTP for Account Verification',
            f'Your new OTP is: {otp}',
            'webmaster@localhost',
            [user.email],
            fail_silently=False,
        )

        messages.success(request, "A new OTP has been sent to your email.")
        remaining_time = 30  # Set the initial time for the new OTP (e.g., 30 seconds)
        return render(request, 'otp.html', {'user': user, 'show_otp_form': True, 'remaining_time': remaining_time})  # Stay on the OTP page

    messages.error(request, "User not found.")
    return render(request, 'otp.html', {'show_otp_form': True})  # Stay on the OTP page if user not found



def google_redirect(request):
    return redirect(settings.SOCIALACCOUNT_PROVIDERS["google"]["AUTH_PARAMS"]["redirect_uri"])


def request_reset_otp(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)

            # Generate a 6-digit OTP
            otp = random.randint(100000, 999999)
            
            # Store OTP temporarily (Using Django cache for 5 mins)
            cache.set(f"otp_{email}", otp, timeout=300)

            # Send OTP via email
            send_mail(
                "Password Reset OTP",
                f"Your OTP for password reset is: {otp}",
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )

            messages.success(request, "OTP sent to your email.")
            return redirect("verify_reset_otp", email=email)  # Redirect to OTP verification page

        except User.DoesNotExist:
            messages.error(request, "No account found with this email.")
            return redirect("request_reset_otp")

    return render(request, "forgot_password/request_reset_otp.html")


def verify_reset_otp(request, email):
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        stored_otp = cache.get(f"otp_{email}")

        if stored_otp and str(stored_otp) == entered_otp:
            messages.success(request, "OTP verified successfully.")
            return redirect("reset_password", email=email)  # Redirect to reset password page
        else:
            messages.error(request, "Invalid OTP or expired OTP.")
            return redirect("verify_reset_otp", email=email)

    return render(request, "forgot_password/verify_otp.html", {"email": email})

def reset_password(request, email):
    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("reset_password", email=email)

        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)  # Keep user logged in if necessary

            messages.success(request, "Password updated successfully. You can now log in.")
            return redirect("login")  # Redirect to login page
        except User.DoesNotExist:
            messages.error(request, "Error updating password.")
            return redirect("reset_password", email=email)

    return render(request, "forgot_password/reset_password.html", {"email": email})
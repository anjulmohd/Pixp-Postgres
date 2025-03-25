from django.shortcuts import render,redirect,get_object_or_404
from cart.decorators import custom_login_required
from .forms import AddressForm,ProfilePictureForm
from .models import Address,ReferralCode,UsedReferral
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import authenticate
from django.contrib import messages
from order.models import Order,OrderItem
from payment.models import PaymentOrder,Wallet
import hashlib
from django.http import JsonResponse


# Create your views here.
User = get_user_model()

@custom_login_required
def profile_view(request):
    """Display all addresses created by the user and handle profile updates & password changes."""
    
    addresses = Address.objects.filter(user=request.user)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    paidorders = PaymentOrder.objects.filter(user=request.user).exclude(status="PENDING").order_by('-created_at')
    if request.method == 'POST':
        if 'profile_form' in request.POST:  # Handle profile updates
            # Update profile picture if uploaded
            if 'profile_picture' in request.FILES:
                request.user.profile_picture.delete(save=False)  # Delete the old file (optional)
                request.user.profile_picture = request.FILES['profile_picture']
                request.user.save()


            # Update username if provided
            if 'username' in request.POST:
                new_username = request.POST.get('username').strip()
                if new_username:
                    request.user.username = new_username

            # Save user model after updating fields
            request.user.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile_view')

        elif 'password_form' in request.POST:  # Handle password change
            current_password = request.POST.get("current_password")
            new_password = request.POST.get("new_password")
            confirm_password = request.POST.get("confirm_password")

            if not request.user.check_password(current_password):
                messages.error(request, "Current password is incorrect.")
                return redirect("profile_view")

            if new_password != confirm_password:
                messages.error(request, "New password and confirm password do not match.")
                return redirect("profile_view")

            request.user.set_password(new_password)
            request.user.save()

            # Keep the user logged in after password change
            update_session_auth_hash(request, request.user)

            messages.success(request, "Your password has been updated successfully.")
            return redirect("profile_view")

    return render(request, 'userapp/account.html', {
        'addresses': addresses,
        'orders': orders,
        'paidorders' : paidorders
    })



@custom_login_required
def add_address(request):
    """Allow user to add a new address."""
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            return redirect('profile_view')  # Redirect to address list after saving
    else:
        form = AddressForm()
    
    return render(request, 'userapp/add_address.html', {'form': form})
def edit_address(request, address_id):
    
    address = get_object_or_404(Address, id=address_id, user=request.user)

    if request.method == "POST":
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            return redirect('profile_view')  # Redirect back to address list
    else:
        form = AddressForm(instance=address)

    return render(request, 'userapp/edit_address.html', {'form': form})


def delete_address(request, address_id):
    """Delete an address."""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.delete()
    return redirect('profile_view')  # Redirect to address list after deletion

@custom_login_required
def upload_profile_picture(request):
    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile_view')  # Redirect to profile page (or wherever you want)
    else:
        form = ProfilePictureForm(instance=request.user)
    
    return render(request, 'userapp/upload_profile_picture.html', {'form': form})

def wallet_detail(request):
    """Display the user's wallet balance and transaction history."""
    wallet, created = Wallet.objects.get_or_create(user=request.user)  # Ensure wallet exists
    transactions = wallet.transactions.all().order_by("-created_at")  # Get all transactions (latest first)

    context = {
        "wallet": wallet,
        "transactions": transactions,
    }
    return render(request, "wallet/wallet_detail.html", context)

def show_or_create_referral(request):
    """Show or create a referral code for the logged-in user."""
    user = request.user

    # Get or create the referral code
    referral, created = ReferralCode.objects.get_or_create(user=user)

    # Generate a new referral code if it doesn’t exist
    if created or not referral.referrer_code:
        referral.referrer_code = referral.generate_referral_code()
        referral.save()

    # Check if the user has already used a referral code
    used_referral = UsedReferral.objects.filter(user=user).exists()

    return JsonResponse({
        "referral_code": referral.referrer_code,
        "referral_count": referral.referral_count,
        "has_used_referral": used_referral
    })



def apply_referral_code(request):
    """Apply a referral code only if the user hasn't used one yet."""
    if request.method == "POST":
        referral_code = request.POST.get("referral_code")

        # Check if the user has already used a referral
        if UsedReferral.objects.filter(user=request.user).exists():
            return JsonResponse({"message": "You have already used a referral code before."}, status=400)

        # Get the referral object
        referral = ReferralCode.objects.filter(referrer_code=referral_code).first()

        if referral:
            # Prevent self-referral
            if referral.user == request.user:
                return JsonResponse({"message": "You cannot apply your own referral code!"}, status=400)

            # Increment referral count for the original referrer (B)
            referral.referral_count += 1
            referral.save()

            # Create a record that this user used a referral code
            UsedReferral.objects.create(user=request.user, referrer=referral.user)

            return JsonResponse({
                "message": "Referral applied successfully!",
                "referrer_code": referral.referrer_code,
                "new_count": referral.referral_count,
            })
        else:
            return JsonResponse({"message": "Invalid referral code!"}, status=400)

    return JsonResponse({"message": "Invalid request"}, status=400)

def referralpage(request):
    return render(request,'referral.html')


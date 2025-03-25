from .models import Cart
from .models import Wishlist
def cart_item_count(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        count = cart.cart_items.count()  # Count total items in the cart
    else:
        count = 0  # If user is not logged in, set count to 0

    return {'cart_count': count}



def wishlist_item_count(request):
    if request.user.is_authenticated:
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        count = wishlist.items.count()  # Use 'items' from related_name in WishlistItem
    else:
        count = 0  # No wishlist items if user is not logged in

    return {'wishlist_count': count}


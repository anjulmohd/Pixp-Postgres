from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils.timezone import now
from .models import Coupon, Cart,Cart_items,Wishlist,WishlistItem
from myapp.models import Product,ProductVariant
from .decorators import custom_login_required
from django.http import JsonResponse
import logging
logger = logging.getLogger(__name__)
@custom_login_required
def view_cart(request):
    cart_items = Cart_items.objects.filter(cart__user=request.user)
    cart, created = Cart.objects.get_or_create(user=request.user)
    # Create a list to store the calculated subtotals for each item
    for item in cart_items:
        item.subtotal = item.get_total_price()  # You can use the get_total_price method or the subtotal property
    
    # Optionally, calculate the total price for the cart (sum of all item subtotals)
    total_price = sum(item.subtotal for item in cart_items)
    
    return render(request, 'cart.html', {
        'cart_items': cart_items, 
        'total_price': total_price,
        "cart": cart,
        
        
        })


# Create your views here.
def apply_coupon_function(cart):
    cart_items = cart.cart_items.all()
    if not cart_items.exists():
        return cart.total_price  # Return full price without applying coupon

    if cart.coupon and cart.coupon.is_valid():

        total_price = sum(item.get_total_price() for item in cart_items)

        if cart.coupon.discount_type == 'percentage':
            # Apply percentage discount
            discount = (cart.coupon.discount_value / 100) * total_price
        elif cart.coupon.discount_type == 'fixed':
            # Apply fixed discount
            discount = cart.coupon.discount_value
        else:
            discount = 0

        # Return the discounted price
        return total_price - discount
    return cart.total_price  # Return full price if no valid coupon

@custom_login_required

def add_to_cart(request, product_id):
    # Get the base product to be added to the cart
    product = get_object_or_404(Product, id=product_id)
    
    # Get the variant_id from the form (it might be None if no variant is selected)
    variant_id = request.POST.get('variant_id', None)
    
    # If variant_id is provided, fetch the corresponding variant of the product
    variant = None
    if variant_id:
        variant = get_object_or_404(ProductVariant, id=variant_id, product=product)
    
    # Get the quantity to be added to the cart from the POST request
    quantity = int(request.POST.get('quantity', 1))  # Default to 1 if no quantity is specified
    
    # Check stock availability
    if variant:  # If variant is selected
        if quantity > variant.stock_quantity:
            messages.error(request, f"Only {variant.stock_quantity} items of {variant.name} are available in stock.")
            return redirect('view_cart')
    else:  # If no variant, use the base product stock
        if quantity > product.stock_quantity:
            messages.error(request, f"Only {product.stock_quantity} items of {product.name} are available in stock.")
            return redirect('view_cart')
    
    # Get or create the user's cart
    cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
    
    # Check if the cart item already exists
    if variant:
        # If the variant is selected, check if it already exists in the cart
        cart_item, created = Cart_items.objects.get_or_create(cart=cart, product_variant=variant)
    else:
        # If no variant, check for the base product
        cart_item, created = Cart_items.objects.get_or_create(cart=cart, product=product)

    # If it's an existing item, update the quantity
    if not created:
        cart_item.quantity += quantity
        if variant:  # Ensure quantity does not exceed variant stock
            if cart_item.quantity > variant.stock_quantity:
                messages.error(request, f"Only {variant.stock_quantity} items of {variant.name} are available in stock.")
                return redirect('view_cart')
        else:  # Ensure quantity does not exceed product stock
            if cart_item.quantity > product.stock_quantity:
                messages.error(request, f"Only {product.stock_quantity} items of {product.name} are available in stock.")
                return redirect('view_cart')
    else:
        # If it's a new item, set the quantity
        cart_item.quantity = quantity

    cart_item.save()

    # Now, apply the coupon if it's available
    if cart.coupon and cart.coupon.is_valid():
        cart.discounted_price = apply_coupon_function(cart)
    else:
        cart.discounted_price = cart.total_price  # If no coupon, discounted price is the same as total price
    
    # Save the cart with the updated prices
    cart.save()

    # Provide success message to the user
    if variant:
        messages.success(request, f"{quantity} item(s) of {variant.name} added to your cart.")
    else:
        messages.success(request, f"{quantity} item(s) of {product.name} added to your cart.")
    
    return redirect("view_cart")  # Redirect to the cart or wherever appropriate



@custom_login_required
def update_cart(request):
    cart = Cart.objects.filter(user=request.user).first()  # Get the user's cart

    if request.method == "POST":
        for item in cart.cart_items.all():
            quantity_key = f"quantity_{item.id}"  # Matching input name in the template
            new_quantity = int(request.POST.get(quantity_key, item.quantity))  # Get new quantity

            # Check stock availability
            if item.product_variant:  # If the item has a variant
                if new_quantity > item.product_variant.stock_quantity:
                    messages.error(request, f"Only {item.product_variant.stock_quantity} items of {item.product_variant.name} are available.")
                    return redirect("view_cart")
            else:  # If the item has a base product
                if new_quantity > item.product.stock_quantity:
                    messages.error(request, f"Only {item.product.stock_quantity} items of {item.product.name} are available.")
                    return redirect("view_cart")

            # Update or delete the item
            if new_quantity > 0:
                item.quantity = new_quantity
                item.save()
            else:
                item.delete()  # If quantity is 0, remove the item from cart

        # Recalculate cart's total price
        cart.total_price = sum(item.get_total_price() for item in cart.cart_items.all())

        # Apply coupon if available
        if cart.coupon and cart.coupon.is_valid():
            cart.discounted_price = apply_coupon_function(cart)
        else:
            cart.discounted_price = cart.total_price

        cart.save()

    return redirect("view_cart")  # Redirect to cart page after update


def remove_from_cart(request, cart_item_id):
    # Get the user's cart
    cart = Cart.objects.filter(user=request.user).first()
    if not cart:
        messages.error(request, "Cart not found.")
        return redirect('view_cart')

    # Retrieve the cart item to remove
    cart_item = get_object_or_404(Cart_items, id=cart_item_id, cart=cart)
    cart_item.delete()  # Remove the item from the cart

    # Recalculate the cart's total price
    cart.total_price = sum(item.get_total_price() for item in cart.cart_items.all())

    # Apply coupon if available
    if cart.coupon and cart.coupon.is_valid():
        cart.discounted_price = apply_coupon_function(cart)
    else:
        cart.discounted_price = cart.total_price  # If no coupon, discounted price is the same as total price

    # If the cart is empty, reset prices to 0
    if cart.cart_items.count() == 0:
        cart.total_price = 0
        cart.discounted_price = 0

    cart.save()  # Save the cart with the updated prices

    # Provide feedback to the user
    messages.success(request, "Item removed from cart.")
    return redirect('view_cart')



def apply_coupon(request):
    if request.method == "POST":
        coupon_code = request.POST.get("coupon_code")
        cart_id = request.POST.get("cart_id")

        # Get cart and coupon
        cart = get_object_or_404(Cart, id=cart_id, user=request.user)
        try:
            coupon = Coupon.objects.get(code=coupon_code)
        except Coupon.DoesNotExist:
            messages.error(request, "Invalid coupon code.")
            return redirect("view_cart")

        # Validate coupon
        if not coupon.is_active:
            messages.error(request, "This coupon is no longer active.")
            return redirect("view_cart")

        if coupon.expiration_date < now():
            messages.error(request, "This coupon has expired.")
            return redirect("view_cart")

        if coupon.used_count >= coupon.usage_limit:
            messages.error(request, "This coupon has reached its usage limit.")
            return redirect("view_cart")

        # Calculate discount
        total_price = sum(item.get_total_price() for item in cart.cart_items.all())
        print(f"Total Price: ₹{total_price}")

        if coupon.discount_type == "percentage":
            discount_amount = (coupon.discount_value / 100) * total_price
        else:
            discount_amount = coupon.discount_value

        discounted_price = max(total_price - discount_amount, 0)

        print(f"Discounted Price: ₹{discounted_price}")

        # Update cart with the discounted price and coupon
        cart.discounted_price = discounted_price
        cart.coupon = coupon
        cart.save()

        # Update coupon usage count
        coupon.used_count += 1
        coupon.save()

        messages.success(request, f"Coupon '{coupon_code}' applied successfully! Discounted price: ₹{discounted_price}")

    return redirect("view_cart")

def remove_coupon(request):
    cart = Cart.objects.filter(user=request.user).first()

    if cart and cart.coupon:
        cart.coupon = None  # Remove the coupon reference
        cart.discounted_price = 0  # Reset any discounted price if stored
        cart.save()

        messages.success(request, "Coupon removed successfully!")
    else:
        messages.error(request, "No coupon applied to remove.")

    return redirect("view_cart")

@custom_login_required
def view_wishlist(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    return render(request, 'wishlist.html', {'wishlist': wishlist})

@custom_login_required
def add_to_wishlist(request, product_id):
    if request.method == 'POST':
        logger.info(f"Received POST request to add product {product_id} to wishlist.")
        product = get_object_or_404(Product, id=product_id)
        variant_id = request.POST.get('variant_id', None)
        logger.info(f"Variant ID: {variant_id}")
        variant = None

        if variant_id:
            variant = get_object_or_404(ProductVariant, id=variant_id, product=product)

        wishlist, created = Wishlist.objects.get_or_create(user=request.user)

        try:
            if variant:
                wishlist_item, created = WishlistItem.objects.get_or_create(wishlist=wishlist, product_variant=variant)
            else:
                wishlist_item, created = WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)

            return JsonResponse({'success': True, 'message': 'Product added to wishlist.'})
        except ValueError as e:
            logger.error(f"Error adding to wishlist: {e}")
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

def remove_from_wishlist(request, item_id):
    # Get the user's wishlist
    wishlist = get_object_or_404(Wishlist, user=request.user)
    
    # Get the wishlist item to be removed
    wishlist_item = get_object_or_404(WishlistItem, id=item_id, wishlist=wishlist)
    
    # Delete the wishlist item
    wishlist_item.delete()
    
    # Success message
    if wishlist_item.product:
        messages.success(request, f"{wishlist_item.product.name} removed from wishlist.")
    elif wishlist_item.product_variant:
        messages.success(request, f"{wishlist_item.product_variant.name} removed from wishlist.")
    
    return redirect('view_wishlist')

def list_to_cart(request, item_id):
    # Get the wishlist item to be moved to the cart
    wishlist = get_object_or_404(Wishlist, user=request.user)
    wishlist_item = get_object_or_404(WishlistItem, id=item_id, wishlist=wishlist)
    
    # Get or create the user's cart
    cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
    
    # Check stock availability before adding to cart
    if wishlist_item.product:
        # If it's a base product
        product = wishlist_item.product
        if product.stock_quantity < 1:  # Check if product is out of stock
            messages.error(request, f"{product.name} is out of stock.")
            return redirect('view_wishlist')
        
        # Get or create the cart item
        cart_item, created = Cart_items.objects.get_or_create(cart=cart, product=product)
        
    elif wishlist_item.product_variant:
        # If it's a product variant
        variant = wishlist_item.product_variant
        if variant.stock_quantity < 1:  # Check if variant is out of stock
            messages.error(request, f"{variant.name} is out of stock.")
            return redirect('view_wishlist')
        
        # Get or create the cart item
        cart_item, created = Cart_items.objects.get_or_create(cart=cart, product_variant=variant)
    
    # If the item already exists in the cart, check if increasing quantity exceeds stock
    if not created:
        if wishlist_item.product:
            if cart_item.quantity + 1 > product.stock_quantity:
                messages.error(request, f"Only {product.stock_quantity} items of {product.name} are available.")
                return redirect('view_wishlist')
        elif wishlist_item.product_variant:
            if cart_item.quantity + 1 > variant.stock_quantity:
                messages.error(request, f"Only {variant.stock_quantity} items of {variant.name} are available.")
                return redirect('view_wishlist')
        
        # Increase the quantity if stock is sufficient
        cart_item.quantity += 1
        cart_item.save()
    
    # Update the cart's total and discounted prices
    cart.total_price = sum(item.get_total_price() for item in cart.cart_items.all())
    if cart.coupon and cart.coupon.is_valid():
        cart.discounted_price = apply_coupon_function(cart)
    else:
        cart.discounted_price = cart.total_price  # If no coupon, discounted price is the same as total price
    cart.save()
    
    # Remove the item from the wishlist
    wishlist_item.delete()
    
    # Success message
    if wishlist_item.product:
        messages.success(request, f"{wishlist_item.product.name} added to cart and removed from wishlist.")
    elif wishlist_item.product_variant:
        messages.success(request, f"{wishlist_item.product_variant.name} added to cart and removed from wishlist.")
    
    return redirect('view_cart')


def shop_to_wishlist(request, product_id):
    if request.method == 'POST':
        # Get the base product
        product = get_object_or_404(Product, id=product_id)

        # Get or create the user's wishlist
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)

        try:
            # Add the base product to the wishlist
            wishlist_item, created = WishlistItem.objects.get_or_create(
                wishlist=wishlist,
                product=product
            )
            if created:
                message = f"{product.name} added to wishlist."
            else:
                message = f"{product.name} is already in your wishlist."

            return JsonResponse({'success': True, 'message': message})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})
from django.shortcuts import render,redirect,get_object_or_404
from cart.models import Cart,Cart_items
from userapp.models import Address
from django.contrib import messages
from .models import Order,OrderItem
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from cart.models import Cart, Cart_items
from django.http import JsonResponse
from django.conf import settings
from django.contrib import messages
from cart.decorators import custom_login_required
import json
from django.views.decorators.csrf import csrf_exempt
import razorpay
from payment.models import PaymentOrder
from payment.models import Wallet



def checkout(request):
    # Ensure the user is authenticated
    if not request.user.is_authenticated:
        messages.warning(request, "Please log in to proceed to checkout.")
        return redirect('login')

    # Get the user's cart
    cart = Cart.objects.filter(user=request.user).first()
    if not cart:
        messages.warning(request, "Your cart is empty. Please add items before proceeding to checkout.")
        return redirect('view_cart')

    # Get cart items with related products and variants
    cart_items = Cart_items.objects.filter(cart=cart).select_related('product', 'product_variant')
    if not cart_items.exists():
        messages.warning(request, "Your cart is empty. Please add items before proceeding to checkout.")
        return redirect('view_cart')

    # Validate stock for all items in the cart
    out_of_stock_items = []
    for item in cart_items:
        if item.product_variant:  # Check stock for variants
            if item.quantity > item.product_variant.stock_quantity:
                out_of_stock_items.append(item.product_variant.name)
        else:  # Check stock for base products
            if item.quantity > item.product.stock_quantity:
                out_of_stock_items.append(item.product.name)

    if out_of_stock_items:
        messages.error(request, f"The following items are out of stock: {', '.join(out_of_stock_items)}")
        return redirect('view_cart')

    # Get wallet balance
    wallet = Wallet.objects.get(user=request.user)
    wallet_balance = wallet.balance

    # Calculate subtotal and total price
    for item in cart_items:
        item.subtotal = item.get_total_price()
    total_price = sum(item.subtotal for item in cart_items)

    # Get user addresses
    addresses = Address.objects.filter(user=request.user)

    # Check if there is a default address
    has_default_address = addresses.filter(is_default=True).exists()

    # Handle POST requests (e.g., setting default address or placing an order)
    if request.method == 'POST':
        # Check if the request is for setting a default address
        if 'set_default_address' in request.POST:
            selected_address_id = request.POST.get('default_address')
            
            if selected_address_id:
                # Ensure the selected address belongs to the user
                selected_address = get_object_or_404(Address, id=selected_address_id, user=request.user)
                
                # Set all addresses to `is_default = False`
                Address.objects.filter(user=request.user).update(is_default=False)
                
                # Set the selected address as default
                selected_address.is_default = True
                selected_address.save()

                messages.success(request, "Default address updated successfully.")
                return redirect('checkout')
            else:
                messages.error(request, "Please select an address.")
                return redirect('checkout')

        # Check if the request is for placing an order
        elif 'place_order' in request.POST:
            if not has_default_address:
                messages.error(request, "Please select a default address before placing an order.")
                return redirect('checkout')

            # Proceed to payment or order confirmation
            return redirect('payment')  # Replace with your payment or order confirmation view

    # Render the checkout page
    return render(request, 'checkout.html', {
        'cart_items': cart_items, 
        'cart': cart,
        'total_price': total_price,
        'addresses': addresses,
        'wallet_balance': wallet_balance,
        'has_default_address': has_default_address,  # Pass whether a default address exists
    })

def payment(request):
    # Ensure the user is authenticated
    if not request.user.is_authenticated:
        messages.warning(request, "Please log in to proceed with payment.")
        return redirect('login')

    # Add your payment logic here
    return render(request, 'payment.html')

def place_order(request):
    user = request.user
    cart = get_object_or_404(Cart, user=user, is_active=True)
    cart_items = Cart_items.objects.filter(cart=cart)

    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('view_cart')
    
    if not user.addresses.filter(is_default=True).exists():
        messages.error(request, "You need to set a default address to place an order.")
        return redirect('checkout')  # Redirect the user to the page where they can set their default address

    total_price = sum(item.get_total_price() for item in cart_items)

    if cart.coupon:
        discounted_price = cart.discounted_price
    else:
        discounted_price = total_price

    # Create the order
    order = Order.objects.create(
        user=user,
        total_price=total_price,
        discounted_price=discounted_price,
        status='PENDING'
    )

    # Create order items
    for cart_item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=cart_item.product if not cart_item.product_variant else None,  # Set product only if no variant
            product_variant=cart_item.product_variant,  # Set variant if it exists
            quantity=cart_item.quantity
        )
    
    # Deactivate the cart after placing the order
    cart.delete()
    cart.save()

    messages.success(request, "Your order has been placed successfully.")
    return redirect('order_detail', order_id=order.id)


@custom_login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)

    context = {
        'order': order,
        'order_items': order_items
    }
    return render(request, 'order_detail.html', context)


@custom_login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')  # Show latest orders first
    paidorders = PaymentOrder.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'userapp/account.html', {'orders': orders,
                                                    'paidorders': paidorders,
                                                    
                                                    
                                                    
                                                    })

def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status == 'PENDING':  # Only allow cancellation if order is pending
        order.status = 'CANCELLED'
        order.save()
        messages.success(request, "Your order has been cancelled.")
    else:
        messages.error(request, "You cannot cancel this order.")

    return redirect('profile_view')

def return_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == "POST":
        reason = request.POST.get("reason", "").strip()

        if order.status == 'DELIVERED':
            order.status = 'RETURN_REQUESTED'
            order.reason = reason  # Store the reason
            order.save()
            messages.success(request, "Your order return request has been submitted.")
        else:
            messages.error(request, "You cannot return  this order.")

        return redirect('profile_view')

    return render(request, 'userapp/reason_order.html', {'order': order})  # Show the form



def generate_invoice_pdf(request, order_id):
    """Generate and return a PDF invoice for an order."""
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)

    # Create a response object for the PDF
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Invoice_{order.order_unique_id}.pdf"'

    # Create a PDF document
    pdf = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # Set title
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(200, height - 50, "Invoice")

    # Order details
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height - 100, f"Order ID: {order.order_unique_id}")
    pdf.drawString(50, height - 120, f"Customer: {order.user.username} ({order.user.email})")
    pdf.drawString(50, height - 140, f"Order Date: {order.created_at.strftime('%d-%m-%Y %H:%M')}")

    # Table header
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, height - 180, "Product")
    pdf.drawString(300, height - 180, "Quantity")
    pdf.drawString(400, height - 180, "Price")
    pdf.drawString(500, height - 180, "Total")

    # Order items
    y_position = height - 200
    pdf.setFont("Helvetica", 12)
    for item in order_items:
    # Determine the product name (including variant if available)
        product_name = f"{item.product_variant.product.name} - {item.product_variant.name}" if item.product_variant else item.product.name

        # Determine the price (variant price if available)
        price = item.product_variant.price if item.product_variant else item.product.price

        pdf.drawString(50, y_position, product_name)
        pdf.drawString(300, y_position, str(item.quantity))
        pdf.drawString(400, y_position, f"₹{price}")
        pdf.drawString(500, y_position, f"₹{item.get_total_price()}")
        y_position -= 20

    # Total price
    y_position -= 20
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(400, y_position, "Total:")
    pdf.drawString(500, y_position, f"₹{order.total_price}")

    # Save PDF
    pdf.showPage()
    pdf.save()

    return response


        
def toggle_postreturn_request(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id)
    
    if request.method == "POST":
        reason = request.POST.get("reason", "").strip()
        
        if reason:
            # Mark as return requested
            item.return_requested = True
            item.reason = reason
            item.save()
            
            messages.success(request, f"Return request for '{item.product.name if item.product else item.product_variant.product.name}' has been submitted successfully.")
        else:
            messages.error(request, "Return reason cannot be empty.")

    return redirect(request.META.get("HTTP_REFERER", "profile_view"))
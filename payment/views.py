import razorpay
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect,render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import PaymentOrder,PaymentOrderItem
from cart.models import Cart, Cart_items
from django.contrib import messages
import json
import logging
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from .models import Wallet
logger = logging.getLogger(__name__)
from cart.decorators import custom_login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.urls import reverse
from .forms import WalletDepositForm
from razorpay.errors import SignatureVerificationError
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import time
from decimal import Decimal
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
@csrf_exempt  
def place_paymentorder(request):
    if request.method == "POST":
        user = request.user

        if not user.is_authenticated:
            print("DEBUG: User is NOT authenticated!")  # Debugging
            return JsonResponse({"error": "User not logged in"}, status=401)

        cart = get_object_or_404(Cart, user=user, is_active=True)
        cart_items = Cart_items.objects.filter(cart=cart)

        print("DEBUG: Cart Total Price =", cart.total_price)

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        # Determine total and discounted price
        total_price = sum(item.get_total_price() for item in cart_items)
        discounted_price = cart.discounted_price if cart.coupon and cart.discounted_price is not None else total_price

        try:
            razorpay_order = client.order.create({
                "amount": int(float(discounted_price) * 100),
                "currency": "INR",
                "payment_capture": 1,
                "notes": {
                    "callback_url": "http://127.0.0.1:8000/payment/verify_payment/"
                }
            })
        except Exception as e:
            print("DEBUG: Razorpay Error =", str(e))
            return JsonResponse({"error": str(e)}, status=400)

        # Create the payment order
        order = PaymentOrder.objects.create(
            user=user,
            total_price=total_price,
            discounted_price=discounted_price,
            razorpay_order_id=razorpay_order["id"]
        )

        # Create payment order items with product variants
        for cart_item in cart_items:
            PaymentOrderItem.objects.create(
                order=order,
                product=cart_item.product if not cart_item.product_variant else None,  # Store product only if no variant
                product_variant=cart_item.product_variant,  # Store variant if it exists
                quantity=cart_item.quantity
            )

        return JsonResponse({
            "razorpay_key": settings.RAZORPAY_KEY_ID,
            "razorpay_order_id": razorpay_order["id"],
            "amount": float(razorpay_order["amount"]),
            "currency": razorpay_order["currency"]
        })  # ✅ Ensure response is JSON, not a redirect

    return JsonResponse({"error": "Invalid request"}, status=400)





@csrf_exempt
def verify_payment(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            logger.info(f"Received payment data: {data}")  # ✅ Log received data

            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            # Verifying payment signature
            params_dict = {
                'razorpay_order_id': data.get('razorpay_order_id'),
                'razorpay_payment_id': data.get('razorpay_payment_id'),
                'razorpay_signature': data.get('razorpay_signature')
            }

            try:
                client.utility.verify_payment_signature(params_dict)
                logger.info("Signature verification successful.")  # ✅ Log success

                # ✅ Fetch Order
                order = get_object_or_404(PaymentOrder, razorpay_order_id=data['razorpay_order_id'])

                # ✅ Check if order is already paid
                if order.status == "PAID":
                    logger.warning(f"Order {order.id} is already paid.")
                    return JsonResponse({"status": "Payment Already Completed"}, status=400)

                # ✅ Update Order Status
                order.status = "PAID"
                order.razorpay_payment_id = data['razorpay_payment_id']
                order.save()
                logger.info(f"Order {order.id} marked as PAID.")

                # ✅ Remove cart after successful payment
                Cart.objects.filter(user=order.user, is_active=True).delete()

                return JsonResponse({"status": "Payment Successful", "order_id": order.id})

            except razorpay.errors.SignatureVerificationError:
                logger.error("Signature verification failed!", exc_info=True)
                return JsonResponse({"status": "Payment Failed"}, status=400)

        except Exception as e:
            logger.error(f"Error processing payment: {str(e)}", exc_info=True)
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid Request"}, status=400)




def order_success(request, order_id):
    """Renders order success page."""
    order = get_object_or_404(PaymentOrder, id=order_id, user=request.user)
    order_items = PaymentOrderItem.objects.filter(order=order)

    context = {
        'order': order,
        'order_items': order_items
    }
    return render(request, "order_success.html", context)

def order_failed(request):
    """Renders order failure page."""
    return render(request, "order_failed.html")


def generate_invoice_paid_pdf(request, order_id):
    # Get the order details
    order = get_object_or_404(PaymentOrder, id=order_id)
    items = order.order_items.all()  # Fetch all items in this order

    # Create the HTTP response object with a PDF content type
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'

    # Create the PDF document
    pdf = canvas.Canvas(response, pagesize=A4)
    pdf.setTitle(f"Invoice_{order.id}")

    # Define starting position
    y = 800  # Start from the top

    # Add header
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(200, y, "Invoice")
    y -= 30  # Move down

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, y, f"Order ID: {order.order_unique_id}")
    pdf.drawString(350, y, f"Date: {order.created_at.strftime('%Y-%m-%d')}")
    y -= 20

    pdf.drawString(50, y, f"Customer: {order.user.username}")
    pdf.drawString(350, y, f"Status: {order.status}")
    y -= 30

    # Table headers
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Product")
    pdf.drawString(250, y, "Quantity")
    pdf.drawString(350, y, "Price")
    pdf.drawString(450, y, "Total")
    y -= 20
    pdf.line(50, y, 550, y)  # Draw a line
    y -= 20

    # Add each product
    pdf.setFont("Helvetica", 12)
    for item in items:
        pdf.drawString(50, y, item.product.name)
        pdf.drawString(250, y, str(item.quantity))
        pdf.drawString(350, y, f"₹{item.product.price:.2f}")
        pdf.drawString(450, y, f"₹{item.get_total_price():.2f}")
        y -= 20

    pdf.line(50, y, 550, y)  # Draw another line
    y -= 30

    # Total price
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(350, y, "Total:")
    pdf.drawString(450, y, f"₹{order.total_price:.2f}")

    # Save and return the PDF response
    pdf.showPage()
    pdf.save()
    return response

def cancel_paidorder(request, order_id):
    order = get_object_or_404(PaymentOrder, id=order_id, user=request.user)

    if request.method == "POST":
        cancellation_reason = request.POST.get("reason", "").strip()

        if order.status == 'PAID':
            order.status = 'CANCEL_REQUESTED'
            order.reason = cancellation_reason  # Store the reason
            order.save()
            messages.success(request, "Your order cancellation request has been submitted.")
        else:
            messages.error(request, "You cannot cancel this order.")

        return redirect('profile_view')

    return render(request, 'userapp/reason_paidorder.html', {'order': order})  # Show the form


def return_paidorder(request, order_id):
    order = get_object_or_404(PaymentOrder, id=order_id, user=request.user)

    if request.method == "POST":
        cancellation_reason = request.POST.get("reason", "").strip()

        if order.status == 'DELIVERED':
            order.status = 'RETURN_REQUESTED'
            order.reason = cancellation_reason  # Store the reason
            order.save()
            messages.success(request, "Your order return request has been submitted.")
        else:
            messages.error(request, "You cannot return  this order.")

        return redirect('profile_view')

    return render(request, 'userapp/reason_paidorder.html', {'order': order})  # Show the form
@custom_login_required
def wallet_detail(request):
    """Display the user's wallet balance and transaction history."""
    wallet, created = Wallet.objects.get_or_create(user=request.user)  # Ensure wallet exists
    transactions = wallet.transactions.all().order_by("-created_at")  # Get all transactions (latest first)

    context = {
        "wallet": wallet,
        "transactions": transactions,
    }
    return render(request, "wallet/wallet_detail.html", context)




def create_razorpay_order(request):
    """Create a Razorpay order for adding money to the wallet."""
    if request.method == "POST":
        try:
            # Parse request data
            data = json.loads(request.body)
            amount = int(float(data.get("amount", 0)) * 100)  # Convert to paise

            # Validate amount
            if amount <= 0:
                return JsonResponse({"error": "Invalid amount"}, status=400)

            # Initialize Razorpay client
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            # Create Razorpay order
            order_data = {
                "amount": amount,  # Amount in paise
                "currency": "INR",
                "payment_capture": 1,  # Auto-capture payment
                "receipt": f"wallet_rcpt_{int(time.time())}"  # Unique receipt ID
            }
            order = client.order.create(order_data)

            # Return order ID to the client
            return JsonResponse({
                "order_id": order["id"],
                "amount": order["amount"],
                "currency": order["currency"]
            })

        except Exception as e:
            print(f"Error creating Razorpay order: {str(e)}")
            return JsonResponse({"error": f"Failed to create order: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def razorpay_success(request):
    """Handle Razorpay payment success for wallet."""
    if request.method == "POST":
        try:
            # Parse request data
            data = json.loads(request.body)
            payment_id = data.get("razorpay_payment_id")
            order_id = data.get("razorpay_order_id")
            signature = data.get("razorpay_signature")

            # Log received data for debugging
            print(f"Received payment data: payment_id={payment_id}, order_id={order_id}")

            # Validate required parameters
            if not (payment_id and order_id and signature):
                return JsonResponse({
                    "status": "error",
                    "message": "Missing required parameters"
                }, status=400)

            # Initialize Razorpay client
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            # Verify payment signature
            params_dict = {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature
            }

            try:
                # Verify signature
                client.utility.verify_payment_signature(params_dict)

                # Fetch order details
                order = client.order.fetch(order_id)
                amount = Decimal(str(order["amount"])) / 100  # Convert from paise to rupees (as Decimal)

                # Check if the user is authenticated
                if not request.user.is_authenticated:
                    return JsonResponse({
                        "status": "error",
                        "message": "User not authenticated"
                    }, status=401)

                # Update wallet balance
                try:
                    wallet = request.user.wallet
                    wallet.deposit(amount, description=f"Razorpay Deposit (ID: {payment_id})")

                    return JsonResponse({
                        "status": "success",
                        "amount": float(amount)  # Return float for JSON serialization
                    })
                except Exception as e:
                    print(f"Error updating wallet: {str(e)}")
                    return JsonResponse({
                        "status": "error",
                        "message": f"Error updating wallet: {str(e)}"
                    }, status=500)

            except SignatureVerificationError as e:
                print(f"Signature verification failed: {str(e)}")
                return JsonResponse({
                    "status": "error",
                    "message": "Payment signature verification failed"
                }, status=400)
            except Exception as e:
                print(f"Error processing payment: {str(e)}")
                return JsonResponse({
                    "status": "error",
                    "message": f"Error processing payment: {str(e)}"
                }, status=500)

        except Exception as e:
            print(f"General error: {str(e)}")
            return JsonResponse({
                "status": "error",
                "message": f"General error: {str(e)}"
            }, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)

def place_order_wallet(request):
    if request.method == "POST":
        user = request.user
        cart = get_object_or_404(Cart, user=user, is_active=True)
        cart_items = Cart_items.objects.filter(cart=cart)

        # Check if the cart is empty
        if not cart_items.exists():
            return JsonResponse({"error": "Your cart is empty."}, status=400)

        # Check if the user has a default address
        if not user.addresses.filter(is_default=True).exists():
            return JsonResponse({"error": "You need to set a default address to place an order."}, status=400)

        # Calculate total price and discounted price
        total_price = sum(item.get_total_price() for item in cart_items)
        discounted_price = cart.discounted_price if cart.coupon else total_price

        # Check if the user has sufficient wallet balance
        wallet = Wallet.objects.get(user=user)
        if wallet.balance < discounted_price:
            return JsonResponse({"error": "Insufficient wallet balance to place the order."}, status=400)

        # Create the order
        order = PaymentOrder.objects.create(
            user=user,
            total_price=total_price,
            discounted_price=discounted_price,
            status='PAID'
        )

        # Create order items
        for cart_item in cart_items:
            PaymentOrderItem.objects.create(
                order=order,
                product=cart_item.product if not cart_item.product_variant else None,  # Set product only if no variant
                product_variant=cart_item.product_variant,  # Set variant if it exists
                quantity=cart_item.quantity
            )

        # Deduct the amount from the wallet balance
        wallet.withdraw(discounted_price, description=f"Payment for Order #{order.id}")

        # Deactivate the cart after placing the order
        cart.delete()
        cart.save()

        return JsonResponse({"status": "success", "order_id": order.id})
    

def toggle_return_request(request, item_id):
    item = get_object_or_404(PaymentOrderItem, id=item_id)
    
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
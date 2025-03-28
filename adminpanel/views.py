from django.shortcuts import render, get_object_or_404, redirect
from myapp.models import Product,Category, ProductImage,ProductVariant
from .forms import ProductForm, OrderStatusUpdateForm,CategoryForm,PaidOrderStatusUpdateForm,CouponForm,ProductVariantForm
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q,Sum,F,Count,DecimalField
from django.db.models.functions import Lower
from django.core.paginator import Paginator
from django.views.generic import CreateView,UpdateView
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.hashers import make_password,check_password
from login.models import CustomUser
from django.contrib.auth import get_user_model
from order.models import Order,OrderItem
from django.urls import reverse
from payment.models import PaymentOrderItem,PaymentOrder,Wallet
from decimal import Decimal,ROUND_DOWN
from datetime import datetime, timedelta
from django.db.models.functions import TruncDate
import json

from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import io
from cart.models import Coupon 
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.functions import TruncMonth
from collections import defaultdict
from django.db.models.functions import Coalesce
User = get_user_model()
# Check if user is superuser
def admin_required(user):
    return user.is_superuser

@user_passes_test(admin_required)
def admin_dashboard(request):
    orders = Order.objects.all()
    payment_orders = PaymentOrder.objects.exclude(status="PENDING")

    # Combine both models' order data
    combined_orders = list(orders) + list(payment_orders)
    total_combined_count = len(combined_orders)
    total_combined_price = sum(order.total_price for order in orders) + sum(payment_order.total_price for payment_order in payment_orders)

    # Aggregating revenue per month
    order_revenue = (
        Order.objects.annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('total_price'))
        .order_by('month')
    )

    payment_revenue = (
        PaymentOrder.objects.exclude(status="PENDING")
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('total_price'))
        .order_by('month')
    )

    order_items = OrderItem.objects.values('product__id', 'product__name', 'product__category__name').annotate(total_quantity=Sum('quantity'))
    payment_order_items = PaymentOrderItem.objects.values('product__id', 'product__name', 'product__category__name').annotate(total_quantity=Sum('quantity'))

    #  Merge product sales data
    product_sales = defaultdict(int)
    category_sales = defaultdict(int)

    for item in order_items:
        product_sales[item['product__name']] += item['total_quantity']
        category_sales[item['product__category__name']] += item['total_quantity']

    for item in payment_order_items:
        product_sales[item['product__name']] += item['total_quantity']
        category_sales[item['product__category__name']] += item['total_quantity']

    #  Sorting top-selling products and categories
    best_selling_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]  # Top 5 products
    best_selling_categories = sorted(category_sales.items(), key=lambda x: x[1], reverse=True)[:3]  # Top 3 categories

    # Formatting for JSON serialization
    product_labels = [p[0] for p in best_selling_products]
    product_data = [p[1] for p in best_selling_products]

    category_labels = [c[0] for c in best_selling_categories]
    category_data = [c[1] for c in best_selling_categories]



    # Merging revenue data
    revenue_dict = {}
    for item in order_revenue:
        revenue_dict[item['month'].strftime('%b')] = item['total']

    for item in payment_revenue:
        month = item['month'].strftime('%b')
        revenue_dict[month] = revenue_dict.get(month, 0) + item['total']

    # Extracting month names and revenues
    months = list(revenue_dict.keys())
    revenues = list(revenue_dict.values())

    #  **Orders Pie Chart Data**
    order_status_counts = Order.objects.values('status').annotate(count=Count('status'))
    payment_status_counts = PaymentOrder.objects.values('status').annotate(count=Count('status'))

    # Merging both status counts
    status_dict = {}
    for item in order_status_counts:
        status_dict[item["status"]] = item["count"]

    for item in payment_status_counts:
        status_dict[item["status"]] = status_dict.get(item["status"], 0) + item["count"]

    # Sorting statuses for consistency
    sorted_statuses = [
        "PENDING", "PROCESSING", "SHIPPED", "DELIVERED", "CANCELLED", 
        "RETURN_REQUESTED", "RETURN_APPROVED", "CANCEL_REQUESTED", "CANCEL_APPROVED"
    ]

    status_labels = []
    status_data = []
    status_colors = {
        "PENDING": "#ffc107", "PROCESSING": "#17a2b8", "SHIPPED": "#007bff", "DELIVERED": "#28a745",
        "CANCELLED": "#dc3545", "RETURN_REQUESTED": "#fd7e14", "RETURN_APPROVED": "#6610f2",
        "CANCEL_REQUESTED": "#6c757d", "CANCEL_APPROVED": "#20c997"
    }

    for status in sorted_statuses:
        if status in status_dict:
            status_labels.append(status.replace("_", " ").title())  # Format as "Return Requested"
            status_data.append(status_dict[status])

    context = {
        'user': request.user,
        'total_combined_count': total_combined_count,
        'total_combined_price': total_combined_price,
        'graph_data': json.dumps({'months': months, 'revenues': revenues}, cls=DjangoJSONEncoder),
        'pie_chart_data': json.dumps({'labels': status_labels, 'data': status_data, 'colors': [status_colors[s] for s in sorted_statuses if s in status_dict]}, cls=DjangoJSONEncoder),
        'best_selling_products': json.dumps({'labels': product_labels, 'data': product_data}, cls=DjangoJSONEncoder),
        'best_selling_categories': json.dumps({'labels': category_labels, 'data': category_data}, cls=DjangoJSONEncoder),
    
    }

    return render(request, 'admin/admin-dashboard.html', context)

def manage_category(request):
    categories = Category.objects.all()
    form = CategoryForm()

    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES)  # Added request.FILES

        if form.is_valid():
            form.save()
            return redirect("manage_category")  # Redirect to refresh the page
        else:
            # Form is invalid - errors will be displayed in template
            pass

    return render(request, "admin/manage-category.html", {
        "categories": categories, 
        "form": form
    })

def toggle_sale(request, category_id):
    """Toggle the sale status of a category."""
    category = get_object_or_404(Category, id=category_id)
    category.is_sale = not category.is_sale
    category.save()
    messages.success(request, f"{category.name} sale status updated.")
    return redirect('manage_category')

def update_discount(request, category_id):
    """Update the discount percentage of a category."""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == "POST":
        sale_percentage = request.POST.get("sale_percentage")
        if sale_percentage is not None:
            category.sale_percentage = float(sale_percentage)
            category.save()
            messages.success(request, f"{category.name} discount updated to {sale_percentage}%.")

    return redirect('manage_category')

def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.delete()
    return redirect("manage_category")

# List all products
@user_passes_test(admin_required)
def product_list(request):
    # Initial product queryset
    products = Product.objects.active()
      # Get only unblocked products
    category = Category.objects.all()  # Get all categories for filtering
    
    # Get query parameters from the request
    query = request.GET.get('q')
    selected_category = str(request.GET.get('category', 'all'))
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort_by')
    is_blocked = request.GET.get('is_blocked')

    # Search functionality
    if query:
        products = products.filter(
            Q(name__icontains=query) |  # Search by product name
            Q(category__name__icontains=query)  # Search by category name
        )

    # Category filter
    if selected_category and selected_category != "all":
        try:
            selected_category = int(selected_category)  # Convert to int
            products = products.filter(category__id=selected_category)
        except ValueError:
            pass  # Ignore invalid category values

    # Price filters
    if min_price:
        products = products.filter(price__gte=min_price)

    if max_price:
        products = products.filter(price__lte=max_price)
    if is_blocked:  # Checkbox is checked
        products = Product.objects.filter(is_blocked=True)

    # Sorting functionality
    if sort_by == "date_asc":
        products = products.order_by('date')
    elif sort_by == "date_desc":
        products = products.order_by('-date')
    
    elif sort_by == "price_asc":
        products = products.order_by("price")
    elif sort_by == "price_desc":
        products = products.order_by("-price")
    elif sort_by == "name_asc":
        products = products.order_by(Lower("name"))
    elif sort_by == "name_desc":
        products = products.order_by(Lower("name").desc())
    
    

    else:
        products = products.order_by('-date')  # Default to sorting by date (newest first)

    total_strength = products.count()

    # Pagination
    paginator = Paginator(products, 16)  # Show 16 products per page
    page_number = request.GET.get('page')  # Get the page number from the URL query parameter
    page_obj = paginator.get_page(page_number)  # Get the paginated page object

    
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("product_list")  # Redirect to the product list after adding
    else:
        form = ProductForm()





    

    return render(request, 'admin/admin-products.html', {
        'page_obj': page_obj,
        'query': query,
        'category': category,
        'total_strength': total_strength,
        'selected_category': selected_category,
        'min_price': min_price,
        'max_price': max_price,
        "form": form,
        'sort_by': sort_by,
        'products': products,
        'is_blocked': is_blocked,
          # The form for adding or editing products
    })



@user_passes_test(admin_required)
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == "POST":
        # Toggle the blocked status instead of just blocking
        product.is_blocked = not product.is_blocked
        product.save()
        return redirect('product_list')

    return render(request, "admin_panel/delete_product.html", {"product": product})



class ProductVariantCreateView(CreateView):
    model = ProductVariant
    form_class = ProductVariantForm
    template_name = 'admin/add_product_variant.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = get_object_or_404(Product, id=self.kwargs['product_id'])
        return context

    def form_valid(self, form):
        product = get_object_or_404(Product, id=self.kwargs['product_id'])
        form.instance.product = product
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('product_list')  # Redirect to the product list after adding the variant



def editproduct(request, pk):
    product = Product.objects.get(id=pk)
    product_images = product.images.all()
    categories = Category.objects.all()

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            updated_product = form.save(commit=False)

            # Handle image update
            if 'image' in request.FILES:
                updated_product.image = request.FILES['image']

            if 'product_image' in request.FILES:
                ProductImage.objects.create(product=product, image=request.FILES['product_image'])



            updated_product.save()
            return redirect('product_list')
        else:
            print(form.errors)  # Debug: Print form errors in console

    else:
        form = ProductForm(instance=product)

    return render(request, 'admin/editproduct.html', {
        'product': product,
        'product_images': product_images,
        'categories': categories,
        'form': form,
    })

class ProductVariantUpdateView(UpdateView):
    model = ProductVariant
    form_class = ProductVariantForm
    template_name = 'admin/edit_product_variant.html'
    context_object_name = 'variant'

    def get_success_url(self):
        return reverse('editproduct', kwargs={'pk': self.object.product.id})
def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("product_list")  # Redirect to the product list after adding
    else:
        form = ProductForm()

    return render(request, "admin/admin-addproduct.html", {"form": form})


def admin_users(request):
    users = User.objects.all()
    error_message = None
    
    query = request.GET.get('q')  # Get search query from the URL
    if query:
        users = users.filter(
            Q(username__icontains=query) | Q(email__icontains=query)
        ) 
    if request.method == 'POST':
        
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')

        if action == 'delete':
            user = get_object_or_404(User, id=user_id)
            user.delete()
            messages.success(request, "User deleted successfully!")
            return redirect('admin_users')
        elif action == 'softdelete':
            user = get_object_or_404(User, id=user_id)
            user.is_active = False
            user.save()
            messages.success(request, "User blocked successfully!")
            return redirect('admin_users')

        elif action == 'update':
            user = get_object_or_404(User, id=user_id)
            user.username = request.POST.get('username', user.username)
            user.email = request.POST.get('email', user.email)
            password = request.POST.get('password')
            if password:  # Update password only if provided
                user.password = make_password(password)
            user.save()
            messages.success(request, "User updated successfully!")
            return redirect('admin_users')
        
        elif action == 'add_user':
            # Process the form data for adding a user
            username = request.POST['username']
            email = request.POST['email']
            password = request.POST['password']
            confirm_password = request.POST.get('confirm_password')
            
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists.')
            elif password != confirm_password:
                error_message = "Passwords do not match!"
            else:
                User.objects.create(username=username, email=email, password=make_password(password))
                messages.success(request, 'User added successfully!')
            return redirect('admin_users')  # Redirect to the same page      

        

    return render(
    request,
    'admin/admin-users.html',
    {'users': users, 'error_message': error_message,'query': query}
                    )

def manage_orders(request):
    search_query = request.GET.get("search", "").strip()
    orders = Order.objects.all().order_by('-created_at')

    # Filter orders based on search query
    if search_query:
        orders = orders.filter(
            order_unique_id__icontains=search_query
        ) | orders.filter(
            user__username__icontains=search_query
        ) | orders.filter(
            user__email__icontains=search_query
        )

    # Paginate orders (10 per page)
    paginator = Paginator(orders, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    if request.method == "POST":
        order_id = request.POST.get("order_id")
        order = get_object_or_404(Order, id=order_id)
        form = OrderStatusUpdateForm(request.POST, instance=order)
        
        if form.is_valid():
            form.save()
            messages.success(request, f"Order {order.order_unique_id} status updated to {order.status}.")
            return redirect('manage_orders')

    else:
        form = OrderStatusUpdateForm()

    return render(request, "admin/manage_orders.html", {
        "page_obj": page_obj,  
        "form": form,
        "search_query": search_query
    })




def verify_return_request(request, order_id):
    """Redirect admin to the order detail page only if the order is in 'RETURN_REQUESTED' status."""
    order = get_object_or_404(Order, id=order_id)

    
    return redirect(reverse('order_detail_admin', args=[order.id]))

    

def order_detail_admin(request, order_id):
    """Admin order detail page, accessible only for return verification."""
    order = get_object_or_404(Order, id=order_id)

    

    order_items = order.order_items.all()


    return render(request, 'admin/order_detail_admin.html', {
        'order': order,
        'order_items': order_items,
    })

def approve_return_request(request, order_id):
    """Approve return request and update order status to 'RETURN_APPROVED'."""
    order = get_object_or_404(Order, id=order_id)

    if order.status == "RETURN_REQUESTED":
        order.status = "RETURN_APPROVED"
        order.save()
        messages.success(request, f"Return request for Order #{order.order_unique_id} has been approved.")
    else:
        messages.error(request, "Order is not in 'RETURN_REQUESTED' status.")

    return redirect('manage_orders')  # Redirect back to order management


def manage_paidorders(request):
    search_query = request.GET.get("search", "").strip()
    orders = PaymentOrder.objects.exclude(status="PENDING").order_by('-created_at')


    # Filter orders based on search query
    if search_query:
        orders = orders.filter(
            order_unique_id__icontains=search_query
        ) | orders.filter(
            user__username__icontains=search_query
        ) | orders.filter(
            user__email__icontains=search_query
        )

    # Paginate orders (10 per page)
    paginator = Paginator(orders, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    if request.method == "POST":
        order_id = request.POST.get("order_id")
        order = get_object_or_404(PaymentOrder, id=order_id)
        form = PaidOrderStatusUpdateForm(request.POST, instance=order)
        
        if form.is_valid():
            form.save()
            messages.success(request, f"Order {order.order_unique_id} status updated to {order.status}.")
            return redirect('manage_paidorders')

    else:
        form = PaidOrderStatusUpdateForm()

    return render(request, "admin/manage_paidorders.html", {
        "page_obj": page_obj,  
        "form": form,
        "search_query": search_query
    })




def verify_paidreturn_request(request, order_id):
    """Redirect admin to the order detail page only if the order is in 'RETURN_REQUESTED' status."""
    order = get_object_or_404(PaymentOrder, id=order_id)

    
    
    return redirect(reverse('paidorder_detail_admin', args=[order.id]))

def verify_paidcancel_request(request, order_id):
    """Redirect admin to the order detail page only if the order is in 'RETURN_REQUESTED' status."""
    order = get_object_or_404(PaymentOrder, id=order_id)

    
    return redirect(reverse('paidorder_detail_admin', args=[order.id]))


def paidorder_detail_admin(request, order_id):
    """Admin order detail page, accessible only for return verification."""
    order = get_object_or_404(PaymentOrder, id=order_id)

    

    order_items = order.order_items.all()


    return render(request, 'admin/paidorder_detail_admin.html', {
        'order': order,
        'order_items': order_items,
    })

def approve_paid_request(request, order_id):
    """Approve return/cancel request, transfer refund to user's wallet, and update order status."""
    order = get_object_or_404(PaymentOrder, id=order_id)

    if order.status in ["RETURN_REQUESTED", "CANCEL_REQUESTED"]:
        # Get user's wallet (create if not exists)
        wallet, created = Wallet.objects.get_or_create(user=order.user)

        # Determine refund amount
        refund_amount = order.discounted_price if order.discounted_price > 0 else order.total_price

        # Deposit refund into wallet
        wallet.deposit_refund(refund_amount, order)

        # Update order status
        if order.status == "RETURN_REQUESTED":
            order.status = "RETURN_APPROVED"
            messages.success(
                request,
                f"Return approved! ${refund_amount} has been credited to {order.user.username}'s wallet."
            )
        elif order.status == "CANCEL_REQUESTED":
            order.status = "CANCEL_APPROVED"
            messages.success(
                request,
                f"Cancellation approved! ${refund_amount} has been credited to {order.user.username}'s wallet."
            )

        order.save()
    else:
        messages.error(request, "Order is not in a valid status for approval.")

    return redirect('manage_paidorders')  # Redirect to order management


def approve_item_return_request(request, item_id):
    item = get_object_or_404(PaymentOrderItem, id=item_id)

    if item.return_requested:
        # ✅ Mark return as approved
        item.return_approved = True
        item.save()

        # 🎯 Check if the item is a variant and adjust stock
        if item.product_variant:
            variant = item.product_variant
            variant.stock_quantity += item.quantity  # Add the returned quantity to variant stock
            variant.save()
        elif item.product:
            product = item.product
            product.stock_quantity += item.quantity  # Add returned quantity to product stock
            product.save()

        # 💸 Update wallet with 80% of the product price
        total_price = item.get_total_price()
        refund_amount = (total_price * Decimal(0.80)).quantize(Decimal('0.00'), rounding=ROUND_DOWN)

        wallet, created = Wallet.objects.get_or_create(user=item.order.user)

        # 💳 Deposit refund amount to user's wallet
        wallet.deposit(refund_amount, description=f"Refund for returned item: {item.product.name if item.product else item.product_variant.name}")

        messages.success(request, f"✅ Return approved, item marked as returned, stock updated, and ₹{refund_amount} refunded to wallet.")
    else:
        messages.warning(request, "❗ No return requested for this item.")

    # ⏪ Redirect back to the same page
    return redirect(request.META.get('HTTP_REFERER', 'paidorder_detail_admin'))

def approve_postitem_return_request(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id)

    if item.return_requested:
        # ✅ Mark return as approved
        item.return_approved = True
        item.save()

        # 🎯 Check if the item is a variant and adjust stock
        if item.product_variant:
            variant = item.product_variant
            variant.stock_quantity += item.quantity  # Add the returned quantity to variant stock
            variant.save()
        elif item.product:
            product = item.product
            product.stock_quantity += item.quantity  # Add returned quantity to product stock
            product.save()

        messages.success(request, f"✅ Return approved for item: {item.product.name if item.product else item.product_variant.name}. Stock updated successfully.")
    else:
        messages.warning(request, "❗ No return requested for this item.")

    # ⏪ Redirect back to the same page
    return redirect(request.META.get('HTTP_REFERER', 'order_detail_admin'))


def manage_wallets(request):
    """View and manage all user wallets."""
    wallets = Wallet.objects.all()
    return render(request, 'admin/manage_wallets.html', {'wallets': wallets})


def update_wallet_balance(request, wallet_id):
    """Add or deduct balance from a user's wallet."""
    wallet = get_object_or_404(Wallet, id=wallet_id)

    if request.method == "POST":
        try:
            amount = Decimal(request.POST.get("amount", 0))  # Convert input to Decimal
        except ValueError:
            messages.error(request, "Invalid amount entered.")
            return redirect("manage_wallets")

        action = request.POST.get("action")

        if amount <= 0:
            messages.error(request, "Amount must be greater than zero.")
            return redirect("manage_wallets")

        if action == "add":
            wallet.deposit(amount)
            messages.success(request, f"₹{amount} added to {wallet.user.username}'s wallet.")
        elif action == "deduct":
            if wallet.balance >= amount:
                wallet.withdraw(amount)
                messages.success(request, f"₹{amount} deducted from {wallet.user.username}'s wallet.")
            else:
                messages.error(request, "Insufficient balance to deduct.")

        return redirect("manage_wallets")

    return render(request, "admin/update_wallet.html", {"wallet": wallet})

def manage_all_stock(request):
    query = request.GET.get("q", "")  # Get search query
    products = Product.objects.active().order_by('-date')  # Fetch all products

    products_with_prices = []
    for product in products:
        final_price, discount_type = product.calculate_final_price()

        

    if query:
        products = products.filter(Q(name__icontains=query) | Q(category__name__icontains=query))

    if request.method == "POST":
        product_id = request.POST.get("product_id")
        quantity = int(request.POST.get("quantity", 0))
        action = request.POST.get("action")

        product = Product.objects.get(id=product_id)

        if action == "add":
            product.stock_quantity += quantity
            messages.success(request, f"Added {quantity} items to {product.name}'s stock.")
        elif action == "deduct":
            if product.stock_quantity >= quantity:
                product.stock_quantity -= quantity
                messages.success(request, f"Deducted {quantity} items from {product.name}'s stock.")
            else:
                messages.error(request, f"Cannot deduct more than available stock for {product.name}!")
        
        product.save()
        return redirect("manage_all_stock")

    return render(request, "admin/manage_all_stock.html", {"products": products, "query": query})

def coupon_list(request):
    """Admin View to list all coupons"""
    coupons = Coupon.objects.all()
    return render(request, 'admin/coupons_list.html', {'coupons': coupons})

def add_coupon(request):
    """Admin View to create a new coupon"""
    if request.method == "POST":
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Coupon added successfully!")
            return redirect(reverse('coupon_list'))
    else:
        form = CouponForm()
    
    return render(request, 'admin/coupon_form.html', {'form': form, 'title': "Add Coupon"})

def edit_coupon(request, coupon_id):
    """Admin View to edit a coupon"""
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    if request.method == "POST":
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            messages.success(request, "Coupon updated successfully!")
            return redirect(reverse('coupon_list'))
    else:
        form = CouponForm(instance=coupon)
    
    return render(request, 'admin/coupon_form.html', {'form': form, 'title': "Edit Coupon"})

def delete_coupon(request, coupon_id):
    """Admin View to delete a coupon with confirmation in the URL"""
    coupon = get_object_or_404(Coupon, id=coupon_id)

    if "confirm" in request.GET:
        coupon.delete()
        messages.success(request, f"Coupon '{coupon.code}' deleted successfully!")
        return redirect(reverse('adminpanel:coupon_list'))

    messages.warning(request, f"Are you sure you want to delete the coupon '{coupon.code}'? Add '?confirm=yes' to the URL to proceed.")
    return redirect(reverse('adminpanel:coupon_list'))






def manage_offers(request):
    """View to display all products and their offer-related details."""
    products = Product.objects.active().order_by('-date')  # Fetch all products

    products_with_prices = []
    for product in products:
        final_price, discount_type = product.calculate_final_price()

        # Ensure the final price is updated in the database
        if product.price != final_price:
            product.price = final_price
            product.save()

        products_with_prices.append({
            "product": product,
            "final_price": final_price,
            "discount_type": discount_type,
        })

    return render(request, 'admin/manage_offers.html', {
        'products_with_prices': products_with_prices
    })


def toggle_product_sale(request, product_id):
    """Toggles the is_sale field for a product and updates final price."""
    product = get_object_or_404(Product, id=product_id)
    product.is_sale = not product.is_sale  # Toggle sale status

    # Recalculate final price
    product.save()  # This will trigger the `save()` method, updating `price`

    return redirect('manage_offers')


def toggle_sale_price(request, product_id):
    """Updates the sale price for a product and recalculates final price."""
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        sale_price = request.POST.get('sale_price')
        if sale_price:
            product.sale_price = float(sale_price)
            product.save()  # This ensures the final price is updated

    return redirect('manage_offers')

def sales_dashboard(request):
    # Get date range from request parameters or default to last 30 days
    end_date = request.GET.get('end_date')
    start_date = request.GET.get('start_date')
    
    # Parse dates if provided, otherwise use defaults
    today = datetime.now().date()
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            end_date = today
    else:
        end_date = today
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = end_date - timedelta(days=30)
    else:
        start_date = end_date - timedelta(days=30)
    
    # For comparison with previous period
    previous_period_length = (end_date - start_date).days
    previous_start_date = start_date - timedelta(days=previous_period_length)
    previous_end_date = start_date - timedelta(days=1)
    
    # Base query for current period
    current_orders = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
        is_active=True
    )
    
    # Base query for previous period
    previous_orders = Order.objects.filter(
        created_at__date__gte=previous_start_date,
        created_at__date__lte=previous_end_date,
        is_active=True
    )
    
    # Calculate total revenue
    total_revenue = current_orders.aggregate(
        revenue=Sum('total_price')
    )['revenue'] or 0
    
    previous_revenue = previous_orders.aggregate(
        revenue=Sum('total_price')
    )['revenue'] or 0
    
    # Calculate revenue change percentage
    if previous_revenue > 0:
        revenue_change = ((total_revenue - previous_revenue) / previous_revenue) * 100
    else:
        revenue_change = 100  # If no previous revenue, assume 100% increase
    
    # Calculate total orders count
    total_orders = current_orders.count()
    previous_orders_count = previous_orders.count()
    
    # Calculate order change percentage
    if previous_orders_count > 0:
        order_change = ((total_orders - previous_orders_count) / previous_orders_count) * 100
    else:
        order_change = 100  # If no previous orders, assume 100% increase
    
    # Calculate average order value
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    previous_avg_order_value = previous_revenue / previous_orders_count if previous_orders_count > 0 else 0
    
    # Calculate AOV change percentage
    if previous_avg_order_value > 0:
        aov_change = ((avg_order_value - previous_avg_order_value) / previous_avg_order_value) * 100
    else:
        aov_change = 0
    
    # Count delivered orders
    delivered_orders = current_orders.filter(status='DELIVERED').count()
    delivered_ratio = (delivered_orders / total_orders * 100) if total_orders > 0 else 0
    
    # Get recent orders for the table (last 10)
    recent_orders = current_orders.order_by('-created_at')[:10]
    
    # Get revenue trend data for chart
    revenue_trend = current_orders.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        daily_revenue=Sum('total_price')
    ).order_by('date')
    
    # Prepare data for revenue chart
    dates = [item['date'].strftime('%b %d') for item in revenue_trend]
    revenue_data = [float(item['daily_revenue']) for item in revenue_trend]
    
    # Order status distribution for chart
    status_data = list(current_orders.values('status').annotate(
        count=Count('id')
    ).order_by('status'))
    
    status_labels = [dict(Order.STATUS_CHOICES).get(item['status']) for item in status_data]
    status_counts = [item['count'] for item in status_data]
    
    # Top selling products
    top_products = OrderItem.objects.filter(
        order__in=current_orders
    ).values(
        'product', 'product_variant'  # Include product_variant in the query
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(
            F('quantity') * Coalesce(F('product_variant__price'), F('product__price'))
        )
    ).order_by('-total_quantity')[:8]
    
    # Add product and product_variant details to top products
    for item in top_products:
        try:
            item['product'] = Product.objects.get(pk=item['product'])
        except Product.DoesNotExist:
            item['product'] = None  # Handle missing products gracefully
        
        try:
            item['product_variant'] = ProductVariant.objects.get(pk=item['product_variant'])
        except ProductVariant.DoesNotExist:
            item['product_variant'] = None  # Handle missing variants gracefully
    
    # Prepare context with all data
    context = {
        'total_revenue': total_revenue,
        'revenue_change': revenue_change,
        'total_orders': total_orders,
        'order_change': order_change,
        'avg_order_value': avg_order_value,
        'aov_change': aov_change,
        'delivered_orders': delivered_orders,
        'delivered_ratio': delivered_ratio,
        'recent_orders': recent_orders,
        'top_products': top_products,
        
        # Chart data as JSON for JavaScript
        'dates_json': json.dumps(dates),
        'revenue_data_json': json.dumps(revenue_data),
        'status_labels_json': json.dumps(status_labels),
        'status_data_json': json.dumps(status_counts),
    }
    context['revenue_change'] = abs(context['revenue_change'])
    
    return render(request, 'admin/sales_dashboard.html', context)

def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse('Error generating PDF', status=400)


def sales_report_pdf(request):
    # Get date range from request parameters or default to last 30 days
    end_date = request.GET.get('end_date')
    start_date = request.GET.get('start_date')
    
    # Parse dates if provided, otherwise use defaults
    today = datetime.now().date()
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            end_date = today
    else:
        end_date = today
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = end_date - timedelta(days=30)
    else:
        start_date = end_date - timedelta(days=30)
    
    # Base query for current period
    orders = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
        is_active=True
    )
    
    # Calculate summary metrics
    total_revenue = orders.aggregate(revenue=Sum('total_price'))['revenue'] or 0
    total_orders = orders.count()
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    delivered_orders = orders.filter(status='DELIVERED').count()
    delivered_ratio = (delivered_orders / total_orders * 100) if total_orders > 0 else 0
    
    # Get order status distribution
    status_distribution = orders.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Convert status codes to display names
    status_choices_dict = dict(Order.STATUS_CHOICES)
    for item in status_distribution:
        item['status_display'] = status_choices_dict.get(item['status'])
        item['percentage'] = (item['count'] / total_orders * 100) if total_orders > 0 else 0
    
    # Get top products and variants
    top_items = OrderItem.objects.filter(
        order__in=orders
    ).values(
        'product', 'variant'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('price'))
    ).order_by('-total_quantity')[:10]
    
    # Add product and variant details to top items
    top_products_with_variants = []
    for item in top_items:
        product = Product.objects.get(pk=item['product'])
        variant = None
        if item['variant']:
            variant = ProductVariant.objects.get(pk=item['variant'])
        
        top_products_with_variants.append({
            'product': product,
            'variant': variant,
            'total_quantity': item['total_quantity'],
            'total_revenue': item['total_revenue']
        })
    
    # Daily revenue breakdown
    daily_revenue = orders.values('created_at__date').annotate(
        date=F('created_at__date'),
        revenue=Sum('total_price')
    ).order_by('date')
    
    # Prepare context
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'report_generated': datetime.now(),
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'avg_order_value': avg_order_value,
        'delivered_orders': delivered_orders,
        'delivered_ratio': delivered_ratio,
        'status_distribution': status_distribution,
        'top_products_with_variants': top_products_with_variants,  # Changed this line
        'daily_revenue': daily_revenue
    }
    
    # Generate PDF
    pdf = render_to_pdf('admin/sales_report_pdf.html', context)
    
    # Set filename for download
    filename = f"Sales_Report_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.pdf"
    pdf['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return pdf



def paidsales_dashboard(request):
    # Get date range from request parameters or default to last 30 days
    end_date = request.GET.get('end_date')
    start_date = request.GET.get('start_date')
    
    # Parse dates if provided, otherwise use defaults
    today = datetime.now().date()
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            end_date = today
    else:
        end_date = today
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = end_date - timedelta(days=30)
    else:
        start_date = end_date - timedelta(days=30)
    
    # For comparison with previous period
    previous_period_length = (end_date - start_date).days
    previous_start_date = start_date - timedelta(days=previous_period_length)
    previous_end_date = start_date - timedelta(days=1)
    
    # Base query for current period
    current_orders = PaymentOrder.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
        is_active=True
    )
    
    # Base query for previous period
    previous_orders = PaymentOrder.objects.filter(
        created_at__date__gte=previous_start_date,
        created_at__date__lte=previous_end_date,
        is_active=True
    )
    
    # Calculate total revenue
    total_revenue = current_orders.aggregate(
        revenue=Sum('total_price')
    )['revenue'] or 0
    
    previous_revenue = previous_orders.aggregate(
        revenue=Sum('total_price')
    )['revenue'] or 0
    
    # Calculate revenue change percentage
    if previous_revenue > 0:
        revenue_change = ((total_revenue - previous_revenue) / previous_revenue) * 100
    else:
        revenue_change = 100  # If no previous revenue, assume 100% increase
    
    # Calculate total orders count
    total_orders = current_orders.count()
    previous_orders_count = previous_orders.count()
    
    # Calculate order change percentage
    if previous_orders_count > 0:
        order_change = ((total_orders - previous_orders_count) / previous_orders_count) * 100
    else:
        order_change = 100  # If no previous orders, assume 100% increase
    
    # Calculate average order value
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    previous_avg_order_value = previous_revenue / previous_orders_count if previous_orders_count > 0 else 0
    
    # Calculate AOV change percentage
    if previous_avg_order_value > 0:
        aov_change = ((avg_order_value - previous_avg_order_value) / previous_avg_order_value) * 100
    else:
        aov_change = 0
    
    # Count delivered orders
    delivered_orders = current_orders.filter(status='DELIVERED').count()
    delivered_ratio = (delivered_orders / total_orders * 100) if total_orders > 0 else 0
    
    # Get recent orders for the table (last 10)
    recent_orders = current_orders.order_by('-created_at')[:10]
    
    # Get revenue trend data for chart
    revenue_trend = current_orders.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        daily_revenue=Sum('total_price')
    ).order_by('date')
    
    # Prepare data for revenue chart
    dates = [item['date'].strftime('%b %d') for item in revenue_trend]
    revenue_data = [float(item['daily_revenue']) for item in revenue_trend]
    
    # Order status distribution for chart
    status_data = list(current_orders.values('status').annotate(
        count=Count('id')
    ).order_by('status'))
    
    status_labels = [dict(PaymentOrder.STATUS_CHOICES).get(item['status']) for item in status_data]
    status_counts = [item['count'] for item in status_data]
    
    # Top selling products
    top_products = PaymentOrderItem.objects.filter(
        order__in=current_orders
    ).values(
        'product', 'product_variant'  # Include product_variant in the query
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(
            F('quantity') * Coalesce(F('product_variant__price'), F('product__price'))
        )
    ).order_by('-total_quantity')[:8]
    
    # Add product and product_variant details to top products
    for item in top_products:
        try:
            item['product'] = Product.objects.get(pk=item['product'])
        except Product.DoesNotExist:
            item['product'] = None  # Handle missing products gracefully
        
        try:
            item['product_variant'] = ProductVariant.objects.get(pk=item['product_variant'])
        except ProductVariant.DoesNotExist:
            item['product_variant'] = None  # Handle missing variants gracefully
    
    # Prepare context with all data
    context = {
        'total_revenue': total_revenue,
        'revenue_change': revenue_change,
        'total_orders': total_orders,
        'order_change': order_change,
        'avg_order_value': avg_order_value,
        'aov_change': aov_change,
        'delivered_orders': delivered_orders,
        'delivered_ratio': delivered_ratio,
        'recent_orders': recent_orders,
        'top_products': top_products,
        
        # Chart data as JSON for JavaScript
        'dates_json': json.dumps(dates),
        'revenue_data_json': json.dumps(revenue_data),
        'status_labels_json': json.dumps(status_labels),
        'status_data_json': json.dumps(status_counts),
    }

    return render(request, 'admin/paidsales_dashboard.html', context)


def update_all_variant_prices(request):
    """Update all variant prices based on the proportion of product price and price_initial."""
    if request.method == "POST":
        try:
            # Get all products with variants
            products = Product.objects.all()
            updated_count = 0  # Track the number of variants updated

            for product in products:
                # Ensure price_initial is greater than 0 to avoid division by zero
                if product.price_initial > 0:
                    price_ratio = Decimal(product.price) / Decimal(product.price_initial)
                else:
                    price_ratio = Decimal(1)  # Default ratio if price_initial is 0

                # Update all variants of the product
                variants = ProductVariant.objects.filter(product=product)
                for variant in variants:
                    # Only update if variant.price_initial is set
                    if variant.price_initial and variant.price_initial > 0:
                        # Apply ratio to variant's price_initial
                        new_price = variant.price_initial * price_ratio
                        variant.price = new_price.quantize(Decimal("0.01"))  # Round to 2 decimal places
                        variant.save()
                        updated_count += 1

            return JsonResponse({
                "success": True,
                "message": f" Variant(s) Prices updated successfully!"
            })
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Error: {str(e)}"})
    else:
        return JsonResponse({"success": False, "message": "Invalid request."})
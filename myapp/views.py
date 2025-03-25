from django.shortcuts import render
from .models import Category,Product,ProductImage,ProductVariant
from django.db.models import Q
from django.db.models.functions import Lower
from django.core.paginator import Paginator
from collections import defaultdict

# Create your views here.





def home(request):
    category = Category.objects.all()
    product = Product.objects.active()
    newproduct = Product.objects.active().order_by('-date')[:10]

    return render(request, 'home.html', {  
        'category': category,
        'product': product,
        'newproduct':newproduct
    })


def product(request, pk):
    product = Product.objects.get(id=pk)
    product_images = product.images.all()
    variants = ProductVariant.objects.filter(product=product)
    variant_id = request.GET.get('variant_id', None)

    # Fetch related products and include variants
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    
    # Prepare related variants as a list of tuples (product, variant_list)
    related_products_with_variants = []
    for related_product in related_products:
        related_variants = ProductVariant.objects.filter(product=related_product)
        related_products_with_variants.append({
            'product': related_product,
            'variants': related_variants
        })

    return render(request, 'product.html', {
        'product': product,
        'product_images': product_images,
        'related_products_with_variants': related_products_with_variants,
        'variants': variants,
        'selected_variant_id': variant_id,
    })
def shop(request):
    # Initial query for products and categories
    product = Product.objects.active()
    category = Category.objects.all()
    
    # Get query parameters from the request
    query = request.GET.get('q')
    selected_category = str(request.GET.get('category', 'all'))

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort_by')
    
    # Search functionality
    if query:
        product = product.filter(
            Q(name__icontains=query) |  
            Q(category__name__icontains=query)  # Search by category name
        )

    # Category filter
    if selected_category and selected_category != "all":
        try:
            selected_category = int(selected_category)  # Convert to int
            product = product.filter(category__id=selected_category)
        except ValueError:
            pass  # Ignore invalid category values

    # Price filters
    if min_price:
        product = product.filter(price__gte=min_price)

    if max_price:
        product = product.filter(price__lte=max_price)
    
    # Sorting functionality
    if sort_by == "price_asc":
        product = product.order_by("price")
    elif sort_by == "price_desc":
        product = product.order_by("-price")
    elif sort_by == "name_asc":
        product = product.order_by(Lower("name"))
    elif sort_by == "name_desc":
        product = product.order_by(Lower("name").desc())
    else:
        product = product.order_by('-date')
    
    total_strength = product.count()

    # Pagination
    paginator = Paginator(product, 16)  # Show 16 products per page
    page_number = request.GET.get('page')  # Get the page number from the URL query parameter
    page_obj = paginator.get_page(page_number)  # Get the paginated page object

    return render(request, 'shop.html', {
        'page_obj': page_obj,
        'query': query,
        'category': category,
        'total_strength': total_strength,
        'selected_category': selected_category,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
    })

def login(request):
    return render(request,'login.html')

def category(request,pk):
    category = Category.objects.get(id=pk)  # Get the category based on the provided pk
    products = Product.objects.filter(category=category)  # Filter products by the category
    
    
    return render(request,'category.html',{'products':products,'category':category})

def about(request):
    return render(request,'about.html')
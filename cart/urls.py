
from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    
    path('cart/', views.view_cart, name='view_cart'),
    path('addtocart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),  # For product without variant
    path('addtocart/<int:product_id>/<int:variant_id>/', views.add_to_cart, name='add_to_cart_variant'),  # For product with variant
    path('updatecart/', views.update_cart, name='update_cart'),
    path('removefromcart/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('apply_coupon/', views.apply_coupon, name='apply_coupon'),
    path("remove_coupon/", views.remove_coupon, name="remove_coupon"),

    path('wishlist/', views.view_wishlist, name='view_wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove-from-wishlist/<int:item_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('list-to-cart/<int:item_id>/', views.list_to_cart, name='list_to_cart'),
    path('add-to-wishlist/<int:product_id>/', views.shop_to_wishlist, name='shop_to_wishlist'),
    
    

]

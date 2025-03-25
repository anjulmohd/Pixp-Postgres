from django.urls import path
from . import views
from .views import ProductVariantCreateView,ProductVariantUpdateView
urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    path('product_list/', views.product_list, name='product_list'),
    path('editproduct/<int:pk>',views.editproduct,name='editproduct'),
    path('product-variant/<int:pk>/edit/', ProductVariantUpdateView.as_view(), name='edit_product_variant'),

    path('product/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('product/add', views.add_product, name='add_product'),
    path('users/', views.admin_users, name='admin_users'),
    path("orders/", views.manage_orders, name="manage_orders"),
    path('paidorders/<int:order_id>/return/', views.paidorder_detail_admin, name='paidorder_detail_admin'),
    path("manage-category/", views.manage_category, name="manage_category"),
    path("delete-category/<int:category_id>/", views.delete_category, name="delete_category"),
    path('category/toggle-sale/<int:category_id>/', views.toggle_sale, name='toggle_sale'),
    path('category/update-discount/<int:category_id>/', views.update_discount, name='update_discount'),

    path('orders/<int:order_id>/verify/', views.verify_return_request, name='verify_return_request'),



    path("paidorders/", views.manage_paidorders, name="manage_paidorders"),
    path('paidorders/<int:order_id>/verify/', views.verify_paidreturn_request, name='verify_paidreturn_request'),
    path('paidorders/<int:order_id>/verify/', views.verify_paidcancel_request, name='verify_paidcancel_request'),
    path('paidorders/<int:order_id>/approve-return/', views.approve_paid_request, name='approve_paid_request'),
    path('approve-return-for-item/<int:item_id>/', views.approve_item_return_request, name='approve_item_return_request'),
    path('approve-post-return-for-item/<int:item_id>/', views.approve_postitem_return_request, name='approve_postitem_return_request'),
    path('orders/<int:order_id>/return/', views.order_detail_admin, name='order_detail_admin'),
    
    path('orders/<int:order_id>/approve-return/', views.approve_return_request, name='approve_return_request'),

    path("manage-wallets/", views.manage_wallets, name="manage_wallets"),
    path("update-wallet/<int:wallet_id>/", views.update_wallet_balance, name="update_wallet_balance"),

    path('manage-all-stock/', views.manage_all_stock, name="manage_all_stock"),

    path('coupons/', views.coupon_list, name='coupon_list'),
    path('coupons/add/', views.add_coupon, name='add_coupon'),
    path('coupons/edit/<int:coupon_id>/', views.edit_coupon, name='edit_coupon'),
    path('coupons/delete/<int:coupon_id>/', views.delete_coupon, name='delete_coupon'),

    path('manage-offers/', views.manage_offers, name='manage_offers'),
    path('toggle-product-sale/<int:product_id>/', views.toggle_product_sale, name='toggle_product_sale'),
    path('toggle-sale-price/<int:product_id>/', views.toggle_sale_price, name='toggle_sale_price'),

    path('sales-dashboard/', views.sales_dashboard, name='sales_dashboard'),
    path('sales-report-pdf/', views.sales_report_pdf, name='sales_report_pdf'),

    path('paidsales-dashboard/', views.paidsales_dashboard, name='paidsales_dashboard'),

    path('product/<int:product_id>/add-variant/', ProductVariantCreateView.as_view(), name='add_product_variant'),
     path('update-all-variant-prices/', views.update_all_variant_prices, name='update_all_variant_prices'),

]

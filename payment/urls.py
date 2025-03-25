from django.urls import path

from . import views

urlpatterns = [
    path('paymentorder/', views.place_paymentorder, name='place_paymentorder'),
    path("success/<int:order_id>/", views.order_success, name="order_success"),
    path("failed/", views.order_failed, name="order_failed"),
    path('verify_payment/', views.verify_payment, name='verify_payment'),
    path('invoicepaid/<int:order_id>/', views.generate_invoice_paid_pdf, name='generate_invoice_paid_pdf'),
    path('paidcancel/<int:order_id>/', views.cancel_paidorder, name='cancel_paidorder'),
    path('paidreturn/<int:order_id>/', views.return_paidorder, name='return_paidorder'),
    path("wallet/", views.wallet_detail, name="wallet_detail"),
    path('toggle-return-request/<int:item_id>/', views.toggle_return_request, name='toggle_return_request'),
    
    path('wallet/create-razorpay-order/', views.create_razorpay_order, name='create_razorpay_order'),  # Create order
    path('wallet/razorpay-success/', views.razorpay_success, name='razorpay_success'),  # Payment success
    
    path('place-order-wallet/', views.place_order_wallet, name='place_order_wallet'),
]

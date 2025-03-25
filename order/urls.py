from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    
    path('checkout/', views.checkout, name='checkout'),
    path('payment/', views.payment, name='payment'),  # Add this line

    path('placeorder/',views.place_order,name="place_order"),
    path('details/<int:order_id>/',views.order_detail,name="order_detail"),
    path('my-orders/', views.order_list, name='order_list'),
    path('cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path("<int:order_id>/return/", views.return_order, name="return_order"),
    path('<int:order_id>/invoice/', views.generate_invoice_pdf, name='generate_invoice_pdf'),
    
    path('toggle-post-return-request/<int:item_id>/', views.toggle_postreturn_request, name='toggle_postreturn_request'),
    

]
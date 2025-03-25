
from django.urls import path
from . import views


urlpatterns = [
 path('',views.profile_view,name='profile_view'),
 
path('addresses/add/', views.add_address, name='add_address'),
path('addresses/edit/<int:address_id>/', views.edit_address, name='edit_address'),
path('addresses/delete/<int:address_id>/', views.delete_address, name='delete_address'),

path('upload_profile/',views.upload_profile_picture,name='upload_profile'),

path('referral/', views.show_or_create_referral, name='show_referral'),
path('apply-referral/', views.apply_referral_code, name='apply_referral'),
path('referralpage/', views.referralpage, name='referral'),


 

]
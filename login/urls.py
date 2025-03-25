
from django.urls import path,include
from . import views
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required




urlpatterns = [
 path('',views.login_view,name='login'),
path('logout/', views.user_logout, name='logout'),
path('register/', views.user_register,name='register'),

path('verify/', views.verify_otp, name='verify_otp'),
path('resend-otp/', views.resend_otp, name='resend_otp'),

 path('google-login/', views.google_redirect, name='google-login'),

 
  path("forgot-password/", views.request_reset_otp, name="request_reset_otp"),
    path("verify-otp/<str:email>/", views.verify_reset_otp, name="verify_reset_otp"),
    path("reset-password/<str:email>/", views.reset_password, name="reset_password")



 
]

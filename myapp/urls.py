
from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
 path('',views.home,name='home'),
path('product/<int:pk>',views.product,name='product'),
path('category/<int:pk>',views.category,name='category'),
path('shop/',views.shop,name='shop'),

path('about/',views.about,name='about')

 

]





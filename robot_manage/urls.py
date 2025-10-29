#from django.contrib import admin
from django.urls import path, include
from robot_manage import views as robot_views

urlpatterns = [
    path('admin/robot', robot_views.admin, name='login'),
    
]

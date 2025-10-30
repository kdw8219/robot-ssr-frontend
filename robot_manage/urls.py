#from django.contrib import admin
from django.urls import path, include
from robot_manage import views as robot_views

urlpatterns = [
    path('robot/management/', robot_views.admin, name='login'),
    
]

#from django.contrib import admin
from django.urls import path, include
from robot_manage import views as robot_views

urlpatterns = [
    path('robots/management/', robot_views.signup, name='robot_signup'),
    path('robots', robot_views.getAll, name='robot_getter'),
]

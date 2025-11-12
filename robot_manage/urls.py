#from django.contrib import admin
from django.urls import path, include
from robot_manage import views as robot_views

urlpatterns = [
    path('robots/management/', robot_views.signup, name='robot_signup'),
    path('robots', robot_views.handling_robots, name='robot_getter'),
    path('robots/<robot_id>/', robot_views.modifying_robots, name='robot_modifier'),
    path('robots/detail/<robot_id>/', robot_views.detail_view_robots, name='robot_details')
]

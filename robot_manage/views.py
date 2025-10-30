from django.shortcuts import render
from django.http import HttpResponse
from auth_service_handler.decorator import jwt_required

def HTMLRenderer(request, template_name='user_manage/index.html', params={}):
    return render(request, template_name, params)

@jwt_required
def admin(request):
    return HttpResponse(HTMLRenderer(request, 'robot_manage/robot_manage.html', params={}))
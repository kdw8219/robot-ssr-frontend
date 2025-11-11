import pytest
import httpx
import os
from django.urls import reverse
from unittest.mock import patch
from django.contrib.messages import get_messages

@pytest.mark.django_db
@pytest.mark.asyncio
@patch("robot_manage.views.httpx.AsyncClient.post")
async def test_signup_success(mock_post, async_client, settings):
    # .env 대신 환경 변수 직접 지정
    settings.ROBOT_SERVICE_URL = "http://fake-robot-service/api/register"

    # Mock httpx 응답 객체
    mock_response = httpx.Response(
        status_code=200,
        json={"result": "success"}
    )
    mock_post.return_value = mock_response

    # 실제 요청 시뮬레이션
    data = {
        "robot_id": "R001",
        "model": "X200",
        "firmware": "TestBot",
        "location": "Seoul",
    }

    url = reverse("/robots/management/") 
    response = await async_client.post(url, data=data)

    assert response.status_code == 302  # redirect
    assert response.headers["Location"] == "/robots/management/"
    mock_post.assert_called_once()  # 외부 호출 확인

# -------------------------------

@pytest.mark.django_db
@pytest.mark.asyncio
@patch("robot_manage.views.httpx.AsyncClient.post")
async def test_signup_conflict(mock_post, async_client, settings):
    settings.ROBOT_SERVICE_URL = "http://fake-robot-service/api/register"

    mock_response = httpx.Response(
        status_code=409,
        json={"detail": "duplicate"}
    )
    mock_post.return_value = mock_response

    data = {"robot_id": "R001"
            ,"model": "X200"
            ,"firmware": "TestBot"
            ,"location": "Seoul",}
    url = reverse("signup")

    response = await async_client.post(url, data=data)

    assert response.status_code == 302
    assert response.headers["Location"] == "/robots/management/"

    # Django messages framework 확인
    messages = [msg.message for msg in get_messages(response.wsgi_request)]
    assert "이미 등록된 로봇입니다." in messages

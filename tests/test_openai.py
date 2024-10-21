# tests/test_openai.py

import sys
import os
import pytest
import asyncio
from httpx import AsyncClient
from unittest.mock import Mock
from fastapi import status

# 프로젝트의 루트 디렉토리를 모듈 검색 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # FastAPI 앱이 정의된 모듈을 임포트합니다.

pytestmark = pytest.mark.asyncio

@pytest.mark.asyncio
async def test_create_thread():
    """
    채팅방 생성 엔드포인트를 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "crop": "토마토",
            "address": "서울특별시 강남구"
        }
        response = await ac.post("/threads/", json=payload)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "threadId" in data
        return data["threadId"]  # 다음 테스트에서 사용할 수 있도록 threadId 반환


@pytest.mark.asyncio
async def test_get_thread():
    """
    채팅방 조회 엔드포인트를 테스트합니다.
    """
    # 먼저 채팅방을 생성합니다.
    thread_id = await test_create_thread()
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get(f"/threads/{thread_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["threadId"] == thread_id
        assert "messages" in data


# 1. 정상 메시지 전송 테스트
@pytest.mark.asyncio
async def test_send_message_success():
    """
    정상적인 메시지 전송 및 AI 응답 생성 테스트
    """
    thread_id = await test_create_thread()
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "threadId": thread_id,
            "message": "오늘 날씨는 어떤가요?"
        }
        response = await ac.post("/threads/message", json=payload)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["threadId"] == thread_id
        assert "message" in data


# 2. 채팅방 ID 누락 테스트
@pytest.mark.asyncio
async def test_send_message_missing_thread_id():
    """
    채팅방 ID가 누락된 경우 400 Bad Request 반환
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "threadId": '',  # 누락된 채팅방 ID
            "message": "오늘 날씨는 어떤가요?"
        }
        response = await ac.post("/threads/message", json=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "채팅방 ID가 누락되었습니다." in data["detail"]


# 3. AI 응답 생성 실패 테스트
@pytest.mark.asyncio
async def test_send_message_ai_response_failed(mocker):
    """
    AI 응답 생성 실패 시 502 Bad Gateway 반환
    """
    thread_id = await test_create_thread()

    # AI 응답 생성 실패 상황 모의(mock)
    mock_run_status = Mock()
    mock_run_status.status = "failed"
    mock_run_status.last_error = "AI 응답 실패"

    mocker.patch("app.api.openai.openai.client.beta.threads.runs.retrieve",
                 return_value=mock_run_status)

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "threadId": thread_id,
            "message": "오늘 날씨는 어떤가요?"
        }
        response = await ac.post("/threads/message", json=payload)
        assert response.status_code == status.HTTP_502_BAD_GATEWAY
        data = response.json()
        assert "응답 생성에 실패했습니다" in data["detail"]


# 4. AI 응답 생성 취소 테스트
@pytest.mark.asyncio
async def test_send_message_ai_response_cancelled(mocker):
    """
    AI 응답 생성이 취소된 경우 409 Conflict 반환
    """
    thread_id = await test_create_thread()

    # AI 응답 생성 실패 상황 모의(mock)
    mock_run_status = Mock()
    mock_run_status.status = "cancelled"
    mock_run_status.last_error = "AI 응답 취소됨"

    mocker.patch("app.api.openai.openai.client.beta.threads.runs.retrieve",
                 return_value=mock_run_status)

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "threadId": thread_id,
            "message": "오늘 날씨는 어떤가요?"
        }
        response = await ac.post("/threads/message", json=payload)
        assert response.status_code == status.HTTP_409_CONFLICT
        data = response.json()
        assert "응답 생성이 취소되었습니다" in data["detail"]


# 5. 응답 생성 시간 초과 테스트
@pytest.mark.asyncio
async def test_send_message_ai_response_timeout(mocker):
    """
    AI 응답 생성 시간 초과 시 408 Request Timeout 반환
    """
    thread_id = await test_create_thread()

    # AI 응답 생성 시간 초과 상황 모의(mock)
    mock_run_status = Mock()
    mock_run_status.status = "expired"
    mock_run_status.last_error = "응답 생성 시간 초과"

    mocker.patch("app.api.openai.openai.client.beta.threads.runs.retrieve",
                 return_value=mock_run_status)
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "threadId": thread_id,
            "message": "오늘 날씨는 어떤가요?"
        }
        response = await ac.post("/threads/message", json=payload)
        assert response.status_code == status.HTTP_408_REQUEST_TIMEOUT
        data = response.json()
        assert "응답 생성이 시간 초과되었습니다" in data["detail"]


# 6. AI 응답 없음 테스트
@pytest.mark.asyncio
async def test_send_message_no_ai_response(mocker):
    """
    AI 응답이 없는 경우 204 No Content 반환
    """
    thread_id = await test_create_thread()

    # AI 응답이 비어 있는 상황 모의(mock)
    mock_run_status = Mock()
    mock_run_status.data = []

    mocker.patch("app.api.openai.openai.client.beta.threads.messages.list",
                 return_value=mock_run_status)

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "threadId": thread_id,
            "message": "오늘 날씨는 어떤가요?"
        }
        response = await ac.post("/threads/message", json=payload)
        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_delete_thread():
    """
    채팅방 삭제 엔드포인트를 테스트합니다.
    """
    # 채팅방 생성
    thread_id = await test_create_thread()
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.delete(f"/threads/{thread_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # 삭제된 채팅방 조회 시도
        response = await ac.get(f"/threads/{thread_id}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

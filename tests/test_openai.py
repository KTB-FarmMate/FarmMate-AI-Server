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

URI = "/members/memberid_1234"


## 채팅방 생성 관련 테스트

# 1. 정상적인 채팅방 생성
@pytest.mark.asyncio
async def test_create_thread():
    """
    모든 필드가 올바르게 입력된 경우 정상적인 생성이 이루어지는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "crop": "토마토",
            "address": "서울특별시 강남구"
        }
        response = await ac.post(f"{URI}/threads/", json=payload)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "threadId" in data
        return data["threadId"]  # 다음 테스트에서 사용할 수 있도록 threadId 반환


# 2. 필수 필드 누락 (작물명)
@pytest.mark.asyncio
async def test_create_thread_missing_crop():
    """
    crop 필드가 비어있거나 누락된 경우 에러가 발생하는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "crop": "",
            "address": "서울특별시 강남구"
        }
        response = await ac.post(f"{URI}/threads/", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["detail"][0]["type"] == "value_error"


# 3. 필수 필드 누락 (주소지)
@pytest.mark.asyncio
async def test_create_thread_missing_address():
    """
    address 필드가 비어있거나 누락된 경우 에러가 발생하는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "crop": "토마토",
            "address": ""
        }
        response = await ac.post(f"{URI}/threads/", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["detail"][0]["type"] == "value_error"


# 4. 올바르지 않은 필드 값
@pytest.mark.asyncio
async def test_create_thread_not_valid():
    """
    crop 또는 address에 예상하지 못한 형식(숫자나 특수 문자 등)이 입력된 경우 어떻게 처리되는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "crop": "!!!!!@",
            "address": "👾👾!@👾👨‍👨‍❤️‍🐤👨🦽‍➡️🦿🥰#"
        }
        response = await ac.post(f"{URI}/threads/", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["detail"][0]["type"] == "value_error"


# 5. 중복된 요청

# ----------------------------------------------------#

## 채팅방 조회 관련 테스트

# 1. 정상적인 채팅방 조회
@pytest.mark.asyncio
async def test_get_thread():
    """
    존재하는 채팅방 ID를 사용하여 정상적으로 조회되는지 테스트합니다.
    """
    # 먼저 채팅방을 생성합니다.
    thread_id = await test_create_thread()
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get(f"{URI}/threads/{thread_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["threadId"] == thread_id
        assert "messages" in data


# 2. 존재하지 않는 채팅방 조회
@pytest.mark.asyncio
async def test_get_none_thread():
    """
    잘못된 또는 존재하지 않는 채팅방 ID로 조회했을 때 적절한 에러가 반환되는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get(f"{URI}/threads/NoneThreadID")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "유효하지 않은 채팅방 ID입니다." in data["detail"]


# 3. 잘못된 형식의 채팅방 ID 조회
@pytest.mark.asyncio
async def test_get_incorrect_format_thread():
    """
    형식이 잘못된(특수 문자, 빈 값 등) ID로 조회했을 때 어떻게 처리되는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get(f"{URI}/threads/😆😆😆😆")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["detail"] == "유효하지 않은 채팅방 ID입니다."


# -------------------------------------------------- #

## 메시지 전송 관련 테스트

# 1. 정상적인 메시지 전송
@pytest.mark.asyncio
async def test_send_message_success():
    """
    올바른 threadId와 메시지를 전송하여 AI 응답이 올바르게 생성되는지 테스트합니다.
    """
    thread_id = await test_create_thread()
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "threadId": thread_id,
            "message": "오늘 날씨는 어떤가요?"
        }
        response = await ac.post(f"{URI}/threads/message", json=payload)
        assert response.status_code == status.HTTP_200_OK


# 2. 채팅방 ID 누락
@pytest.mark.asyncio
async def test_send_message_missing_thread_id():
    """
    threadId가 없을 경우 에러가 발생하는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "threadId": '',  # 누락된 채팅방 ID
            "message": "오늘 날씨는 어떤가요?"
        }
        response = await ac.post(f"{URI}/threads/message", json=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "채팅방 ID가 누락되었습니다." in data["detail"]


# 3. 채팅방 메시지 누락
@pytest.mark.asyncio
async def test_send_message_missing_message():
    """
    threadId가 없을 경우 에러가 발생하는지 테스트합니다.
    """
    thread_id = await test_create_thread()
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "threadId": thread_id,  # 누락된 채팅방 ID
            "message": ""
        }
        response = await ac.post(f"{URI}/threads/message", json=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "메시지가 누락되었습니다." in data["detail"]


# 4. 존재하지 않는 채팅방으로 메시지 전송
@pytest.mark.asyncio
async def test_send_message_none_thread():
    """
    존재하지 않는 threadId로 메시지를 보낼 때 올바른 에러가 반환되는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "threadId": "NoneThreadID",
            "message": "오늘 날씨는 어떤가요?"
        }
        response = await ac.post(f"{URI}/threads/message", json=payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "올바르지 않은 ThreadId 입니다." in data["detail"]


# ----------------------------------------------------- #

## 채팅방 수정 관련 테스트

# 1. 정상적인 주소 변경
@pytest.mark.asyncio
async def test_modify_message_success():
    """
    정상적인 thread_id 와 address로 정상적으로 적용되는지 테스트합니다.
    """
    thread_id = await test_create_thread()
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "address" : "경기 성남시 분당구 대왕판교로 660 유스페이스1 A동 405호"
        }
        response = await ac.patch(f"{URI}/threads/{thread_id}", json=payload)
        assert response.status_code == status.HTTP_200_OK


# 2. 변경 주소 누락

# 3. 올바르지 않은 thread_id

# ----------------------------------------------------- #

## 채팅방 삭제 관련 테스트

# 1. 정상적인 채팅방 삭제
@pytest.mark.asyncio
async def test_delete_thread():
    """
    존재하는 threadId를 사용하여 정상적으로 채팅방을 삭제했을 때 올바른 응답이 반환되는지 테스트합니다.
    """
    # 채팅방 생성
    thread_id = await test_create_thread()
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.delete(f"{URI}/threads/{thread_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT


# 2. 존재하지 않는 채팅방 삭제
@pytest.mark.asyncio
async def test_delete_thread():
    """
    잘못된 threadId로 삭제 요청을 보냈을 때 적절한 에러가 반환되는지 테스트합니다
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.delete(f"{URI}/threads/NoneThreadID")
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ------------------------------------------------ #

## AI 응답 생성 관련 테스트

# 1. AI 응답 성공
@pytest.mark.asyncio
async def test_send_message_ai_response_success():
    """
    정상적인 메시지를 보낸 후 AI 응답이 정상적으로 생성되는지 테스트합니다.
    """
    thread_id = await test_create_thread()

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "threadId": thread_id,
            "message": "오늘 날씨는 어떤가요?"
        }
        response = await ac.post(f"{URI}/threads/message", json=payload)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] is not None


# 2. AI 응답 실패 (시스템 문제)
@pytest.mark.asyncio
async def test_send_message_ai_response_failed(mocker):
    """
    AI 시스템이 응답을 생성하지 못했을 때 502 에러가 발생하는지 테스트합니다.
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
        response = await ac.post(f"{URI}/threads/message", json=payload)
        assert response.status_code == status.HTTP_502_BAD_GATEWAY
        data = response.json()
        assert "응답 생성에 실패했습니다" in data["detail"]


# 3. AI 응답 생성 취소
@pytest.mark.asyncio
async def test_send_message_ai_response_cancelled(mocker):
    """
     AI 응답이 중간에 취소되었을 때 409 에러가 반환되는지 테스트합니다.
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
        response = await ac.post(f"{URI}/threads/message", json=payload)
        assert response.status_code == status.HTTP_409_CONFLICT
        data = response.json()
        assert "응답 생성이 취소되었습니다" in data["detail"]


# 4. AI 응답 시간 초과
@pytest.mark.asyncio
async def test_send_message_ai_response_timeout(mocker):
    """
    응답 생성에 너무 오래 걸렸을 때 408 에러가 발생하는지 테스트합니다.
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
        response = await ac.post(f"{URI}/threads/message", json=payload)
        assert response.status_code == status.HTTP_408_REQUEST_TIMEOUT
        data = response.json()
        assert "응답 생성이 시간 초과되었습니다" in data["detail"]


# 5. AI 응답 없음
@pytest.mark.asyncio
async def test_send_message_no_ai_response(mocker):
    """
    응답이 비어있을 경우 어떻게 처리되는지 테스트합니다.
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
        response = await ac.post(f"{URI}/threads/message", json=payload)
        assert response.status_code == status.HTTP_204_NO_CONTENT


# --------------------------------------------- #

## 부하 테스트

# 부하 테스트 - 대량의 채팅방 생성 테스트
# @pytest.mark.asyncio
# async def test_bulk_create_threads():
#     """
#     동시에 여러 개의 채팅방을 생성했을 때 서버가 제대로 처리하는지 확인합니다.
#     """
#     thread_ids = []
#     async with AsyncClient(app=app, base_url="http://testserver") as ac:
#         tasks = []
#         for i in range(100):  # 100개의 채팅방을 동시에 생성합니다.
#             payload = {
#                 "crop": f"작물_{i}",
#                 "address": f"주소_{i}"
#             }
#             tasks.append(ac.post(f"{URI}/threads/", json=payload))
#         responses = await asyncio.gather(*tasks)
#
#         for response in responses:
#             assert response.status_code == status.HTTP_200_OK
#             data = response.json()
#             assert data["success"] is True
#             assert "threadId" in data
#             thread_ids.append(data["threadId"])
#
# # 부하 테스트 - 대량의 메시지 전송 테스트
# @pytest.mark.asyncio
# async def test_bulk_send_messages():
#     """
#     동일한 채팅방에 매우 많은 메시지를 전송했을 때 서버가 문제 없이 처리되는지 테스트합니다.
#     """
#     thread_id = await test_create_thread()
#     async with AsyncClient(app=app, base_url="http://testserver") as ac:
#         tasks = []
#         for i in range(10):  # 하나의 채팅방에 1000개의 메시지를 전송합니다.
#             payload = {
#                 "threadId": thread_id,
#                 "message": f"메시지_{i}"
#             }
#             tasks.append(ac.post(f"{URI}/threads/message", json=payload))
#         responses = await asyncio.gather(*tasks)
#
#         for response in responses:
#             assert response.status_code == status.HTTP_200_OK
#             data = response.json()
#             assert data["threadId"] == thread_id
#             assert "message" in data
#
# # 부하 테스트 - 짧은 시간 동안 반복적인 요청 테스트
# @pytest.mark.asyncio
# async def test_rapid_fire_requests():
#     """
#     매우 짧은 시간 동안 여러 요청을 보냈을 때 서버가 이를 정상적으로 처리하는지 테스트합니다.
#     """
#     thread_id = await test_create_thread()
#     async with AsyncClient(app=app, base_url="http://testserver") as ac:
#         tasks = []
#         for i in range(10):  # 1초 동안 10개의 메시지를 전송합니다.
#             payload = {
#                 "threadId": thread_id,
#                 "message": f"빠른 요청 메시지_{i}"
#             }
#             tasks.append(ac.post(f"{URI}/threads/message", json=payload))
#         responses = await asyncio.gather(*tasks)
#
#         for response in responses:
#             assert response.status_code == status.HTTP_200_OK
#             data = response.json()
#             assert data["threadId"] == thread_id
#             assert "message" in data
#
# # 부하 테스트 - 대량의 채팅방 삭제 테스트
# @pytest.mark.asyncio
# async def test_bulk_delete_threads():
#     """
#     여러 개의 채팅방을 동시에 삭제했을 때 서버가 제대로 처리하는지 테스트합니다.
#     """
#     thread_ids = []
#     async with AsyncClient(app=app, base_url="http://testserver") as ac:
#         # 50개의 채팅방을 생성합니다.
#         for i in range(50):
#             payload = {
#                 "crop": f"작물_{i}",
#                 "address": f"주소_{i}"
#             }
#             response = await ac.post(f"{URI}/threads/", json=payload)
#             assert response.status_code == status.HTTP_200_OK
#             data = response.json()
#             thread_ids.append(data["threadId"])
#
#         # 동시에 삭제 요청을 보냅니다.
#         tasks = [ac.delete(f"{URI}/threads/{thread_id}") for thread_id in thread_ids]
#         responses = await asyncio.gather(*tasks)
#
#         for response in responses:
#             assert response.status_code == status.HTTP_204_NO_CONTENT

# tests/test_chatbot.py
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

URI = "/members/5b16f218-682c-4eb0-989e-6fff2a6fb4f1"


## 채팅방 생성 관련 테스트

# 1. 정상적인 채팅방 생성
@pytest.mark.asyncio
async def test_create_thread():
    """
    모든 필드가 올바르게 입력된 경우 정상적인 생성이 이루어지는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "cropId": 3,
            "cropName": "감자",
            "address": "서울 성북구 낙산길 243-15 (삼선현대힐스테이트)",
            "plantedAt": "2024-11-01"
        }
        response = await ac.post(f"{URI}/threads/", json=payload)
        print(response.json())
        assert response.is_success == True
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        print(data)
        assert data["message"] == "채팅방이 성공적으로 생성되었습니다."
        assert "data" in data
        return data["data"]["threadId"]  # 다음 테스트에서 사용할 수 있도록 threadId 반환


# 2. 필수 필드 누락 (작물명)
@pytest.mark.asyncio
async def test_create_thread_missing_crop():
    """
    crop 필드가 비어있거나 누락된 경우 에러가 발생하는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "cropId": 3,
            "cropName": "",
            "address": "서울 성북구 낙산길 243-15 (삼선현대힐스테이트)",
            "plantedAt": "2024-11-01"
        }
        response = await ac.post(f"{URI}/threads/", json=payload)
        assert response.is_success == False
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        print(data)
        assert data["message"] == "입력값 검증 실패"
        assert data["error"]["details"] == "올바른 작물명을 입력해야 합니다."


# 3. 필수 필드 누락 (주소지)
@pytest.mark.asyncio
async def test_create_thread_missing_address():
    """
    address 필드가 비어있거나 누락된 경우 에러가 발생하는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "cropId": 3,
            "cropName": "감자",
            "address": "👾!@👾👨‍👨‍❤️‍🐤👨🦽‍",
            "plantedAt": "2024-11-01"
        }
        response = await ac.post(f"{URI}/threads/", json=payload)
        assert response.is_success == False
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        print(data)
        assert data["message"] == "입력값 검증 실패"
        assert data["error"]["details"] == "올바른 주소를 입력해야 합니다."


# 4. 올바르지 않은 필드(작물 아이디) 값
@pytest.mark.asyncio
async def test_create_thread_cropId_not_valid():
    """
    crop 또는 address에 예상하지 못한 형식(숫자나 특수 문자 등)이 입력된 경우 어떻게 처리되는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "cropId": -1,
            "cropName": "감자",
            "address": "서울 성북구 낙산길 243-15 (삼선현대힐스테이트)",
            "plantedAt": "2024-11-01"
        }
        response = await ac.post(f"{URI}/threads/", json=payload)
        assert response.is_success == False
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        print(data)
        assert data["message"] == "입력값 검증 실패"
        assert data["error"]["details"] == "작물ID를 입력해야 합니다."

# 5. 올바르지 않은 필드(심은날짜) 값
@pytest.mark.asyncio
async def test_create_thread_plantedAt_not_valid():
    """
    crop 또는 address에 예상하지 못한 형식(숫자나 특수 문자 등)이 입력된 경우 어떻게 처리되는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "cropId": 3,
            "cropName": "감자",
            "address": "서울 성북구 낙산길 243-15 (삼선현대힐스테이트)",
            "plantedAt": "ㅁㄴ2024-11-01"
        }
        response = await ac.post(f"{URI}/threads/", json=payload)
        assert response.is_success == False
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        print(data)
        assert data["message"] == "입력값 검증 실패"
        assert data["error"]["details"] == "날짜 형식이 올바르지 않습니다."


# ----------------------------------------------------#

## 채팅방 조회 관련 테스트

# 1. 정상적인 채팅방 조회
@pytest.mark.asyncio
async def test_get_thread():
    """
    존재하는 채팅방 ID를 사용하여 정상적으로 조회되는지 테스트합니다.
    """
    # 먼저 채팅방을 생성합니다.
    # thread_id = await test_create_thread()
    thread_id = "thread_9GfoVBuA6yx4V31xriZxNO0g"
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get(f"{URI}/threads/{thread_id}")
        print(response.json())
        assert response.is_success == True
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "채팅방 정보를 가져왔습니다."
        assert "data" in data
        assert data["data"]["threadId"] == thread_id
        assert "messages" in data["data"]


# 2. 존재하지 않는 채팅방 조회
@pytest.mark.asyncio
async def test_get_none_thread():
    """
    잘못된 또는 존재하지 않는 채팅방 ID로 조회했을 때 적절한 에러가 반환되는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get(f"{URI}/threads/NoneThreadID")
        assert response.is_success == False
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["message"] == "유효하지 않은 채팅방 ID"


# 3. 잘못된 형식의 채팅방 ID 조회
@pytest.mark.asyncio
async def test_get_incorrect_format_thread():
    """
    형식이 잘못된(특수 문자, 빈 값 등) ID로 조회했을 때 어떻게 처리되는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get(f"{URI}/threads/😆😆😆😆")
        assert response.is_success == False
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["message"] == "유효하지 않은 채팅방 ID"


# -------------------------------------------------- #

## 메시지 전송 관련 테스트

@pytest.mark.asyncio
async def test_send_message_success():
    """
    올바른 threadId와 메시지를 전송하여 AI 응답이 올바르게 생성되는지 테스트합니다.
    """
    # thread_id = await test_create_thread()
    thread_id = "thread_9GfoVBuA6yx4V31xriZxNO0g"
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "threadId": thread_id,
            "message": "근데, 나 감자 처음 심어서 마트에서 사서 해도 되나?"
        }
        response = await ac.post(f"{URI}/threads/message", json=payload)
        assert response.is_success == True
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        print(data)
        assert data["message"] == "메시지를 성공적으로 전송하였습니다."

@pytest.mark.asyncio
async def test_send_message_missing_thread_id():
    """
    threadId가 없을 경우 에러가 발생하는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "message": "오늘 날씨는 어떤가요?"
        }
        response = await ac.post(f"{URI}/threads/message", json=payload)
        assert response.is_success == False
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["message"] == "채팅방 ID가 누락되었습니다."

@pytest.mark.asyncio
async def test_send_message_missing_message():
    """
    메시지 내용이 없을 경우 에러가 발생하는지 테스트합니다.
    """
    thread_id = await test_create_thread()
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "threadId": thread_id
        }
        response = await ac.post(f"{URI}/threads/message", json=payload)
        assert response.is_success == False
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["message"] == "메시지가 누락되었습니다."

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
        assert response.is_success == False
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["message"] == "올바르지 않은 ThreadId 입니다."

# ----------------------------------------------------- #

## 채팅방 수정 관련 테스트

# 1. 정상적인 주소 변경
@pytest.mark.asyncio
async def test_modify_message_success():
    """
    정상적인 thread_id 와 address로 정상적으로 적용되는지 테스트합니다.
    """
    # thread_id = await test_create_thread()
    thread_id = "thread_xBn6dZlM3QCvwDOIkKnk0GuR"
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "address": "전라남도 고흥군 점암면",
            "plantedAt": "2024-10-29T10:20:10"
        }
        response = await ac.patch(f"{URI}/threads/{thread_id}", json=payload)
        assert response.is_success == True
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["message"] == "주소가 성공적으로 변경되었습니다."


# 2. 변경 주소 누락
@pytest.mark.asyncio
async def test_modify_message_missing_address():
    """
    address 필드가 누락되었을 때 에러가 발생하는지 테스트합니다.
    """
    thread_id = await test_create_thread()
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {}
        response = await ac.patch(f"{URI}/threads/{thread_id}", json=payload)
        assert response.is_success == False
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["message"] == "주소가 누락되었습니다."


# 3. 올바르지 않은 thread_id
@pytest.mark.asyncio
async def test_modify_message_invalid_thread_id():
    """
    존재하지 않는 thread_id로 주소 변경을 시도할 때 에러가 발생하는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "address": "경기도 성남시 분당구 판교역로"
        }
        response = await ac.patch(f"{URI}/threads/InvalidThreadID", json=payload)
        assert response.is_success == False
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["message"] == "올바르지 않은 ThreadId 입니다."


# ----------------------------------------------------- #

## 채팅방 삭제 관련 테스트

# 1. 정상적인 채팅방 삭제
@pytest.mark.asyncio
async def test_delete_thread_success():
    """
    존재하는 threadId를 사용하여 정상적으로 채팅방을 삭제했을 때 올바른 응답이 반환되는지 테스트합니다.
    """
    # 채팅방 생성
    thread_id = await test_create_thread()
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.delete(f"{URI}/threads/{thread_id}")
        assert response.is_success == True
        assert response.status_code == status.HTTP_204_NO_CONTENT
        data = response.json()
        assert data["message"] == "채팅방이 성공적으로 삭제되었습니다."


# 2. 존재하지 않는 채팅방 삭제
@pytest.mark.asyncio
async def test_delete_thread_none():
    """
    잘못된 threadId로 삭제 요청을 보냈을 때 적절한 에러가 반환되는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.delete(f"{URI}/threads/NoneThreadID")
        assert response.is_success == False
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["message"] == "채팅방을 찾을 수 없습니다."


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
        assert response.is_success == True
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["threadId"] == thread_id


# 2. AI 응답 실패 (시스템 문제)
@pytest.mark.asyncio
async def test_send_message_ai_response_failed(mocker):
    """
    AI 시스템이 응답을 생성하지 못했을 때 적절한 에러가 반환되는지 테스트합니다.
    """
    thread_id = await test_create_thread()

    # AI 응답 생성 실패 상황 모의(mock)
    mock_run_status = Mock()
    mock_run_status.status = "failed"
    mock_run_status.last_error = "AI 응답 실패"
    mocker.patch("app.api.openai.chatbot.client.beta.threads.runs.retrieve",
                 return_value=mock_run_status)

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "threadId": thread_id,
            "message": "오늘 날씨는 어떤가요?"
        }
        response = await ac.post(f"{URI}/threads/message", json=payload)
        assert response.is_success == False
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert data["message"] == "응답 생성에 실패했습니다."


# 3. AI 응답 생성 취소
@pytest.mark.asyncio
async def test_send_message_ai_response_cancelled(mocker):
    """
     AI 응답이 중간에 취소되었을 때 적절한 에러가 반환되는지 테스트합니다.
    """
    thread_id = await test_create_thread()

    # AI 응답 생성 취소 상황 모의(mock)
    mock_run_status = Mock()
    mock_run_status.status = "cancelled"
    mock_run_status.last_error = "AI 응답 취소됨"

    mocker.patch("app.api.openai.chatbot.client.beta.threads.runs.retrieve",
                 return_value=mock_run_status)

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "threadId": thread_id,
            "message": "오늘 날씨는 어떤가요?"
        }
        response = await ac.post(f"{URI}/threads/message", json=payload)
        assert response.is_success == False
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert data["message"] == "응답 생성이 취소되었습니다."


# 4. AI 응답 시간 초과
@pytest.mark.asyncio
async def test_send_message_ai_response_timeout(mocker):
    """
    응답 생성에 너무 오래 걸렸을 때 적절한 에러가 반환되는지 테스트합니다.
    """
    thread_id = await test_create_thread()

    # AI 응답 생성 시간 초과 상황 모의(mock)
    mock_run_status = Mock()
    mock_run_status.status = "expired"
    mock_run_status.last_error = "응답 생성이 시간 초과되었습니다."

    mocker.patch("app.api.openai.chatbot.client.beta.threads.runs.retrieve",
                 return_value=mock_run_status)
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "threadId": thread_id,
            "message": "오늘 날씨는 어떤가요?"
        }
        response = await ac.post(f"{URI}/threads/message", json=payload)
        assert response.is_success == False
        assert response.status_code == status.HTTP_408_REQUEST_TIMEOUT
        data = response.json()
        assert data["message"] == "응답 생성이 시간 초과되었습니다."


# 5. AI 응답 없음
@pytest.mark.asyncio
async def test_send_message_no_ai_response(mocker):
    """
    응답이 비어있을 경우 적절한 에러가 반환되는지 테스트합니다.
    """
    thread_id = await test_create_thread()

    # AI 응답이 비어 있는 상황 모의(mock)
    mock_messages = Mock()
    mock_messages.data = []

    mocker.patch("app.api.openai.chatbot.client.beta.threads.messages.list",
                 return_value=mock_messages)

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "threadId": thread_id,
            "message": "오늘 날씨는 어떤가요?"
        }

        response = await ac.post(f"{URI}/threads/message", json=payload)
        assert response.is_success == True
        assert response.status_code == status.HTTP_204_NO_CONTENT
        data = response.json()
        assert data["message"] == "AI 응답이 없습니다."


# --------------------------------------------- #

## 상태 정보 조회 테스트

# 1. 상태 정보 조회 성공
@pytest.mark.asyncio
async def test_get_thread_status():
    """
    특정 채팅방의 상태 정보를 정상적으로 조회하는지 테스트합니다.
    """
    thread_id = await test_create_thread()

    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get(f"{URI}/threads/{thread_id}/status")
        assert response.is_success == True
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        print(data)
        assert data["message"] == "상대 정보가 올바르게 반환 되었습니다."


# 2. 존재하지 않는 채팅방의 상태 정보 조회
@pytest.mark.asyncio
async def test_get_thread_status_none():
    """
    존재하지 않는 채팅방의 상태 정보를 조회했을 때 적절한 에러가 반환되는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get(f"{URI}/threads/NoneThreadID/status")
        assert response.is_success == False
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["message"] == "채팅방을 찾을 수 없습니다."


# --------------------------------------------- #

## 부하 테스트 (선택적으로 활성화)

# 부하 테스트는 실제 서버 환경에서 주의해서 실행해야 합니다. 필요에 따라 주석을 해제하여 실행할 수 있습니다.

# # 부하 테스트 - 대량의 채팅방 생성 테스트
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
#             assert response.status_code == status.HTTP_201_CREATED
#             data = response.json()
#             assert data["success"] is True
#             assert "data" in data
#             assert "threadId" in data["data"]
#             thread_ids.append(data["data"]["threadId"])
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
#         for i in range(10):  # 하나의 채팅방에 10개의 메시지를 전송합니다.
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
#             assert data["success"] is True
#             assert "data" in data
#             assert data["data"]["threadId"] == thread_id
#             assert "message" in data["data"]
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
#             assert data["success"] is True
#             assert "data" in data
#             assert data["data"]["threadId"] == thread_id
#             assert "message" in data["data"]
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
#             assert response.status_code == status.HTTP_201_CREATED
#             data = response.json()
#             thread_ids.append(data["data"]["threadId"])
#
#         # 동시에 삭제 요청을 보냅니다.
#         tasks = [ac.delete(f"{URI}/threads/{thread_id}") for thread_id in thread_ids]
#         responses = await asyncio.gather(*tasks)
#
#         for response in responses:
#             assert response.status_code == status.HTTP_200_OK
#             data = response.json()
#             assert data["success"] is True
#             assert "message" in data

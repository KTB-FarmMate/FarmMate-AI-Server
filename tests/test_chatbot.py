# tests/test_chatbot.py
import sys
import os
import pytest
import asyncio
from httpx import AsyncClient
from unittest.mock import Mock
from fastapi import status
from starlette.status import HTTP_204_NO_CONTENT

# 프로젝트의 루트 디렉토리를 모듈 검색 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # FastAPI 앱이 정의된 모듈을 임포트합니다.

pytestmark = pytest.mark.asyncio

URI = "/members/ff33b967-3035-4346-88e0-af925bc70405"


## 채팅방 생성 관련 테스트

# 1. 정상적인 채팅방 생성
@pytest.mark.asyncio
async def test_create_thread():
    """
    모든 필드가 올바르게 입력된 경우 정상적인 생성이 이루어지는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "cropName": "고구마",
            "address": "전라남도 여수시",
            "plantedAt": "2024-11-06"
        }
        response = await ac.post(f"{URI}/threads", json=payload)
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
            "cropName": "",
            "address": "서울 성북구 낙산길 243-15 (삼선현대힐스테이트)",
            "plantedAt": "2024-11-01"
        }
        response = await ac.post(f"{URI}/threads", json=payload)
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
            "cropName": "감자",
            "address": "👾!@👾👨‍👨‍❤️‍🐤👨🦽‍",
            "plantedAt": "2024-11-01"
        }
        response = await ac.post(f"{URI}/threads", json=payload)
        assert response.is_success == False
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        print(data)
        assert data["message"] == "입력값 검증 실패"
        assert data["error"]["details"] == "올바른 주소를 입력해야 합니다."

#
# # 4. 올바르지 않은 필드(작물 아이디) 값
# @pytest.mark.asyncio
# async def test_create_thread_cropId_not_valid():
#     """
#     crop 또는 address에 예상하지 못한 형식(숫자나 특수 문자 등)이 입력된 경우 어떻게 처리되는지 테스트합니다.
#     """
#     async with AsyncClient(app=app, base_url="http://testserver") as ac:
#         payload = {
#             "cropName": "감자",
#             "address": "서울 성북구 낙산길 243-15 (삼선현대힐스테이트)",
#             "plantedAt": "2024-11-01"
#         }
#         response = await ac.post(f"{URI}/threads", json=payload)
#         assert response.is_success == False
#         assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
#         data = response.json()
#         print(data)
#         assert data["message"] == "입력값 검증 실패"
#         assert data["error"]["details"] == "작물ID를 입력해야 합니다."

# 5. 올바르지 않은 필드(심은날짜) 값
@pytest.mark.asyncio
async def test_create_thread_plantedAt_not_valid():
    """
    crop 또는 address에 예상하지 못한 형식(숫자나 특수 문자 등)이 입력된 경우 어떻게 처리되는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "cropName": "감자",
            "address": "서울 성북구 낙산길 243-15 (삼선현대힐스테이트)",
            "plantedAt": "ㅁㄴ2024-11-01"
        }
        response = await ac.post(f"{URI}/threads", json=payload)
        assert response.is_success == False
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        print(data)
        assert data["message"] == "입력값 검증 실패"
        assert data["error"]["details"] == "날짜 형식이 올바르지 않습니다."


# ----------------------------------------------------#

## 채팅방 조회 관련 테스트

# 0. member의 모든 채팅방 조회
# @pytest.mark.asyncio
# async def test_get_threads():
#     """
#     존재하는 memberId를 사용하여 모든 채팅이 정상적으로 조회되는지 테스트합니다.
#     """
#     async with AsyncClient(app=app, base_url="http://testserver") as ac:
#         response = await ac.get(f"{URI}/threads")
#         print(response)
#         assert response.is_success
#         assert response.status_code == status.HTTP_200_OK
#         data = response.json()
#         assert data["message"] == "채팅방 정보를 올바르게 가져왔습니다."
#         print(data)

# 1. 정상적인 채팅방 조회
@pytest.mark.asyncio
async def test_get_thread():
    """
    존재하는 채팅방 ID를 사용하여 정상적으로 조회되는지 테스트합니다.
    """
    # 먼저 채팅방을 생성합니다.
    thread_id = await test_create_thread()
    # thread_id = "thread_cFbmc45Mmst2tRnLmEEnbgnN"
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get(f"{URI}/threads/{thread_id}")
        assert response.is_success == True
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # print(data)
        assert data["message"] == "채팅방 정보를 가져왔습니다."
        assert "data" in data
        assert data["data"]["threadId"] == thread_id
        assert "messages" in data["data"]


# 2. 올바르지 않은  채팅방 조회
@pytest.mark.asyncio
async def test_get_none_thread():
    """
    잘못된 또는 올바르지 않은  채팅방 ID로 조회했을 때 적절한 에러가 반환되는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get(f"{URI}/threads/NoneThreadID")
        assert response.is_success == False
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        print(data)
        assert data["message"] == "유효하지 않은 리소스 ID"


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
        print(data)
        assert data["message"] == "유효하지 않은 리소스 ID"


# -------------------------------------------------- #

## 메시지 전송 관련 테스트

@pytest.mark.asyncio
async def test_send_message_success():
    """
    올바른 threadId와 메시지를 전송하여 AI 응답이 올바르게 생성되는지 테스트합니다.
    """
    thread_id = await test_create_thread()
    # thread_id = "thread_6blpaxBSYEmrW5KzMmQ95TZa"
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "message": "내가 심은 작물은 뭐고, 언제 어디에 심었어?"
        }
        response = await ac.post(f"{URI}/threads/{thread_id}", json=payload)
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
        response = await ac.post(f"{URI}/threads", json=payload)
        assert response.is_success == False
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["message"] == "입력값 검증 실패"

@pytest.mark.asyncio
async def test_send_message_missing_message():
    """
    메시지 내용이 없을 경우 에러가 발생하는지 테스트합니다.
    """
    thread_id = await test_create_thread()
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "message": ""
        }
        response = await ac.post(f"{URI}/threads/{thread_id}", json=payload)
        assert response.is_success == False
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        print(data)
        assert data["message"] == "입력값 검증 실패"
        assert data["error"]["message"] == "입력값이 유효하지 않습니다."

@pytest.mark.asyncio
async def test_send_message_none_thread():
    """
    올바르지 않은  threadId로 메시지를 보낼 때 올바른 에러가 반환되는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "message": "오늘 날씨는 어떤가요?"
        }
        response = await ac.post(f"{URI}/threads/NoneThreadId", json=payload)
        assert response.is_success == False
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        print(data)
        assert data["message"] == "유효하지 않은 리소스 ID"
        assert data["error"]["message"] == "올바르지 않은 Thread ID입니다."

# ----------------------------------------------------- #

## 채팅방 수정 관련 테스트

# 1. 정상적인 주소 변경
@pytest.mark.asyncio
async def test_modify_message_success():
    """
    정상적인 thread_id 와 address로 정상적으로 적용되는지 테스트합니다.
    """
    thread_id = await test_create_thread()
    # thread_id = "thread_0PVErCzYRjSzdIf3a42NWC9F"
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "address": "경기도 수원시 곡반정동",
            "plantedAt": "2024-11-06"
        }
        response = await ac.patch(f"{URI}/threads/{thread_id}", json=payload)
        print(response.json())
        assert response.is_success == True
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["message"] == "채팅방 정보가 성공적으로 변경되었습니다."


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
        print(data)
        assert data["message"] == "입력값 검증 실패"
        assert data["error"]["details"] == "입력값이 모두 누락 되었습니다."


# 3. 올바르지 않은 thread_id
@pytest.mark.asyncio
async def test_modify_message_invalid_thread_id():
    """
    올바르지 않은  thread_id로 주소 변경을 시도할 때 에러가 발생하는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "address": "경기도 성남시 분당구 판교역로"
        }
        response = await ac.patch(f"{URI}/threads/InvalidThreadID", json=payload)
        assert response.is_success == False
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        print(data)
        assert data["message"] == "유효하지 않은 리소스 ID"
        assert data["error"]["message"] == "올바르지 않은 Thread ID입니다."


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
    # thread_id = "thread_uxQdoflvFkl0lY2bOVwj4j2w"
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.delete(f"{URI}/threads/{thread_id}")
        # print(response.json())
        assert response.status_code == HTTP_204_NO_CONTENT


# 2. 올바르지 않은  채팅방 삭제
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
        print(data)
        assert data["message"] == "유효하지 않은 리소스 ID"
        assert data["error"]["message"] == "올바르지 않은 Thread ID입니다."


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
        response = await ac.post(f"{URI}/threads/{thread_id}", json=payload)
        assert response.is_success == True
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        print(data)
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
        response = await ac.post(f"{URI}/threads/{thread_id}", json=payload)
        assert response.is_success == False
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        print(data)
        assert data["message"] == "서버 내부 오류가 발생했습니다."
        assert data["error"]["message"] == "AI 응답 생성 실패: failed"


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
        response = await ac.post(f"{URI}/threads/{thread_id}", json=payload)
        assert response.is_success == False
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        print(data)
        assert data["message"] == "서버 내부 오류가 발생했습니다."
        assert data["error"]["message"] == "AI 응답 생성 실패: cancelled"


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
        response = await ac.post(f"{URI}/threads/{thread_id}", json=payload)
        assert response.is_success == False
        assert response.status_code == status.HTTP_408_REQUEST_TIMEOUT
        data = response.json()
        print(data)
        assert data["message"] == "요청 시간이 초과되었습니다."
        assert data["error"]["message"] == "AI 응답 생성 실패: expired"


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

        response = await ac.post(f"{URI}/threads/{thread_id}", json=payload)
        assert response.is_success == False
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        print(data)
        assert data["message"] == "리소스를 찾을 수 없습니다."
        assert data["error"]["message"] == "AI 응답이 없습니다."


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
        assert data["message"] == "상태 정보가 올바르게 반환되었습니다."


# 2. 올바르지 않은  채팅방의 상태 정보 조회
@pytest.mark.asyncio
async def test_get_thread_status_none():
    """
    올바르지 않은  채팅방의 상태 정보를 조회했을 때 적절한 에러가 반환되는지 테스트합니다.
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get(f"{URI}/threads/NoneThreadID/status")
        assert response.is_success == False
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["message"] == "유효하지 않은 리소스 ID"
        assert data["error"]["message"] == "올바르지 않은 Thread ID입니다."


# --------------------------------------------- #

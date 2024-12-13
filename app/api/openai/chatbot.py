# 타입과 유틸리티 관련 모듈
from typing import List, Any, Optional, Generic, TypeVar
import re
import time
import json
import logging
from enum import Enum
from datetime import datetime

# HTTP 및 API 관련 모듈
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator, ValidationError
from starlette.responses import JSONResponse
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_408_REQUEST_TIMEOUT, HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_404_NOT_FOUND,
)

# OpenAI 관련 모듈
from openai.pagination import SyncCursorPage
import openai

# 프로젝트 내 모듈
from app.core.config import settings
from app.utils.response import create_response
from app.models.error import ErrorDetail

# 네트워크 관련 모듈
import socket

# BE_BASE_URL = "http://15.164.175.127:8080/api"

router = APIRouter()

# OpenAI API 클라이언트 생성
client: openai.Client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

# ASSISTANT_ID를 사용하여 Assistant 인스턴스 가져오기
assistant = client.beta.assistants.retrieve(assistant_id=settings.ASSISTANT_ID)

T = TypeVar('T')


class BaseResponse(BaseModel, Generic[T]):
    """기본 응답 모델"""
    success: bool
    message: str
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None


# 메시지 관련 모델
class Message(BaseModel):
    role: str
    content: str


class ThreadDetail(BaseModel):
    threadId: str
    messages: List[Message]


class CreateThreadRequest(BaseModel):
    cropName: str = Field("", description="재배할 작물 이름")
    address: str = Field("", description="농사를 짓는 지역 주소")
    plantedAt: str = Field("", description="작물을 심은 날짜")


class ThreadCreateData(BaseModel):
    threadId: str = Field(..., description="생성된 채팅방의 고유 식별자")


@router.post(
    "",
    summary="채팅방 생성",
    tags=["채팅방 관련"],
    responses={
        200: {
            "description": "성공적인 응답.",
            "content": {
                "application/json": {
                    "example": {  # Example 값을 설정합니다.
                        "message": "채팅방이 성공적으로 생성되었습니다.",
                        "data": {
                            "threadId": "thread_YiIpm1PYCP8hy443TaIlulAd"
                        }
                    }
                }
            }
        }
    }
)
async def create_thread(memberId: str, request: CreateThreadRequest) -> JSONResponse:
    """새로운 채팅방(Thread)을 생성하고 초기 메시지를 추가합니다."""
    thread = client.beta.threads.create()

    # crop_id = request.cropId
    # if crop_id == -1:
    #     raise ValueError("작물ID를 입력해야 합니다.")

    crop = request.cropName
    if not crop.strip() or re.search(r'[^\w\s]', crop):
        raise ValueError(f"올바른 작물명을 입력해야 합니다.")

    address = request.address
    if not address.strip() or not re.match(r'^[가-힣a-zA-Z0-9\s()\-_,.]+$', request.address):
        raise ValueError("올바른 주소를 입력해야 합니다.")

    plantedAt = request.plantedAt
    if not plantedAt.strip():
        raise ValueError("심은 날짜를 입력해야 합니다.")

    try:
        datetime.strptime(plantedAt, "%Y-%m-%d")
    except ValueError:
        raise ValueError("날짜 형식이 올바르지 않습니다.")

    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="assistant",
        content=f"[시스템 메시지] 사용자는 심은날짜 : {plantedAt}, 주소 : {address}에서 작물 : {crop}을(를) 재배하고 있습니다.",
    )

    # if req.status_code != 200:
    #     raise HTTPException(
    #         status_code=req.status_code,
    #         detail=req.json().get("details", "백엔드 서버 요청 실패")
    #     )
    return create_response(
        status_code=HTTP_201_CREATED,
        message="채팅방이 성공적으로 생성되었습니다.",
        data={"threadId": thread.id}
    )


class Role(str, Enum):
    USER = "user"
    ASSITANT = "assistant"


class MessageData(BaseModel):
    """채팅방의 메시지 구조를 정의합니다."""
    role: Role = Field(..., description="메시지 작성자 (assistant 또는 user)")
    text: str = Field(..., description="메시지 내용")

    def to_dict(self):
        return {
            "role": self.role,
            "text": self.text,
        }


@router.get(
    "/{thread_id}",
    summary="채팅방 정보 로드",
    tags=["채팅방 관련"],
    responses={
        200: {
            "description": "성공적인 응답.",
            "content": {
                "application/json": {
                    "example": {
                        "message": "채팅방 정보를 가져왔습니다.",
                        "data": {
                            "threadId": "thread_oOr1qnY5H6XTqTQuKTKGHfSY",
                            "messages": [
                                {
                                    "role": "assistant",
                                    "text": "[시스템 메시지] 사용자는 심은날짜 : 2024-01-01, 주소 : 판교에서 작물 : 감자을(를) 재배하고 있습니다."
                                },
                                {
                                    "role": "user",
                                    "text": "감자 데이터 줘"
                                }
                            ]
                        }
                    }
                }
            }
        }
    }
)
async def get_thread(memberId: str, thread_id: str):
    """특정 채팅방의 메시지 목록을 반환합니다."""
    thread = client.beta.threads.retrieve(thread_id=thread_id)
    messages = client.beta.threads.messages.list(thread_id=thread_id, order="asc")

    messages_data = [
        MessageData(
            role=Role(message.role),
            text=message.content[0].text.value if message.content else "",
        ).to_dict()
        for message in messages.data
    ]

    return create_response(
        status_code=HTTP_200_OK,
        message="채팅방 정보를 가져왔습니다.",
        data={"threadId": thread_id, "messages": messages_data}
    )


class MessageRequest(BaseModel):
    """사용자가 보낸 메시지 정보를 담는 모델입니다."""
    message: str = Field("", description="사용자가 보낸 메시지 내용")


@router.post(
    "/{thread_id}",
    summary="채팅방 메시지 전송",
    tags=["채팅방 관련"],
    responses={
        200: {
            "description": "성공적인 응답.",
            "content": {
                "application/json": {
                    "example": {
                        "message": "메시지를 성공적으로 전송하였습니다.",
                        "data": {
                            "threadId": "thread_oOr1qnY5H6XTqTQuKTKGHfSY",
                            "text": "응답 메시지"
                        }
                    }
                }
            }
        }
    }
)
async def send_message(memberId: str, thread_id: str, request: MessageRequest):
    """특정 채팅방에 메시지를 전송하고 AI의 응답을 생성합니다."""
    if not request.message:
        raise ValueError("메시지가 누락되었습니다.")

    thread = client.beta.threads.retrieve(thread_id=thread_id)

    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=request.message,
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )

    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        if run_status.status == "completed":
            break
        elif run_status.status in ["failed", "cancelled"]:
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI 응답 생성 실패: {run_status.status}"
            )
        elif run_status.status == "expired":
            raise HTTPException(
                status_code=HTTP_408_REQUEST_TIMEOUT,
                detail=f"AI 응답 생성 실패: {run_status.status}"
            )
        time.sleep(1)

    messages = client.beta.threads.messages.list(thread_id=thread_id, order="desc", limit=1)
    if not messages.data:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="AI 응답이 없습니다."
        )

    latest_message = messages.data[0]
    if latest_message.role == "assistant":
        content = latest_message.content[0].text.value if latest_message.content else ""
        return create_response(
            status_code=HTTP_200_OK,
            message="메시지를 성공적으로 전송하였습니다.",
            data={"threadId": thread_id, "text": content}
        )

    raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="AI 응답을 찾을 수 없습니다.")


class ModifyMessageRequest(BaseModel):
    address: str = Field("", description="변경할 주소")
    plantedAt: datetime = Field(None, description="변경할 심은 날짜 (YYYY-MM-DD 형식)")


@router.patch(
    "/{thread_id}",
    summary="채팅방 정보 수정",
    tags=["채팅방 관련"],
    responses={
        200: {
            "description": "성공적인 응답.",
            "content": {
                "application/json": {
                    "example": {
                        "message": "주소가 성공적으로 변경되었습니다.",
                        "data": {
                            "message": "주소가 성공적으로 변경되었습니다."
                        }
                    }
                }
            }
        }
    }
)
async def modify_message(memberId: str, thread_id: str, request: ModifyMessageRequest):
    """특정 채팅방의 주소 정보를 수정합니다."""
    if not thread_id:
        raise ValueError("채팅방 ID가 누락되었습니다.")
    if not request.address:
        raise ValueError("주소가 누락되었습니다.")

    thread = client.beta.threads.retrieve(thread_id=thread_id)

    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="assistant",
        content=f"""
       [시스템 메시지]
       사용자 요청에 따라 주소지 변경 작업이 이루어졌습니다.

       [변경 사항]
       - 변경된 주소지: {request.address}
       - 변경된 이유: 사용자의 요청에 따른 주소지 업데이트
       - 변경된 심은날짜 : {request.plantedAt}
       - 변경된 이유: 사용자의 요청에 따른 심은날짜 업데이트
       """,
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )

    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run_status.status == "completed":
            break
        elif run_status.status in ["failed", "cancelled", "expired"]:
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI 응답 생성 실패: {run_status.status}"
            )
        time.sleep(1)

    return create_response(
        status_code=HTTP_200_OK,
        message="주소가 성공적으로 변경되었습니다.",
        data={"message": "주소가 성공적으로 변경되었습니다."}
    )


@router.delete(
    "/{thread_id}",
    summary="채팅방 삭제",
    tags=["채팅방 관련"],
    responses={
        200: {
            "description": "반환되지 않음",
            "content": {"application/json": {"example": {}}},
        },
        204: {
            "description": "성공적으로 삭제되었습니다."
        }
    }
)
async def delete_thread(memberId: str, thread_id: str):
    """특정 채팅방을 삭제합니다."""
    client.beta.threads.delete(thread_id)

    # req = requests.delete(f"{BE_BASE_URL}/members/{memberId}/threads/{thread_id}", json=request_data)
    #
    # if req.status_code != 200:
    #     raise HTTPException(
    #         status_code=req.status_code,
    #         detail=req.json().get("details", "백엔드 서버 요청 실패")
    #     )
    return create_response(status_code=HTTP_204_NO_CONTENT, message="채팅방이 성공적으로 삭제되었습니다.")


@router.get(
    "/{thread_id}/status",
    summary="대시보드 정보 요청",
    tags=["대시보드 관련"],
    responses={
        200: {
            "description": "성공적인 응답",
            "content": {
                "application/json":
                    {"example":
                        {
                            "message": "상태 정보가 올바르게 반환되었습니다.",
                            "data": {
                                "recommendedActions": {
                                    "0": "물 주기",
                                    "1": "비료 주기",
                                    "2": "영양제 주기"
                                }
                            }
                        }
                    }
            }
        }
    }
)
async def get_thread_status(memberId: str, thread_id: str, cropName: str, plantedAt: str):
    """특정 채팅방의 상태 정보를 반환합니다."""
    # thread = client.beta.threads.retrieve(thread_id=thread_id)
    # messages = client.beta.threads.messages.list(thread_id=thread.id, order="asc")

    # assistant_message = [
    #     {"role": "assistant", "content": message.content[0].text.value}
    #     for message in messages
    #     if message.role == "assistant" and "[시스템 메시지]" in message.content[0].text.value
    # ]

    # thread_status = ThreadStatus()
    # thread_status.set_message(assistant_message)
    # weather_data = thread_status.get_weather()

    return create_response(
        status_code=HTTP_200_OK,
        message="상태 정보가 올바르게 반환되었습니다.",
        data={
            "recommendedActions": {
                "0": "물 주기",
                "1": "비료 주기",
                "2": "영양제 주기"
            }
        }
    )

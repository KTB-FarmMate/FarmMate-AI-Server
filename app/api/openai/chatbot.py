# 타입과 유틸리티 관련 모듈
from typing import List, Any, Optional, Generic, TypeVar
import re
import time
import json
import logging
from enum import Enum
from datetime import datetime
import logging

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
from app.utils.response import ApiResponse, ErrorDetail

# 네트워크 관련 모듈
import socket

# BE_BASE_URL = "http://15.164.175.127:8080/api"

router = APIRouter()

# OpenAI API 클라이언트 생성
client: openai.Client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

# ASSISTANT_ID를 사용하여 Assistant 인스턴스 가져오기
assistant = client.beta.assistants.retrieve(assistant_id=settings.ASSISTANT_ID)

T = TypeVar('T')

logging.basicConfig(level=logging.INFO)


class BaseResponse(BaseModel, Generic[T]):
    """기본 응답 모델"""
    success: bool
    message: str
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None


class Role(str, Enum):
    USER = "USER"
    ASSITANT = "ASSISTANT"


class MessageData(BaseModel):
    """채팅방의 메시지 구조를 정의합니다."""
    role: Role = Field(..., description="메시지 작성자 (USER 또는 ASSISTANT)")
    text: str = Field(..., description="메시지 내용")

    def to_dict(self):
        return {
            "role": self.role,
            "text": self.text,
        }


class ThreadDetail(BaseModel):
    threadId: str
    messages: List[MessageData]


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
    response_model=ApiResponse[ThreadCreateData],
    status_code=HTTP_201_CREATED,
    responses={
        201: {
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
async def create_thread(memberId: str, request: CreateThreadRequest) -> ApiResponse:
    """새로운 채팅방(Thread)을 생성하고 초기 메시지를 추가합니다."""
    thread = client.beta.threads.create()

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

    logging.info("[CHATBOT] thread create success.")
    return ApiResponse(
        message="채팅방이 성공적으로 생성되었습니다.",
        data={"threadId": thread.id},
        status_code=HTTP_201_CREATED
    ).to_response()


@router.get(
    "/{thread_id}",
    summary="채팅방 정보 로드",
    tags=["채팅방 관련"],
    response_model=ApiResponse[ThreadDetail],
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
                                    "role": "ASSISTANT",
                                    "text": "[시스템 메시지] 사용자는 심은날짜 : 2024-01-01, 주소 : 판교에서 작물 : 감자을(를) 재배하고 있습니다."
                                },
                                {
                                    "role": "USER",
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
            role=Role(message.role.upper()),
            text=message.content[0].text.value if message.content else "",
        ).to_dict()
        for message in messages.data
    ]

    logging.info("[CHATBOT] thread message list return success.")
    return ApiResponse(
        message="채팅방 정보를 가져왔습니다.",
        data={"threadId": thread_id, "messages": messages_data}
    ).to_response()


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
            logging.warning("[CHATBOT] message send failed")
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI 응답 생성 실패: {run_status.status}"
            )
        elif run_status.status == "expired":
            logging.warning("[CHATBOT] message send failed")
            raise HTTPException(
                status_code=HTTP_408_REQUEST_TIMEOUT,
                detail=f"AI 응답 생성 실패: {run_status.status}"
            )
        time.sleep(1)

    messages = client.beta.threads.messages.list(thread_id=thread_id, order="desc", limit=1)
    if not messages.data:
        logging.warning("[CHATBOT] message send failed")
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="AI 응답이 없습니다."
        )

    latest_message = messages.data[0]
    if latest_message.role == "assistant":
        content = latest_message.content[0].text.value if latest_message.content else ""
        logging.info("[CHATBOT] message send success.")
        return ApiResponse(
            message="메시지를 성공적으로 전송하였습니다.",
            data={"threadId": thread_id, "text": content}
        ).to_response()

    logging.error("[CHATBOT] message send error")
    raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="AI 응답을 찾을 수 없습니다.")


class ModifyMessageRequest(BaseModel):
    address: str = Field("", description="변경할 주소")
    plantedAt: str = Field(None, description="변경할 심은 날짜 (YYYY-MM-DD 형식)")


@router.patch(
    "/{thread_id}",
    summary="채팅방 정보 수정",
    response_model=ApiResponse,
    tags=["채팅방 관련"],
    responses={
        200: {
            "description": "성공적인 응답.",
            "content": {
                "application/json": {
                    "example": {
                        "message": "채팅방 정보가 성공적으로 변경되었습니다.",
                        "data": {
                            "message": "채팅방 정보가 성공적으로 변경되었습니다."
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
    if request.plantedAt:
        try:
            # `request.plantedAt`를 datetime으로 변환 시도
            datetime.strptime(request.plantedAt, "%Y-%m-%d")
        except ValueError:
            raise ValueError("plantedAt는 'YYYY-MM-DD' 형식이어야 합니다.")

    if not request.address and not request.plantedAt:
        raise ValueError("입력값이 모두 누락 되었습니다.")

    thread = client.beta.threads.retrieve(thread_id=thread_id)

    modify_message = """
    [변경 사항]
    """

    if request.address:
        modify_message += f"""
        - 변경된 주소지: {request.address}
       - 변경된 이유: 사용자의 요청에 따른 주소지 업데이트
        """

    if request.plantedAt:
        modify_message += f"""
       - 변경된 심은날짜 : {request.plantedAt}
       - 변경된 이유: 사용자의 요청에 따른 심은날짜 업데이트
        """

    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="assistant",
        content=f"""
       [시스템 메시지]
       사용자 요청에 따라 채팅방 정보 변경 작업이 이루어졌습니다.
        앞으로의 사용자에게 제공하는 정보는 변경된 정보를 제공해야 한다.
       """ + modify_message,
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

    logging.info("[CHATBOT] message modify success.")
    return ApiResponse(
        message="채팅방 정보가 성공적으로 변경되었습니다.",
        data={"message": "채팅방 정보가 성공적으로 변경되었습니다."}
    ).to_response()


@router.delete(
    "/{thread_id}",
    summary="채팅방 삭제",
    response_model=None,
    status_code=204,  # 기본 상태 코드를 204로 설정
    tags=["채팅방 관련"],
    responses={
        204: {
            "description": "성공적으로 삭제되었습니다.",
            "content": None,  # 본문 없음
        },
    }
)
async def delete_thread(memberId: str, thread_id: str):
    """특정 채팅방을 삭제합니다."""
    client.beta.threads.delete(thread_id)

    logging.info("[CHATBOT] thread delete success.")
    return None
    # return ApiResponse(status_code=HTTP_204_NO_CONTENT, message="채팅방이 성공적으로 삭제되었습니다.")


class DashBoardResponse(BaseModel):
    recommendedActions: List[str] = Field([], description="추천 작업에 대한 리스트")


@router.get(
    "/{thread_id}/status",
    summary="대시보드 정보 요청",
    response_model=ApiResponse[DashBoardResponse],
    tags=["대시보드 관련"],
    responses={
        200: {
            "description": "성공적인 응답",
            "content": {"application/json":
                {"example":
                    {
                        "message": "상태 정보가 올바르게 반환되었습니다.",
                        "data": {
                            "recommendedActions": ["묘판 설치", "싹 틔우기", "영양제 주기"]
                        }
                    }
                }
            }
        }
    }
)
async def get_thread_status(memberId: str, thread_id: str):
    """특정 채팅방의 상태 정보를 반환합니다."""
    client.beta.threads.retrieve(thread_id=thread_id)
    logging.info("[CHATBOT] thread status return success.")
    return ApiResponse(
        message="상태 정보가 올바르게 반환되었습니다.",
        data={
            "recommendedActions": ["물 주기", "비료 주기", "영양제 주기"]
        }).to_response()

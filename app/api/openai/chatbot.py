from typing import List, Any, Optional, Generic, TypeVar
import re
import time
from enum import Enum
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Response
from openai.pagination import SyncCursorPage
from pydantic import BaseModel, Field, field_validator, ValidationError
from openai import OpenAI, Client
from starlette.responses import JSONResponse
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR, HTTP_408_REQUEST_TIMEOUT
)

from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.api.weather.weather import get_coordinates

router = APIRouter()

# OpenAI API 클라이언트 생성
client: Client = OpenAI(api_key=settings.OPENAI_API_KEY)

# ASSISTANT_ID를 사용하여 Assistant 인스턴스 가져오기
assistant = client.beta.assistants.retrieve(assistant_id=settings.ASSISTANT_ID)

T = TypeVar('T')

"""HTTP 상태 코드 정의"""
# OK = HTTP_200_OK                          # 200: 성공
# CREATED = HTTP_201_CREATED                # 201: 리소스 생성됨
# NO_CONTENT = HTTP_204_NO_CONTENT         # 204: 성공했지만 반환할 컨텐츠 없음
# BAD_REQUEST = HTTP_400_BAD_REQUEST        # 400: 잘못된 요청
# UNAUTHORIZED = HTTP_401_UNAUTHORIZED      # 401: 인증 필요
# FORBIDDEN = HTTP_403_FORBIDDEN           # 403: 권한 없음
# NOT_FOUND = HTTP_404_NOT_FOUND           # 404: 리소스를 찾을 수 없음
# CONFLICT = HTTP_409_CONFLICT             # 409: 리소스 충돌
# UNPROCESSABLE = HTTP_422_UNPROCESSABLE_ENTITY  # 422: 유효성 검증 실패
# SERVER_ERROR = HTTP_500_INTERNAL_SERVER_ERROR  # 500: 서버 에러

class ErrorDetail(BaseModel):
    """에러 상세 정보 모델"""
    code: str
    message: str
    details: Optional[str] = None

    def to_dict(self):
        """객체를 딕셔너리로 변환"""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details
        }


class BaseResponse(BaseModel, Generic[T]):
    """기본 응답 모델"""
    success: bool
    message: str
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None


# 메시지 관련 모델
class Message(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class ThreadDetail(BaseModel):
    threadId: str
    messages: List[Message]


def create_response(*,
                    status_code: int,
                    message: str,
                    data: Any = None,
                    error: dict[str, str] = None) -> JSONResponse:
    """통합 응답 생성 함수
    - status_code로 성공/실패 판단 (2xx는 성공, 4xx/5xx는 실패)
    - error는 실패시에만 포함
    """
    return JSONResponse(status_code=status_code, content=
    {
        "message": message,
        "data": data,
        "error": error}
                        )


class CreateThreadRequest(BaseModel):
    crop: str = Field("", description="재배할 작물 이름")
    address: str = Field("", description="농사를 짓는 지역 주소")


class ThreadCreateData(BaseModel):
    threadId: str = Field(..., description="생성된 채팅방의 고유 식별자")


@router.post("/")
async def create_thread(memberId: str, request: CreateThreadRequest) -> JSONResponse:
    """
    새로운 채팅방(Thread)을 생성하고 초기 메시지를 추가합니다.

    Returns:
        BaseResponse[ThreadCreateData]: 생성된 채팅방의 고유 식별자를 반환합니다.
    """
    try:
        thread = client.beta.threads.create()

        crop = request.crop

        if not isinstance(crop, str):
            raise ValueError('작물명은 문자열이어야 합니다.')
        if not crop.strip():
            raise ValueError("작물명을 입력해야 합니다.")
        if re.search(r'[^\w\s]', crop):
            raise ValueError('작물명에는 특수 문자가 포함될 수 없습니다.')

        address = request.address

        if not isinstance(address, str):
            raise ValueError('주소는 문자열이어야 합니다.')
        if not address.strip():
            raise ValueError("주소를 입력해야 합니다.")
        if re.search(r'[^\w\s]', address):
            raise ValueError('주소에는 특수 문자가 포함될 수 없습니다.')
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"주소 : {address}에서 작물 : {crop}을(를) 재배하고 있습니다.",
        )

        return create_response(status_code=HTTP_201_CREATED,
                               message="채팅방이 성공적으로 생성되었습니다.",
                               data={"threadId": thread.id})

    except ValueError as e:
        return create_response(status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                               message="요청이 올바르지 않음",
                               error=ErrorDetail(
                                   code="VALUE_ERROR",
                                   message="요청 매개변수가 올바르지 않습니다.",
                                   details=str(e)
                               ).to_dict()
                               )
    except Exception as e:
        return create_response(status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                               message="Internal server error",
                               error=ErrorDetail(
                                   code="SERVER_ERROR",
                                   message="An unexpected error occurred",
                                   details=str(e)
                               ).to_dict()
                               )


class MessageData(BaseModel):
    """
    채팅방의 메시지 구조를 정의합니다.
    """
    id: str = Field(..., description="OpenAI Thread 내 메시지의 고유 식별자")
    role: str = Field(..., description="메시지 작성자 (assistant 또는 user)")
    content: str = Field(..., description="메시지 내용")
    created_at: str = Field(..., description="메시지 생성 시간")

    def to_dict(self):
        """객체를 딕셔너리로 변환"""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at
        }


class ThreadResponseData(BaseModel):
    """
    채팅방의 응답 형식을 정의합니다.
    """
    threadId: str = Field(..., description="채팅방의 고유 식별자")
    messages: List[MessageData] = Field(..., description="채팅방의 모든 메시지")


@router.get("/{thread_id}", response_model=create_response)
async def get_thread(memberId: str, thread_id: str):
    """
    특정 채팅방의 메시지 목록을 반환합니다.
    """
    try:
        try:
            client.beta.threads.retrieve(thread_id=thread_id)
        except Exception:
            return create_response(
                status_code=HTTP_404_NOT_FOUND,
                message="유효하지 않은 채팅방 ID입니다.",
                error=ErrorDetail(
                    code="NOT_FOUND",
                    message="채팅방을 찾을 수 없습니다.",
                    details="Invalid thread_id"
                ).to_dict()
            )

        messages = client.beta.threads.messages.list(thread_id=thread_id, order="asc")

        messages_data = [
            MessageData(
                id=message.id,
                role=message.role,
                content=message.content[0].text.value if message.content else "",
                created_at=time.strftime('%Y-%m-%d %H:%M', time.localtime(message.created_at))
            ).to_dict()
            for message in messages.data
        ]

        return create_response(
            status_code=HTTP_200_OK,
            message="채팅방 정보를 가져왔습니다.",
            data={"threadId": thread_id, "messages": messages_data}
        )
    except HTTPException as e:
        return create_response(
            status_code=HTTP_400_BAD_REQUEST,
            message="채팅방 정보를 가져오는데 실패했습니다.",
            error=ErrorDetail(
                code="HTTP_ERROR",
                message="요청 처리 중 오류가 발생했습니다.",
                details=str(e.detail)
            ).to_dict()
        )
    except Exception as e:
        return create_response(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            message="채팅방 정보 조회 중 오류가 발생했습니다.",
            error=ErrorDetail(
                code="SERVER_ERROR",
                message="서버 내부 오류가 발생했습니다.",
                details=str(e)
            ).to_dict()
        )


class MessageRequest(BaseModel):
    """
    사용자가 보낸 메시지 정보를 담는 모델입니다.
    """
    threadId: str = Field("", description="채팅방의 고유 식별자")
    message: str = Field("", description="사용자가 보낸 메시지 내용")


class SendMessageData(BaseModel):
    threadId: str = Field(..., description="채팅방의 고유 식별자")
    message: str = Field(..., description="AI의 응답 메시지")


@router.post("/message", response_model=create_response)
async def send_message(memberId: str, request: MessageRequest):
    """
    특정 채팅방에 메시지를 전송하고 AI의 응답을 생성합니다.
    """
    try:
        if not request.threadId:
            return create_response(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                message="채팅방 ID가 누락되었습니다.",
                error=ErrorDetail(
                    code="MISSING_FIELD",
                    message="필수 필드가 누락되었습니다.",
                    details="threadId is required"
                ).to_dict()
            )
        if not request.message:
            return create_response(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                message="메시지가 누락되었습니다.",
                error=ErrorDetail(
                    code="MISSING_FIELD",
                    message="필수 필드가 누락되었습니다.",
                    details="message is required"
                ).to_dict()
            )
        try:
            thread = client.beta.threads.retrieve(thread_id=request.threadId)
        except Exception as e:
            return create_response(
                status_code=HTTP_404_NOT_FOUND,
                message="올바르지 않은 ThreadId 입니다.",
                error=ErrorDetail(
                    code="NOT_FOUND",
                    message="채팅방을 찾을 수 없습니다.",
                    details=f"{e}"
                ).to_dict()
            )

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
            run_status = client.beta.threads.runs.retrieve(thread_id=request.threadId, run_id=run.id)
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                return create_response(
                    status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                    message="응답 생성에 실패했습니다.",
                    error=ErrorDetail(
                        code="AI_RESPONSE_FAILED",
                        message="AI 응답 생성 실패",
                        details=run_status.last_error
                    ).to_dict()
                )
            elif run_status.status == "cancelled":
                return create_response(
                    status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                    message="응답 생성이 취소되었습니다.",
                    error=ErrorDetail(
                        code="AI_RESPONSE_CANCELLED",
                        message="AI 응답이 취소됨",
                        details=run_status.last_error
                    ).to_dict()
                )
            elif run_status.status == "expired":
                return create_response(
                    status_code=HTTP_408_REQUEST_TIMEOUT,
                    message="응답 생성이 시간 초과되었습니다.",
                    error=ErrorDetail(
                        code="AI_RESPONSE_TIMEOUT",
                        message="응답 생성 시간 초과",
                        details=run_status.last_error
                    ).to_dict()
                )
            time.sleep(1)

        messages = client.beta.threads.messages.list(thread_id=request.threadId, order="desc", limit=1)

        if not messages.data:
            return create_response(
                status_code=HTTP_204_NO_CONTENT,
                message="AI 응답이 없습니다.",
                error=ErrorDetail(
                    code="NO_CONTENT",
                    message="AI 응답을 찾을 수 없습니다.",
                    details="No AI response generated"
                ).to_dict()
            )

        latest_message = messages.data[0]
        if latest_message.role == "assistant":
            content = latest_message.content[0].text.value if latest_message.content else ""
            return create_response(
                status_code=HTTP_200_OK,
                message="메시지를 성공적으로 전송하였습니다.",
                data={"threadId": request.threadId, "message": content}
            )

        return create_response(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            message="AI 응답이 없습니다.",
            error=ErrorDetail(
                code="NO_CONTENT",
                message="AI 응답을 찾을 수 없습니다.",
                details="No assistant response found"
            ).to_dict()
        )

    except HTTPException as e:
        return create_response(
            status_code=HTTP_400_BAD_REQUEST,
            message="메시지 전송에 실패했습니다.",
            error=ErrorDetail(
                code="HTTP_ERROR",
                message="요청 처리 중 오류가 발생했습니다.",
                details=str(e.detail)
            ).to_dict()
        )
    except Exception as e:
        return create_response(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            message="메시지 전송 중 오류가 발생했습니다.",
            error=ErrorDetail(
                code="SERVER_ERROR",
                message="서버 내부 오류가 발생했습니다.",
                details=str(e)
            ).to_dict()
        )


class ModifyMessageRequest(BaseModel):
    address: str = Field("", description="변경할 주소")
    plantedAt: datetime = Field(None, description="변경할 심은 날짜 (YYYY-MM-DDTHH:MM:SS 형식)")  # ISO 형식 사용


class ModifyMessageData(BaseModel):
    message: str = Field("", description="수정 결과 메시지")


@router.patch("/{thread_id}", response_model=create_response)
async def modify_message(memberId: str, thread_id: str, request: ModifyMessageRequest):
    """
    특정 채팅방의 주소 정보를 수정합니다.
    """
    try:
        if not thread_id:
            return create_response(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                message="채팅방 ID가 누락되었습니다.",
                error=ErrorDetail(
                    code="MISSING_FIELD",
                    message="필수 필드가 누락되었습니다.",
                    details="thread_id is required"
                ).to_dict()
            )
        if not request.address:
            return create_response(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                message="주소가 누락되었습니다.",
                error=ErrorDetail(
                    code="MISSING_FIELD",
                    message="필수 필드가 누락되었습니다.",
                    details="address is required"
                ).to_dict()
            )

        address = request.address
        plantedAt = request.plantedAt

        try:
            thread = client.beta.threads.retrieve(thread_id=thread_id)
        except Exception as e:
            return create_response(
                status_code=HTTP_404_NOT_FOUND,
                message="올바르지 않은 ThreadId 입니다.",
                error=ErrorDetail(
                    code="NOT_FOUND",
                    message="채팅방을 찾을 수 없습니다.",
                    details="Invalid thread_id"
                ).to_dict()
            )

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="assistant",
            content=f"""
           [시스템 메시지]
           사용자 요청에 따라 주소지 변경 작업이 이루어졌습니다.

           [변경 사항]
           - 변경된 주소지: {address}
           - 변경된 이유: 사용자의 요청에 따른 주소지 업데이트
           - 변경된 심은날짜 : {plantedAt}
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
            elif run_status.status == "failed":
                return create_response(
                    status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                    message="응답 생성에 실패했습니다.",
                    error=ErrorDetail(
                        code="AI_RESPONSE_FAILED",
                        message="AI 응답 생성 실패",
                        details=run_status.last_error
                    ).to_dict()
                )
            elif run_status.status == "cancelled":
                return create_response(
                    status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                    message="응답 생성이 취소되었습니다.",
                    error=ErrorDetail(
                        code="AI_RESPONSE_CANCELLED",
                        message="AI 응답이 취소됨",
                        details=run_status.last_error
                    ).to_dict()
                )
            elif run_status.status == "expired":
                return create_response(
                    status_code=HTTP_408_REQUEST_TIMEOUT,
                    message="응답 생성이 시간 초과되었습니다.",
                    error=ErrorDetail(
                        code="AI_RESPONSE_TIMEOUT",
                        message="응답 생성 시간 초과",
                        details=run_status.last_error
                    ).to_dict()
                )
            time.sleep(1)

        return create_response(
            status_code=HTTP_200_OK,
            message="주소가 성공적으로 변경되었습니다.",
            data=ModifyMessageData(message="주소가 성공적으로 변경되었습니다.").dict()
        )

    except HTTPException as e:
        return create_response(
            status_code=HTTP_400_BAD_REQUEST,
            message="주소 변경에 실패했습니다.",
            error=ErrorDetail(
                code="HTTP_ERROR",
                message="요청 처리 중 오류가 발생했습니다.",
                details=str(e.detail)
            ).to_dict()
        )
    except Exception as e:
        return create_response(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            message="주소 변경 중 오류가 발생했습니다.",
            error=ErrorDetail(
                code="SERVER_ERROR",
                message="서버 내부 오류가 발생했습니다.",
                details=str(e)
            ).to_dict()
        )


@router.delete("/{thread_id}", status_code=HTTP_204_NO_CONTENT)
async def delete_thread(memberId: str, thread_id: str):
    """
    특정 채팅방을 삭제합니다.
    """
    try:
        client.beta.threads.delete(thread_id)
        return create_response(status_code=HTTP_204_NO_CONTENT, message="채팅방이 성공적으로 삭제되었습니다.")
    except Exception:
        return create_response(
            status_code=HTTP_404_NOT_FOUND,
            message="채팅방을 찾을 수 없습니다.",
            error=ErrorDetail(
                code="NOT_FOUND",
                message="채팅방을 찾을 수 없습니다.",
                details="Thread not found"
            ).to_dict()
        )


class ThreadStatusData(BaseModel):
    weather: dict = Field(..., description="날씨 정보")
    recommendedActions: dict = Field(..., description="추천 작업 목록")
    createdAt: dict = Field(..., description="생성 날짜 정보")


@router.get("/{thread_id}/status", response_model=create_response)
async def get_thread_status(memberId: str, thread_id: str):
    """
    특정 채팅방의 상태 정보를 반환합니다.
    """
    try:
        # thread_id 유효성 검증
        try:
            thread = client.beta.threads.retrieve(thread_id=thread_id)
        except Exception as e:
            return create_response(
                status_code=HTTP_404_NOT_FOUND,
                message="채팅방을 찾을 수 없습니다.",
                error=ErrorDetail(
                    code="NOT_FOUND",
                    message="채팅방을 찾을 수 없습니다.",
                    details="Thread not found"
                ).to_dict()
            )
        # 실제 로직 구현 부분 (예: 날씨 정보 조회 등)
        return create_response(status_code=HTTP_200_OK, message="상대 정보가 올바르게 반환 되었습니다.", data={"weather": {
            "temp": "20",
            "skyCondition": "흐림",
            "rainProbability": "70",
            "radinCondition": "비안옴"
        },
            "recommendedActions": {
                "0": "물 주기",
                "1": "비료 주기",
                "2": "영양제 주기"
            },
            "createdAt": {
                "year": 2024,
                "month": 12,
                "day": 14,
            }})
    except HTTPException as e:
        return create_response(
            status_code=HTTP_400_BAD_REQUEST,
            message="상태 정보를 가져오는데 실패했습니다.",
            error=ErrorDetail(
                code="HTTP_ERROR",
                message="요청 처리 중 오류가 발생했습니다.",
                details=str(e.detail)
            ).to_dict()
        )
    except Exception as e:
        return create_response(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            message="상태 정보 조회 중 오류가 발생했습니다.",
            error=ErrorDetail(
                code="SERVER_ERROR",
                message="서버 내부 오류가 발생했습니다.",
                details=str(e)
            ).to_dict()
        )


def get_weather(city):
    # 실제 API나 시스템과 연동된 부분이라고 가정
    return f"{city}의 현재 온도는 23도입니다."


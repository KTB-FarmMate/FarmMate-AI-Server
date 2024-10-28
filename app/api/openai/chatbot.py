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
                    error: Optional[dict[str, str]] = None) -> JSONResponse:
    """통합 응답 생성 함수
    - status_code로 성공/실패 판단 (2xx는 성공, 4xx/5xx는 실패)
    - error는 실패시에만 포함
    """
    content = {
        "message": message
    }

    # 상태 코드가 성공일 경우 (2xx), data만 포함
    if 200 <= status_code < 300:
        content["data"] = data

    # 상태 코드가 실패일 경우 (4xx, 5xx), error만 포함
    else:
        content["error"] = error

    return JSONResponse(
        status_code=status_code,
        content=content
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


if __name__ == "__main__":
    # 함수 정의: function call로 호출될 함수
    # address = "충남 천안시 서북구 성환신흥 2길 50"
    # crop = "감자"
    #
    # thread = client.beta.threads.create()
    #
    # client.beta.threads.messages.create(
    #     thread_id=thread.id,
    #     role="assistant",
    #     content=f"주소 : {address}에서 작물 : {crop}을(를) 재배하고 있습니다.",
    # )
    # Thread 응답 반환
    # Assistant의 응답만 사용할지?
    # 주요 이유 ( 변경 사항, 날씨, 주소는 Assistant 에서 echo 해주기 때문 )

    # 일단 ㄱㄱ
    # thread_hdzYPxNwLUHoouZGRh5ZEoiY
    thread = client.beta.threads.retrieve(thread_id="thread_hdzYPxNwLUHoouZGRh5ZEoiY")

    # AI 응답 생성
    # run = client.beta.threads.runs.create(
    #     thread_id=thread.id,
    #     assistant_id=assistant.id,
    # )
    messages: SyncCursorPage[Message]
    messages = client.beta.threads.messages.list(thread_id=thread.id, order="asc")
    assistant_message = [("assistant" if message.role == "assistant" else "user", message.content[0].text.value) for
                         message in messages]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "주어진 작물에 대한 대화 내용을 분석하여 대시보드에 제공할 정보를 json 형식으로 반환하세요. 날씨 정보는 기능 호출을 통해 사용할 예정이지만, 현재는 온도, 습도, 풍속에 대한 정보를 제공합니다.\n\n대화에서 작업 내용과 각 작업의 우선순위를 추출하여 날씨 정보와 함께 출력해야 합니다. 우선순위는 0부터 3까지 있으며, 3일수록 중요합니다.\n\n# Steps\n\n1. 대화 내용을 분석하여 온도, 습도, 풍속과 같은 날씨 정보를 수집합니다.\n2. 작업 내용과 각 작업의 날짜 및 우선순위를 추출합니다.\n3. 우선순위는 0, 1, 2, 3 중 가장 높을수록 중요합니다.\n4. 수집된 정보를 바탕으로 JSON 형식으로 정리합니다.\n5. 너무 먼 작업에 경우는 사용하지 않고 주간에 대한 할일을 적어주는게 좋음\n\n# Output Format\n\n- JSON 형식으로 반환합니다.\n- 예시:\n  ```json\n  {\n    \"weather\": {\n      \"temp\": \"32\",\n      \"humidity\": \"60\",\n      \"wind speed\": \"12\"\n    },\n    \"works\": {\n      \"0\": {\n        \"name\": \"작업 명\",\n        \"date\": \"작업 시작일 ~ 작업 종료일\",\n        \"priority\": \"우선순위\"\n      },\n    \"1\" : ....\n    }\n  }\n  ```\n- 날씨 정보는 기본값으로 사용하되, 실제 데이터를 기반으로 업데이트하세요.\n- 작업 정보 및 우선순위는 실제 대화에서 추출해 설정하세요.\n\n# Examples\n\n**Example 1:**\n- Input: \"오늘 날씨는 맑고 온도는 32도, 습도는 60%야. 다음 주에 감자 심기를 우선적으로 해야 해.\"\n- Output:\n  ```json\n  {\n    \"weather\": {\n      \"temp\": \"32\",\n      \"humidity\": \"60\",\n      \"wind speed\": \"0\"\n    },\n    \"works\": {\n      \"0\": {\n        \"name\": \"감자 심기\",\n        \"date\": \"2024-10-26 ~ 2024-11-02\",\n        \"priority\": \"3\"\n      }\n     \"1\" : {\n         \"name\" : \"물 주기\"\n         \"date\" : \"2024-11-02 ~ 2024-12-20\",\n         \"priorty\": \"3\"\n      }\n    }\n  }\n  ```\n\n# Notes\n\n- 대화의 문맥을 정확히 이해하여 올바른 정보를 추출하세요.\n- 날씨 정보 수집은 현재 정적이나 추후 기능 호출로 대체될 수 있습니다.\n- 작업 내용이 복잡할 경우, 최대한 간단히 요약하여 제공합니다."
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "본문 : [('assistant', '주소 : 충남 천안시 서북구 성환신흥 2길 50에서 작물 : 감자을(를) 재배하고 있습니다.'), ('user', '감자 키우는 방법에 대해 알려줘'), ('assistant', '감자를 키우는 방법에 대해 다음과 같은 절차를 따를 수 있습니다:\\n\\n1. **싹틔움상 설치**: 감자를 심기 전에 바람이 잘 통하고 서늘하며 물 빠짐이 좋은 곳에 싹틔움상을 만듭니다. PE 필름하우스를 이용하여 바람이 잘 통하도록 하고, 감자를 자른 면이 아래로 향하게 놓고 모래로 덮습니다. 이때 온도를 낮추고 마르지 않도록 볏짚을 덮어주며, 하루에 한 번 물을 주어 촉촉한 상태를 유지합니다. 싹을 틔우는 기간은 10~15일 정도 소요됩니다【5:0†source】.\\n\\n2. **씨감자 준비**: 씨감자는 심기 하루 전이나 2~3시간 전에 충분히 물을 주어 뿌리가 끊어지지 않도록 합니다. 감자를 2~4등분하여 각 절편의 무게가 30~40g 정도 되도록 자릅니다. 절단면은 14~15℃에서 상대습도 85~90%로 유지하여 치유합니다【5:2†source】【5:7†source】.\\n\\n3. **아주심기**: 감자를 심는 방법으로는 1줄 또는 2줄로 심는 방법이 있으며, 2줄로 심는 것이 생육과 수량 면에서 유리합니다. 이랑 폭은 60~75cm로 하고, 포기 사이를 20~30cm로 설정합니다. 비료는 질소 10kg, 인산 8.8kg, 칼륨 13kg을 10a당 주며, 최근에는 감자 전용 복합 비료를 사용하는 것이 편리합니다【5:2†source】【5:3†source】.\\n\\n4. **병해충 방제**: 감자를 심고 나면 전면적으로 발아억제용 제초제를 살포하여 잡초를 방지합니다. 병해충 방제는 동력분무기를 이용하여 효과적으로 수행할 수 있습니다【5:3†source】【5:4†source】.\\n\\n5. **수확**: 감자는 심은 후 60~70일째 수확하는 것이 효율적이며, 수확 시기는 품종에 따라 다를 수 있습니다【5:4†source】.\\n\\n이러한 절차를 통해 감자를 성공적으로 재배할 수 있습니다.'), ('user', '물은 얼마나 줘야해?'), ('assistant', '감자에 물을 주는 방법은 다음과 같습니다:\\n\\n1. **관수 방법**: 감자에 물을 주는 방법으로는 스프링클러, 레인호스 등을 이용한 살수 방법이나 점적호스를 이용한 방울물대기(점적관수)가 있습니다. 경사지에서는 방울물대기나 살수 방법을, 평탄지에서는 방울물대기나 골에 물을 흘려서 주는 것이 효과적입니다【9:6†source】.\\n\\n2. **물 주는 시기**: 감자는 생육 초기부터 덩이줄기 비대기까지 건조한 시기에 물을 주어야 하며, 이 시기에 가뭄이 발생하면 잎줄기 생육과 덩이줄기 비대가 늦어져 수량 감소가 클 수 있습니다. 따라서 수시로 물을 주는 것이 다수확의 지름길입니다【9:6†source】.\\n\\n3. **물 주는 양**: 물을 줄 때는 골에 오랜 시간 물이 고이지 않도록 하여야 하며, 덩이줄기 비대 중기 이전에 물을 주는 것이 중요합니다. 덩이줄기의 비대가 완료되는 시기에 물을 주면 부패를 조장할 수 있으므로 주의해야 합니다【9:6†source】.\\n\\n이러한 방법을 통해 감자에 적절한 수분을 공급할 수 있습니다.'), ('user', '주소를 두정역동 2길 31 로 바꾸고 싶어'), ('assistant', '죄송하지만, 주소 변경에 대한 정보는 제공할 수 없습니다.'), ('user', '지금 24년 10월 26일에 심을 예정이야'), ('assistant', '감자를 심기에 가장 좋은 시기는 지역에 따라 다릅니다. 남부 지방에서는 언 땅이 녹는 2월 중하순부터 3월 상순까지가 적절하며, 중부 지방은 3월 중하순이 좋습니다. 가을에 심는 경우, 10월 26일에 심는 것은 적절할 수 있지만, 생육 기간이 짧아야 하므로 첫 서리가 늦은 지역에서 하는 것이 좋습니다【15:0†source】【15:4†source】.\\n\\n감자를 심기 20~30일 전에 씨감자를 준비하여 휴면을 깨우는 것이 중요합니다. 따라서 10월 26일에 심을 예정이라면, 씨감자는 9월 말에서 10월 초에 준비하는 것이 좋습니다【15:1†source】【15:5†source】.'), ('user', '내 주소의 경우는 언제 심는게 좋아?'), ('assistant', '충남 천안 지역에서 감자를 심기에 적절한 시기는 다음과 같습니다:\\n\\n- **봄감자**: 남부 지방에서는 언 땅이 녹는 2월 중하순부터 3월 상순까지가 적절하며, 중부 지방은 3월 중하순이 좋습니다. 충남 천안은 중부 지방에 해당하므로, 3월 중하순이 적절한 시기입니다【19:5†source】.\\n\\n- **가을감자**: 가을감자는 중부 지방에서 8월 중순에서 하순에 심는 것이 좋습니다. 따라서, 8월 상순에서 중순 사이에 심는 것이 적절합니다【19:8†source】.\\n\\n10월 26일에 심을 예정이라면, 가을감자 재배에 해당하며, 기온이 차차 떨어지고 장마가 끝나는 시기에 심는 것이 유리합니다. 이 시기에 씨감자가 썩지 않도록 주의해야 합니다.')]"
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "```json\n{\n  \"weather\": {\n    \"temp\": \"0\",\n    \"humidity\": \"0\",\n    \"wind speed\": \"0\"\n  },\n  \"works\": {\n    \"0\": {\n      \"name\": \"씨감자 준비\",\n      \"date\": \"2024-09-26 ~ 2024-10-26\",\n      \"priority\": \"3\"\n    },\n    \"1\": {\n      \"name\": \"감자 심기\",\n      \"date\": \"2024-10-26 ~ 2024-10-26\",\n      \"priority\": \"3\"\n    },\n    \"2\": {\n      \"name\": \"물 주기 및 관리\",\n      \"date\": \"2024-10-27 ~ 2024-12-20\",\n      \"priority\": \"2\"\n    }\n  }\n}\n```"
                    }
                ]
            }
        ],
        temperature=1,
        max_tokens=2048,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Determine weather in my location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state e.g. San Francisco, CA"
                            },
                            "unit": {
                                "type": "string",
                                "enum": [
                                    "c",
                                    "f"
                                ]
                            }
                        },
                        "additionalProperties": false,
                        "required": [
                            "location",
                            "unit"
                        ]
                    },
                    "strict": true
                }
            }
        ],
        parallel_tool_calls=true,
        response_format={
            "type": "text"
        }
    )
    exit(0)
    # 응답 완료 대기
    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=request.threadId, run_id=run.id)
        if run_status.status == "completed":
            break
        elif run_status.status == "failed":
            raise HTTPException(status_code=HTTP_502_BAD_GATEWAY, detail=f"응답 생성에 실패했습니다: {run_status.last_error}")
        elif run_status.status == "cancelled":
            raise HTTPException(status_code=HTTP_409_CONFLICT, detail=f"응답 생성이 취소되었습니다: {run_status.last_error}")
        elif run_status.status == "expired":
            raise HTTPException(status_code=HTTP_408_REQUEST_TIMEOUT,
                                detail=f"응답 생성이 시간 초과되었습니다: {run_status.last_error}")
        time.sleep(1)

    # 최신 AI 응답 가져오기
    messages = client.beta.threads.messages.list(thread_id=request.threadId, order="desc", limit=1)

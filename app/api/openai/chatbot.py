from typing import List, Any, Optional, Generic, TypeVar
import re
import time
from xmlrpc.client import INTERNAL_ERROR

import requests
from enum import Enum
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Response
from openai.pagination import SyncCursorPage
from pydantic import BaseModel, Field, field_validator, ValidationError
# from openai import OpenAI, Client, OpenAIError, APIError
import openai
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
import json
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.api.weather.weather import kakao_service

import socket

DEBUG = True

BE_BASE_URL = "http://15.164.175.127:8080/api"

router = APIRouter()

# OpenAI API 클라이언트 생성
client: openai.Client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

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
    cropId: int = Field(-1, description="재배할 작물의 고유식별자")
    cropName: str = Field("", description="재배할 작물 이름")
    address: str = Field("", description="농사를 짓는 지역 주소")
    plantedAt: str = Field("", description="작물을 심은 날짜")


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

        crop_id = request.cropId
        print(crop_id)
        if not isinstance(crop_id, int):
            raise ValueError('작물ID는 정수형이어야 합니다.')
        if crop_id == -1:
            raise ValueError("작물ID를 입력해야 합니다.")

        crop = request.cropName

        if not isinstance(crop, str):
            raise ValueError('작물명은 문자열이어야 합니다.')
        if not crop.strip() or re.search(r'[^\w\s]', crop):
            raise ValueError(f"올바른 작물명을 입력해야 합니다.")

        address = request.address

        if not isinstance(address, str):
            raise ValueError('주소는 문자열이어야 합니다.')
        if not address.strip() or not re.match(r'^[가-힣a-zA-Z0-9\s()\-_,.]+$', request.address):
            raise ValueError("올바른 주소를 입력해야 합니다.")


        plantedAt = request.plantedAt

        if not isinstance(plantedAt, str):
            raise ValueError('심은 날짜는 문자열이어야 합니다.')
        if not plantedAt.strip():
            raise ValueError("심은 날짜를 입력해야 합니다.")
        try:
            print(plantedAt)
            datetime.strptime(plantedAt, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"날짜 형식이 올바르지 않습니다.")

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="assistant",
            content=f"[시스템 메시지] 사용자는 심은날짜 : {plantedAt}, 주소 : {address}에서 작물 : {crop}을(를) 재배하고 있습니다.",
        )

        request_data = {
            "address": address,
            "cropId": crop_id,
            "plantedAt": plantedAt,
            "threadId": str(thread.id)}
        print(request_data)
        req = requests.post(f"{BE_BASE_URL}/members/{memberId}/threads", json=request_data)

        if req.status_code != 200:
            raise HTTPException(
                status_code=req.status_code,
                detail=req.json().get("details", "백엔드 서버 요청 실패")
            )

        return create_response(status_code=HTTP_201_CREATED,
                               message="채팅방이 성공적으로 생성되었습니다.",
                               data={"threadId": thread.id})

    except ValueError as e:
        return create_response(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            message="입력값 검증 실패",
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="입력값이 유효하지 않습니다.",
                details=str(e)
            ).to_dict()
        )

    except openai.APIError as e:
        return create_response(
            status_code=HTTP_502_BAD_GATEWAY,
            message="OpenAI 서비스 오류",
            error=ErrorDetail(
                code="OPENAI_API_ERROR",
                message="OpenAI 서비스 연동 중 오류가 발생했습니다.",
                details=str(e)
            ).to_dict()
        )

    except requests.Timeout:
        return create_response(
            status_code=HTTP_504_GATEWAY_TIMEOUT,
            message="백엔드 서버 응답 시간 초과",
            error=ErrorDetail(
                code="BACKEND_TIMEOUT",
                message="백엔드 서버가 응답하지 않습니다.",
                details="Request to backend server timed out"
            ).to_dict()
        )

    except requests.RequestException as e:
        return create_response(
            status_code=HTTP_502_BAD_GATEWAY,
            message="백엔드 서버 연결 실패",
            error=ErrorDetail(
                code="BACKEND_CONNECTION_ERROR",
                message="백엔드 서버와 통신 중 오류가 발생했습니다.",
                details=str(e)
            ).to_dict()
        )

    except HTTPException as e:
        return create_response(
            status_code=e.status_code,
            message="요청 처리 실패",
            error=ErrorDetail(
                code="REQUEST_FAILED",
                message="요청을 처리할 수 없습니다.",
                details=str(e.detail)
            ).to_dict()
        )

    except Exception as e:
        return create_response(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            message="서버 내부 오류",
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="예기치 않은 오류가 발생했습니다.",
                details=str(e)
            ).to_dict()
        )


class Role(str, Enum):
    USER = "user"
    ASSITANT = "assistant"


class MessageData(BaseModel):
    """
    채팅방의 메시지 구조를 정의합니다.
    """
    role: Role = Field(..., description="메시지 작성자 (assistant 또는 user)")
    text: str = Field(..., description="메시지 내용")

    def to_dict(self):
        """객체를 딕셔너리로 변환"""
        return {
            "role": self.role,
            "text": self.text,
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
        client.beta.threads.retrieve(thread_id=thread_id)
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
    except openai.AuthenticationError as e:
        return create_response(
            status_code=HTTP_401_UNAUTHORIZED,
            message="유효하지 않은 OPENAI_API_KEY",
            error=ErrorDetail(
                code=e.type,
                message=e.message,
                details=str(e)
            ).to_dict()
        )
    except openai.NotFoundError as e:
        return create_response(
            status_code=HTTP_404_NOT_FOUND,
            message="유효하지 않은 채팅방 ID",
            error=ErrorDetail(
                code=e.type,
                message=e.message,
                details=str(e)
            ).to_dict()
        )
    except HTTPException as e:
        return create_response(
            status_code=HTTP_400_BAD_REQUEST,
            message="채팅방 정보를 가져오는데 실패했습니다.",
            error=ErrorDetail(
                code="HTTP_ERROR",
                message="요청 처리 중 오류가 발생했습니다.",
                details=str(e)
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


class ThreadStatus:
    """
    PTY (강수 형태): 0
    강수 형태를 나타내며, 0은 강수 없음을 의미합니다.

    REH (습도): 50
    현재 습도를 나타내며, 50은 습도가 50%임을 의미합니다.

    RN1 (1시간 강수량): 0
    지난 1시간 동안의 강수량을 나타내며, 0은 강수량이 없음을 의미합니다.

    T1H (기온): 17.6
    현재 기온을 나타내며, 17.6°C임을 의미합니다.

    UUU (동서 방향 바람 성분): -1
    동서 방향의 바람 성분을 나타내며, -1 m/s로 서쪽에서 동쪽으로 부는 바람을 의미합니다 (음수는 서풍을 의미).

    VEC (풍향): 54
    풍향을 나타내며, 54°는 북동쪽에서 불어오는 바람임을 의미합니다.

    VVV (남북 방향 바람 성분): -0.7
    남북 방향의 바람 성분을 나타내며, -0.7 m/s로 남쪽에서 북쪽으로 부는 바람을 의미합니다 (음수는 남풍을 의미).

    WSD (풍속): 1.4
    풍속을 나타내며, 1.4 m/s의 속도로 바람이 불고 있음을 의미합니다.

    """

    def __init__(self, model="gpt-4o-mini"):
        self.tool = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Converts an address to geographic coordinates and retrieves weather information for those coordinates",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "address": {
                                "type": "string",
                                "description": "The address to be converted to coordinates"
                            }
                        },
                        "required": ["address"],
                        "additionalProperties": False
                    }
                }
            }
        ]
        self.message = None
        self.model = model
        self.directions = [
            "남", "남남서", "남서", "서남서", "서", "서북서", "북서", "북북서",
            "북", "북북동", "북동", "동북동", "동", "동남동", "남동", "남남동"
        ]

    def set_message(self, message):
        self.message = message

    # 하늘 상태와 비 여부 설정 함수
    def get_sky_condition(self, pty_value):
        match pty_value:
            case 0:
                return "맑음", "비안옴"
            case 1:
                return "비", "비옴"
            case 2:
                return "비/눈", "비/눈"
            case 3:
                return "눈", "눈옴"
            case 5:
                return "빗방울", "비옴"
            case 6:
                return "빗방울눈날림", "비옴"
            case 7:
                return "눈날림", "눈옴"
            case _:
                return "알 수 없음", "알 수 없음"

    # 풍향 설정 함수
    def get_wind_direction(self, vec_value):
        idx = (int((float(vec_value) + 22.5) // 22.5) + 8) % 16
        return self.directions[idx]

    def get_weather(self):
        response = client.chat.completions.create(
            model=self.model,
            messages=self.message,
            temperature=0,
            max_tokens=2048,
            top_p=0,
            frequency_penalty=0,
            presence_penalty=0,
            tools=self.tool,
            parallel_tool_calls=True,
            response_format={
                "type": "text"
            },
            tool_choice="required"  # 함수 호출을 강제 실행
        )
        if response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            arguments = json.loads(tool_call.function.arguments)
            address = arguments.get("address")
            weather_data = kakao_service.convert_address_to_coordinate(address)

            # skyCondition과 rainCondition 값을 설정
            skyCondition, rainCondition = self.get_sky_condition(weather_data["PTY"])

            # windDirection 값을 설정
            windDirection = self.get_wind_direction(weather_data["VEC"])

            weather = {
                "temp": weather_data["T1H"],
                "skyCondition": skyCondition,
                "rainProbability": weather_data["RN1"],
                "rainCondition": rainCondition,
                "humidity": weather_data["REH"],
                "windSpeed": weather_data["WSD"],
                "windDirection": windDirection
            }

            return weather


@router.get("/{thread_id}/status", response_model=create_response)
async def get_thread_status(memberId: str, thread_id: str):
    """
    특정 채팅방의 상태 정보를 반환합니다.
    """

    try:
        # thread_id 유효성 검증
        try:
            thread = client.beta.threads.retrieve(thread_id=thread_id)

            messages: SyncCursorPage[Message]
            messages = client.beta.threads.messages.list(thread_id=thread.id, order="asc")

            assistant_message = [{"role": "assistant", "content": message.content[0].text.value} for message in messages
                                 if
                                 message.role == "assistant" and "[시스템 메시지]" in message.content[0].text.value]
            # tools 정의
            print(assistant_message)
            thread_status = ThreadStatus()
            thread_status.set_message(assistant_message)
            weather_data = thread_status.get_weather()
            print(weather_data)
            # 실제 로직 구현 부분 (예: 날씨 정보 조회 등)
            return create_response(
                status_code=HTTP_200_OK,
                message="상대 정보가 올바르게 반환 되었습니다.",
                data={
                    "weather": weather_data,
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

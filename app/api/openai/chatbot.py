# 타입과 유틸리티 관련 모듈
from typing import List, Any, Optional, Generic, TypeVar
import re
import time
import json
from enum import Enum
from datetime import datetime
from httpx import AsyncClient

# HTTP 및 API 관련 모듈
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator, ValidationError
from starlette.responses import JSONResponse
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_408_REQUEST_TIMEOUT, HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_404_NOT_FOUND, HTTP_409_CONFLICT,
)

# OpenAI 관련 모듈
from openai.pagination import SyncCursorPage
import openai

# 프로젝트 내 모듈
from app.core.config import settings
from app.api.weather.weather import kakao_service
from app.utils.response import create_response
from app.models.error import ErrorDetail

# 네트워크 관련 모듈
import socket

DEBUG = True

BE_BASE_URL = "http://farmmate.net/api"

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
    cropId: int = Field(-1, description="재배할 작물의 고유식별자")
    cropName: str = Field("", description="재배할 작물 이름")
    address: str = Field("", description="농사를 짓는 지역 주소")
    plantedAt: str = Field("", description="작물을 심은 날짜")


class ThreadCreateData(BaseModel):
    threadId: str = Field(..., description="생성된 채팅방의 고유 식별자")


@router.post("")
async def create_thread(memberId: str, request: CreateThreadRequest) -> JSONResponse:
    """새로운 채팅방(Thread)을 생성하고 초기 메시지를 추가합니다."""
    thread = client.beta.threads.create()

    crop_id = request.cropId
    if crop_id == -1:
        raise ValueError("작물ID를 입력해야 합니다.")

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

    request_data = {
        "address": address,
        "cropId": str(crop_id),
        "plantedAt": plantedAt,
        "threadId": str(thread.id)
    }

    async with AsyncClient() as Client:
        req = await Client.post(f"{BE_BASE_URL}/members/{memberId}/threads", json=request_data)
        if req.status_code == HTTP_409_CONFLICT:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail=req.json(),
            )
        if req.status_code != HTTP_201_CREATED:
            raise HTTPException(
                status_code=req.status_code,
                detail=req.json()
            )
    return create_response(
        status_code=HTTP_201_CREATED,
        message="채팅방이 성공적으로 생성되었습니다.",
        data={"threadId": thread.id}
    )


@router.get("")
async def get_threads(memberId: str):
    async with AsyncClient() as Client:
        req = await Client.get(f"{BE_BASE_URL}/members/{memberId}/threads")
        if req.status_code == HTTP_200_OK:
            req_json = req.json()
            # if not req_json:
            #     raise HTTPException(
            #         status_code=HTTP_404_NOT_FOUND,
            #         detail=req_json
            #     )
            return create_response(
                status_code=HTTP_200_OK,
                message="채팅방 정보를 올바르게 가져왔습니다.",
                data={"threads": req_json}
            )
        else:
            raise HTTPException(
                status_code=req.status_code,
                detail=req.json()
            )


class Role(str, Enum):
    USER = "user"
    ASSITANT = "assistant"

    def __str__(self):
        return self.value.upper()  # 대문자로 반환

class MessageData(BaseModel):
    """채팅방의 메시지 구조를 정의합니다."""
    role: Role = Field(..., description="메시지 작성자 (assistant 또는 user)")
    text: str = Field(..., description="메시지 내용")

    def to_dict(self):
        return {
            "role": str(self.role),
            "text": self.text,
        }


@router.get("/{thread_id}")
async def get_thread(memberId: str, thread_id: str):
    """특정 채팅방의 메시지 목록을 반환합니다."""
    thread = client.beta.threads.retrieve(thread_id=thread_id)
    messages = client.beta.threads.messages.list(thread_id=thread.id, order="asc")

    messages_data = [
        MessageData(
            role=Role(message.role),
            text=message.content[0].text.value
        ).to_dict()
        for message in messages
        if message.content is not None and "[시스템 메시지]" not in message.content[0].text.value
    ]

    return create_response(
        status_code=HTTP_200_OK,
        message="채팅방 정보를 가져왔습니다.",
        data={"threadId": thread_id, "messages": messages_data}
    )


class MessageRequest(BaseModel):
    """사용자가 보낸 메시지 정보를 담는 모델입니다."""
    message: str = Field("", description="사용자가 보낸 메시지 내용")


@router.post("/{thread_id}")
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
    cropId: int = Field(-1, description="변경할 작물 ID")
    address: str = Field("", description="변경할 주소")
    plantedAt: str = Field(None, description="변경할 심은 날짜 (YYYY-MM-DD 형식)")


@router.patch("/{thread_id}")
async def modify_message(memberId: str, thread_id: str, request: ModifyMessageRequest):
    """특정 채팅방의 주소 정보를 수정합니다."""
    if not thread_id:
        raise ValueError("채팅방 ID가 누락되었습니다.")
    if not request.address:
        raise ValueError("주소가 누락되었습니다.")
    if request.cropId == -1:
        raise ValueError("작물 ID가 누락되었습니다.")
    if not request.plantedAt:
        raise ValueError("심은 날짜가 누락되었습니다.")
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
    # run = client.beta.threads.runs.create(
    #     thread_id=thread.id,
    #     assistant_id=assistant.id,
    #
    # )
    #
    # while True:
    #     run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    #     if run_status.status == "completed":
    #         break
    #     elif run_status.status in ["failed", "cancelled", "expired"]:
    #         raise HTTPException(
    #             status_code=HTTP_500_INTERNAL_SERVER_ERROR,
    #             detail=f"AI 응답 생성 실패: {run_status.status}"
    #         )
    #     time.sleep(1)

    request_data = {
        "address": request.address,
        "cropId": request.cropId,
        "plantedAt": request.plantedAt,
        "threadId": str(thread.id)
    }

    req = requests.patch(f"{BE_BASE_URL}/members/{memberId}/threads/{thread.id}", json=request_data)

    if req.status_code != 200:
        raise HTTPException(
            status_code=req.status_code,
            detail=req.json().get("details", "백엔드 서버 요청 실패")
        )
    return create_response(
        status_code=HTTP_200_OK,
        message="채팅방 정보 수정 완료",
        data={"message": "주소가 성공적으로 변경되었습니다."}
    )


@router.delete("/{thread_id}")
async def delete_thread(memberId: str, thread_id: str):
    """특정 채팅방을 삭제합니다."""
    async with AsyncClient() as Client:
        req = await Client.delete(f"{BE_BASE_URL}/members/{memberId}/threads/{thread_id}")
        if req.status_code != HTTP_204_NO_CONTENT:
            raise HTTPException(
                status_code=req.status_code,
                detail=req.json()
            )
        client.beta.threads.delete(thread_id)
    return create_response(status_code=HTTP_204_NO_CONTENT, message="채팅방이 성공적으로 삭제되었습니다.")


class ThreadStatus:
    def __init__(self, model="gpt-4o-mini"):
        self.tool = [{
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
        }]
        self.message = None
        self.model = model
        self.directions = [
            "남", "남남서", "남서", "서남서", "서", "서북서", "북서", "북북서",
            "북", "북북동", "북동", "동북동", "동", "동남동", "남동", "남남동"
        ]

    def set_message(self, message):
        self.message = message

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
            response_format={"type": "text"},
            tool_choice="required"
        )

        if response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            arguments = json.loads(tool_call.function.arguments)
            address = arguments.get("address")
            weather_data = kakao_service.convert_address_to_coordinate(address)

            skyCondition, rainCondition = self.get_sky_condition(weather_data["PTY"])
            windDirection = self.get_wind_direction(weather_data["VEC"])

            return {
                "temp": weather_data["T1H"],
                "skyCondition": skyCondition,
                "rainProbability": weather_data["RN1"],
                "rainCondition": rainCondition,
                "humidity": weather_data["REH"],
                "windSpeed": weather_data["WSD"],
                "windDirection": windDirection
            }


@router.get("/{thread_id}/status")
async def get_thread_status(memberId: str, thread_id: str):
    """특정 채팅방의 상태 정보를 반환합니다."""
    thread = client.beta.threads.retrieve(thread_id=thread_id)
    messages = client.beta.threads.messages.list(thread_id=thread.id, order="asc")

    assistant_message = [
        {"role": "assistant", "content": message.content[0].text.value}
        for message in messages
        if message.role == "assistant" and "[시스템 메시지]" in message.content[0].text.value
    ]

    thread_status = ThreadStatus()
    thread_status.set_message(assistant_message)
    weather_data = thread_status.get_weather()

    return create_response(
        status_code=HTTP_200_OK,
        message="상태 정보가 올바르게 반환되었습니다.",
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
            }
        }
    )

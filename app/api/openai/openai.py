from typing import List

import time

from fastapi import APIRouter, HTTPException, status, Response
from pydantic import BaseModel, Field
from openai import OpenAI
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_409_CONFLICT, \
    HTTP_408_REQUEST_TIMEOUT, HTTP_502_BAD_GATEWAY

from app.core.config import settings

router = APIRouter()

# OpenAI API 클라이언트 생성
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# ASSISTANT_ID를 사용하여 Assistant 인스턴스 가져오기
assistant = client.beta.assistants.retrieve(assistant_id=settings.ASSISTANT_ID)


class CreateThreadRequest(BaseModel):
    crop: str = Field(..., description="재배할 작물 이름")
    address: str = Field(..., description="농사를 짓는 지역 주소")


@router.post("/")
async def create_thread(request: CreateThreadRequest):
    """
    새로운 채팅방(Thread)을 생성하고 초기 메시지를 추가합니다.

    Returns:
        dict: 생성된 채팅방의 고유 식별자(ID)를 반환합니다.
    """
    try:
        thread = client.beta.threads.create()

        # 초기 메시지 생성
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"저는 {request.address}에서 {request.crop}을(를) 재배하고 있습니다.",
        )

        return {"success": True, "threadId": thread.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class Message(BaseModel):
    """
    채팅방의 메시지 구조를 정의합니다.

    Attributes:
        id (str): 메시지의 고유 식별자
        role (str): 메시지 작성자 (assistant 또는 user)
        content (str): 메시지 내용
        created_at (str): 메시지 생성 시간
    """
    id: str = Field(..., description="OpenAI Thread 내 메시지의 고유 식별자")
    role: str = Field(..., description="메시지 작성자 (assistant 또는 user)")
    content: str = Field(..., description="메시지 내용")
    created_at: str = Field(..., description="메시지 생성 시간")


class ThreadResponse(BaseModel):
    """
    채팅방의 응답 형식을 정의합니다.

    Attributes:
        threadId (str): 채팅방의 고유 식별자
        messages (List[Message]): 채팅방의 메시지 목록
    """
    threadId: str = Field(..., description="채팅방의 고유 식별자")
    messages: List[Message] = Field(..., description="채팅방의 모든 메시지")


@router.get("/{thread_id}")
async def get_thread(thread_id: str):
    """
    특정 채팅방의 메시지 목록을 반환합니다.

    Args:
        thread_id (str): 조회할 채팅방의 고유 식별자

    Returns:
        dict: 채팅방의 고유 식별자와 메시지 목록을 반환합니다.
    """
    try:
        # 채팅방 존재 여부 확인
        try:
            client.beta.threads.retrieve(thread_id=thread_id)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="유효하지 않은 채팅방 ID입니다.")

        # 모든 메시지 가져오기
        messages = client.beta.threads.messages.list(thread_id=thread_id, order="asc")

        # 메시지 데이터 구성
        messages_data = [
            Message(
                id=message.id,
                role=message.role,
                content=message.content[0].text.value if message.content else "",
                created_at=time.strftime('%Y-%m-%d %H:%M', time.localtime(message.created_at))
            )
            for message in messages.data
        ]

        return {"success": True, "threadId": thread_id, "messages": messages_data}

    except Exception as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))


class MessageRequest(BaseModel):
    """
    사용자가 보낸 메시지 정보를 담는 모델입니다.

    Attributes:
        threadId (str): 메시지를 보낼 채팅방의 고유 식별자
        message (str): 사용자가 보낸 메시지 내용
    """
    threadId: str = Field(..., description="채팅방의 고유 식별자")
    message: str = Field(..., description="사용자가 보낸 메시지 내용")


@router.post("/message")
async def send_message(request: MessageRequest):
    """
    특정 채팅방에 메시지를 전송하고 AI의 응답을 생성합니다.

    Args:
        request (MessageRequest): 채팅방 ID와 사용자 메시지를 포함합니다.

    Returns:
        dict: AI의 응답 메시지를 반환합니다.
    """
    try:
        # 채팅방 ID 검증
        if not request.threadId:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="채팅방 ID가 누락되었습니다.")

        # 기존 채팅방 가져오기
        thread = client.beta.threads.retrieve(thread_id=request.threadId)

        # 사용자 메시지 추가
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=request.message,
        )

        # AI 응답 생성
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
        )

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

        if not messages.data:
            return Response(status_code=204)  # No Content

        latest_message = messages.data[0]
        if latest_message.role == "assistant":
            for content in latest_message.content:
                if content.type == 'text':
                    return {"threadId": request.threadId, "message": content.text.value}

        return Response(status_code=204)  # No Content

    except HTTPException as e:
        raise e
    except Exception as e:
        # 기타 모든 예외는 500 에러로 처리
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{thread_id}")
async def delete_thread(thread_id: str):
    """
    특정 채팅방을 삭제합니다.

    Args:
        thread_id (str): 삭제할 채팅방의 고유 식별자

    Returns:
        Response: 성공 시 204 No Content를 반환합니다.
    """
    try:
        client.beta.threads.delete(thread_id)
        return Response(status_code=204)  # No Content
    except Exception:
        raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")

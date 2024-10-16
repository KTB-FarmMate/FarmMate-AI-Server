from typing import Dict, Any, List
from pydantic import (
    BaseModel,
    ValidationError,
    ValidationInfo,
    field_validator,
    Field
)
from fastapi import APIRouter, HTTPException, status, Request, Query, Response
from fastapi.responses import JSONResponse
from app.core.config import settings
from openai import OpenAI
import time

router = APIRouter()

# OpenAI의 API 클라이언트를 생성
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Assistant 사용을 위해 ASSISTANT_ID를 통해 retrieve 하여 가져온다
assistant = client.beta.assistants.retrieve(assistant_id=settings.ASSISTANT_ID)


@router.post("/createThread")
async def createThread() -> dict:
    """
    새로운 Thread(채팅방)를 생성하는 함수 \n
    :return: 생성된 Thread(채팅방)의 고유식별자(ID)를 반환 \n
    """
    try:
        thread = client.beta.threads.create()
        return {"threadId": thread.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class Message(BaseModel):
    """
    Thread 요청시, Message의 실 구성
    id : 메시지의 고유 번호
    role : 메시지 작성자 ( assistant, user )
    content : 메시지의 내용
    """
    id: str
    role: str
    content: str


class ThreadResponse(BaseModel):
    """
    Thread 내용의 반환 형태
    threadId : 채팅방(Thread)의 고유식별자
    messages : 채팅방에서 이루어진 대화 목록
    """
    threadId: str
    messages: List[Message]


@router.get("/getThread", response_model=ThreadResponse)
async def get_thread(threadId: str = Query(..., description="채팅방 ID")):
    """
    특정 채팅방(Thread)의 메시지 목록을 반환하는 함수 \n
    :param threadId: str = 조회할 채팅방의 고유식별자 \n
    :return: 채팅방의 고유식별자와 해당 채팅방의 메시지 목록을 반환 \n
    """
    if not threadId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="threadId는 필수 요소 입니다.")

    # 스레드의 모든 메시지 가져오기
    thread = client.beta.threads.retrieve(thread_id=threadId)
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")

    messages = client.beta.threads.messages.list(thread_id=threadId, order="asc")

    # 메시지 데이터 정리
    messages_data = [
        {
            'id': message.id,
            'role': message.role,
            'content': message.content[0].text.value if message.content else "",
        }
        for message in messages.data
    ]

    return {
        'threadId': threadId,
        'messages': messages_data
    }


class MessageRequest(BaseModel):
    """
    요청자로부터 전달된 Message 정보
    """
    threadId: str
    message: str


@router.post("/sendMessage")
async def sendMessage(request: MessageRequest):
    """
    사용자가 특정 Thread에 메시지를 전송하고, 이에 대한 AI의 답변을 생성하는 함수 \n
    :param request: MessageRequest 객체로, 사용자가 전송할 메시지 및 Thread ID를 포함 \n
        - threadId (str): 메시지를 보낼 Thread의 고유 식별자 \n
        - message (str): 사용자가 전송하는 메시지 내용 \n
    :return: AI의 답변을 포함한 JSON 객체를 반환. 답변이 없거나 문제가 있을 경우 204 No Content 또는 오류 메시지 반환 \n
        - threadId (str): 해당 Thread의 고유 식별자 \n
        - content (str): AI가 생성한 텍스트 응답 \n
    """
    try:
        threadId = request.threadId
        message = request.message

        # threadId 없을 경우, BAD_REQUEST 반환
        if not threadId:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="전달된 Thread ID가 없습니다.")

        # threadId 있어서, 기존에 존재하는 thread를 가져옴
        thread = client.beta.threads.retrieve(thread_id=threadId)

        # threadId 해당하는 채팅방에 user가 전달한 message를 기반으로 message 생성
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"{message}",
        )

        # 답변 생성
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
        )

        # Run 완료 대기
        while True:
            run = client.beta.threads.runs.retrieve(thread_id=threadId, run_id=run.id)
            if run.status == "completed":
                break
            elif run.status in ["failed", "cancelled", "expired"]:
                return JsonResponse({'error': f"Run failed: {run.last_error}"})
            time.sleep(1)

        # 최신 응답 가져오기
        messages = client.beta.threads.messages.list(thread_id=threadId, order="desc", limit=1)

        # 메시지가 없는 경우
        if not messages.data:
            return Response(status_code=204)  # 데이터가 없을 때 204 반환

        if messages.data:
            message = messages.data[0]
            if message.role == "assistant":
                for content in message.content:
                    if content.type == 'text':
                        return {'threadId': threadId, 'content': content.text.value}
        return Response(status_code=204)  # 데이터가 없을 때 204 반환
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class DeleteThreadRequest(BaseModel):
    """
    Thread Delete 요청 형식
    """
    threadId: str = Field(..., description="삭제할 스레드의 고유 식별자")


@router.post("/deleteThread")
async def deleteThread(request: DeleteThreadRequest):
    """
    특정 Thread(채팅방)를 삭제하는 함수 \n
    :param request: DeleteThreadRequest 객체로, 삭제할 Thread의 고유식별자를 포함 \n
    :return: 성공 시 204 No Content 응답을 반환 \n
    """
    try:
        client.beta.threads.delete(request.threadId)
        return Response(status_code=204)  # 성공 시 204 No Content 반환
    except Exception as e:
        raise HTTPException(status_code=500, detail="Thread가 존재하지 않습니다.")

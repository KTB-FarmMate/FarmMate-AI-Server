from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_408_REQUEST_TIMEOUT,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_502_BAD_GATEWAY,
    HTTP_504_GATEWAY_TIMEOUT, HTTP_204_NO_CONTENT
)
import openai
from requests.exceptions import RequestException, Timeout

from app.models.error import ErrorDetail
from app.utils.response import create_response


def get_status_message(status_code: int) -> str:
    """상태 코드에 따른 적절한 메시지 반환"""
    return {
        HTTP_204_NO_CONTENT: "반환된 값이 없습니다.",
        HTTP_400_BAD_REQUEST: "잘못된 요청입니다.",
        HTTP_401_UNAUTHORIZED: "인증이 필요합니다.",
        HTTP_403_FORBIDDEN: "권한이 없습니다.",
        HTTP_404_NOT_FOUND: "리소스를 찾을 수 없습니다.",
        HTTP_422_UNPROCESSABLE_ENTITY: "입력값 검증에 실패했습니다.",
        HTTP_500_INTERNAL_SERVER_ERROR: "서버 내부 오류가 발생했습니다.",
    }.get(status_code, "요청을 처리할 수 없습니다.")


def get_error_code(status_code: int) -> str:
    """상태 코드에 따른 에러 코드 반환"""
    return {
        HTTP_204_NO_CONTENT: "NO_CONTENT",
        HTTP_400_BAD_REQUEST: "BAD_REQUEST",
        HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
        HTTP_403_FORBIDDEN: "FORBIDDEN",
        HTTP_404_NOT_FOUND: "NOT_FOUND",
        HTTP_422_UNPROCESSABLE_ENTITY: "VALIDATION_ERROR",
        HTTP_500_INTERNAL_SERVER_ERROR: "INTERNAL_SERVER_ERROR",
    }.get(status_code, "HTTP_ERROR")


def add_exception_handlers(app: FastAPI):
    @app.exception_handler(ValueError)
    async def validation_exception_handler(request: Request, exc: ValueError):
        return create_response(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            message="입력값 검증 실패",
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="입력값이 유효하지 않습니다.",
                details=str(exc)
            ).to_dict()
        )

    @app.exception_handler(openai.APIError)
    async def openai_exception_handler(request: Request, exc: openai.APIError):
        return create_response(
            status_code=HTTP_502_BAD_GATEWAY,
            message="OpenAI 서비스 오류",
            error=ErrorDetail(
                code="OPENAI_API_ERROR",
                message="OpenAI 서비스 연동 중 오류가 발생했습니다.",
                details=str(exc)
            ).to_dict()
        )

    @app.exception_handler(openai.AuthenticationError)
    async def openai_auth_exception_handler(request: Request, exc: openai.AuthenticationError):
        return create_response(
            status_code=HTTP_401_UNAUTHORIZED,
            message="OPENAI 서비스 인증 실패",
            error=ErrorDetail(
                code=exc.type,
                message="유효하지 않은 OPENAI_API_KEY",
                details=str(exc)
            ).to_dict()
        )

    @app.exception_handler(openai.NotFoundError)
    async def openai_not_found_exception_handler(request: Request, exc: openai.NotFoundError):
        return create_response(
            status_code=HTTP_404_NOT_FOUND,
            message="유효하지 않은 리소스 ID",
            error=ErrorDetail(
                code=exc.type,
                message="올바르지 않은 Thread ID입니다.",
                details=str(exc)
            ).to_dict()
        )

    @app.exception_handler(Timeout)
    async def timeout_exception_handler(request: Request, exc: Timeout):
        return create_response(
            status_code=HTTP_504_GATEWAY_TIMEOUT,
            message="백엔드 서버 응답 시간 초과",
            error=ErrorDetail(
                code="BACKEND_TIMEOUT",
                message="백엔드 서버가 응답하지 않습니다.",
                details="Request to backend server timed out"
            ).to_dict()
        )

    @app.exception_handler(RequestException)
    async def request_exception_handler(request: Request, exc: RequestException):
        return create_response(
            status_code=HTTP_502_BAD_GATEWAY,
            message="백엔드 서버 연결 실패",
            error=ErrorDetail(
                code="BACKEND_CONNECTION_ERROR",
                message="백엔드 서버와 통신 중 오류가 발생했습니다.",
                details=str(exc)
            ).to_dict()
        )

    @app.exception_handler(HTTPException)  # Exception 대신 HTTPException
    async def http_exception_handler(request: Request, exc: HTTPException):
        return create_response(
            status_code=exc.status_code,
            message=get_status_message(exc.status_code),  # 상태 코드에 따른 적절한 메시지
            error=ErrorDetail(
                code=get_error_code(exc.status_code),  # 상태 코드에 따른 에러 코드
                message=str(exc.detail),
                details=None  # 필요한 경우에만 상세 정보 제공
            ).to_dict()
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return create_response(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            message="서버 내부 오류",
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="예기치 않은 오류가 발생했습니다.",
                details=str(exc)
            ).to_dict()
        )

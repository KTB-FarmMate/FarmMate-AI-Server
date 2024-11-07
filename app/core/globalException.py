from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import openai
from requests.exceptions import RequestException, Timeout

from app.models.error import ErrorDetail
from app.utils.response import create_response

from starlette.status import (
    HTTP_100_CONTINUE,
    HTTP_101_SWITCHING_PROTOCOLS,
    HTTP_102_PROCESSING,
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_203_NON_AUTHORITATIVE_INFORMATION,
    HTTP_204_NO_CONTENT,
    HTTP_205_RESET_CONTENT,
    HTTP_206_PARTIAL_CONTENT,
    HTTP_207_MULTI_STATUS,
    HTTP_208_ALREADY_REPORTED,
    HTTP_226_IM_USED,
    HTTP_300_MULTIPLE_CHOICES,
    HTTP_301_MOVED_PERMANENTLY,
    HTTP_302_FOUND,
    HTTP_303_SEE_OTHER,
    HTTP_304_NOT_MODIFIED,
    HTTP_305_USE_PROXY,
    HTTP_307_TEMPORARY_REDIRECT,
    HTTP_308_PERMANENT_REDIRECT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_402_PAYMENT_REQUIRED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_406_NOT_ACCEPTABLE,
    HTTP_407_PROXY_AUTHENTICATION_REQUIRED,
    HTTP_408_REQUEST_TIMEOUT,
    HTTP_409_CONFLICT,
    HTTP_410_GONE,
    HTTP_411_LENGTH_REQUIRED,
    HTTP_412_PRECONDITION_FAILED,
    HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    HTTP_414_REQUEST_URI_TOO_LONG,
    HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
    HTTP_417_EXPECTATION_FAILED,
    HTTP_418_IM_A_TEAPOT,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_423_LOCKED,
    HTTP_424_FAILED_DEPENDENCY,
    HTTP_426_UPGRADE_REQUIRED,
    HTTP_428_PRECONDITION_REQUIRED,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE,
    HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_501_NOT_IMPLEMENTED,
    HTTP_502_BAD_GATEWAY,
    HTTP_503_SERVICE_UNAVAILABLE,
    HTTP_504_GATEWAY_TIMEOUT,
    HTTP_505_HTTP_VERSION_NOT_SUPPORTED,
    HTTP_507_INSUFFICIENT_STORAGE,
    HTTP_508_LOOP_DETECTED,
    HTTP_510_NOT_EXTENDED,
    HTTP_511_NETWORK_AUTHENTICATION_REQUIRED,
)

def get_status_message(status_code: int) -> str:
    """상태 코드에 따른 적절한 메시지 반환"""
    return {
        HTTP_100_CONTINUE: "계속 진행하세요.",
        HTTP_101_SWITCHING_PROTOCOLS: "프로토콜을 전환합니다.",
        HTTP_102_PROCESSING: "처리 중입니다.",
        HTTP_200_OK: "요청이 성공했습니다.",
        HTTP_201_CREATED: "리소스가 생성되었습니다.",
        HTTP_202_ACCEPTED: "요청이 수락되었습니다.",
        HTTP_203_NON_AUTHORITATIVE_INFORMATION: "권위 없는 정보입니다.",
        HTTP_204_NO_CONTENT: "반환된 값이 없습니다.",
        HTTP_205_RESET_CONTENT: "콘텐츠를 초기화하세요.",
        HTTP_206_PARTIAL_CONTENT: "부분 콘텐츠입니다.",
        HTTP_207_MULTI_STATUS: "다중 상태입니다.",
        HTTP_208_ALREADY_REPORTED: "이미 보고되었습니다.",
        HTTP_226_IM_USED: "이미 사용 중입니다.",
        HTTP_300_MULTIPLE_CHOICES: "다중 선택 사항입니다.",
        HTTP_301_MOVED_PERMANENTLY: "영구적으로 이동되었습니다.",
        HTTP_302_FOUND: "임시로 이동되었습니다.",
        HTTP_303_SEE_OTHER: "다른 것을 참조하세요.",
        HTTP_304_NOT_MODIFIED: "수정되지 않았습니다.",
        HTTP_305_USE_PROXY: "프록시를 사용하세요.",
        HTTP_307_TEMPORARY_REDIRECT: "임시 리디렉션입니다.",
        HTTP_308_PERMANENT_REDIRECT: "영구 리디렉션입니다.",
        HTTP_400_BAD_REQUEST: "잘못된 요청입니다.",
        HTTP_401_UNAUTHORIZED: "인증이 필요합니다.",
        HTTP_402_PAYMENT_REQUIRED: "결제가 필요합니다.",
        HTTP_403_FORBIDDEN: "권한이 없습니다.",
        HTTP_404_NOT_FOUND: "리소스를 찾을 수 없습니다.",
        HTTP_405_METHOD_NOT_ALLOWED: "허용되지 않는 메서드입니다.",
        HTTP_406_NOT_ACCEPTABLE: "허용되지 않는 요청입니다.",
        HTTP_407_PROXY_AUTHENTICATION_REQUIRED: "프록시 인증이 필요합니다.",
        HTTP_408_REQUEST_TIMEOUT: "요청 시간이 초과되었습니다.",
        HTTP_409_CONFLICT: "충돌이 발생했습니다.",
        HTTP_410_GONE: "리소스가 삭제되었습니다.",
        HTTP_411_LENGTH_REQUIRED: "길이 정보가 필요합니다.",
        HTTP_412_PRECONDITION_FAILED: "사전 조건에 실패했습니다.",
        HTTP_413_REQUEST_ENTITY_TOO_LARGE: "요청 엔터티가 너무 큽니다.",
        HTTP_414_REQUEST_URI_TOO_LONG: "요청 URI가 너무 깁니다.",
        HTTP_415_UNSUPPORTED_MEDIA_TYPE: "지원되지 않는 미디어 타입입니다.",
        HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE: "요청 범위를 만족시킬 수 없습니다.",
        HTTP_417_EXPECTATION_FAILED: "기대에 부응하지 못했습니다.",
        HTTP_418_IM_A_TEAPOT: "저는 찻주전자입니다.",
        HTTP_422_UNPROCESSABLE_ENTITY: "입력값 검증에 실패했습니다.",
        HTTP_423_LOCKED: "잠겨 있습니다.",
        HTTP_424_FAILED_DEPENDENCY: "의존성 실패가 발생했습니다.",
        HTTP_426_UPGRADE_REQUIRED: "업그레이드가 필요합니다.",
        HTTP_428_PRECONDITION_REQUIRED: "사전 조건이 필요합니다.",
        HTTP_429_TOO_MANY_REQUESTS: "요청이 너무 많습니다.",
        HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE: "요청 헤더 필드가 너무 큽니다.",
        HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS: "법적 이유로 사용할 수 없습니다.",
        HTTP_500_INTERNAL_SERVER_ERROR: "서버 내부 오류가 발생했습니다.",
        HTTP_501_NOT_IMPLEMENTED: "구현되지 않았습니다.",
        HTTP_502_BAD_GATEWAY: "잘못된 게이트웨이입니다.",
        HTTP_503_SERVICE_UNAVAILABLE: "서비스를 사용할 수 없습니다.",
        HTTP_504_GATEWAY_TIMEOUT: "게이트웨이 타임아웃이 발생했습니다.",
        HTTP_505_HTTP_VERSION_NOT_SUPPORTED: "지원되지 않는 HTTP 버전입니다.",
        HTTP_507_INSUFFICIENT_STORAGE: "저장 공간이 부족합니다.",
        HTTP_508_LOOP_DETECTED: "루프가 감지되었습니다.",
        HTTP_510_NOT_EXTENDED: "확장되지 않았습니다.",
        HTTP_511_NETWORK_AUTHENTICATION_REQUIRED: "네트워크 인증이 필요합니다.",
    }.get(status_code, "요청을 처리할 수 없습니다.")

def get_error_code(status_code: int) -> str:
    """상태 코드에 따른 에러 코드 반환"""
    return {
        HTTP_100_CONTINUE: "CONTINUE",
        HTTP_101_SWITCHING_PROTOCOLS: "SWITCHING_PROTOCOLS",
        HTTP_102_PROCESSING: "PROCESSING",
        HTTP_200_OK: "OK",
        HTTP_201_CREATED: "CREATED",
        HTTP_202_ACCEPTED: "ACCEPTED",
        HTTP_203_NON_AUTHORITATIVE_INFORMATION: "NON_AUTHORITATIVE_INFORMATION",
        HTTP_204_NO_CONTENT: "NO_CONTENT",
        HTTP_205_RESET_CONTENT: "RESET_CONTENT",
        HTTP_206_PARTIAL_CONTENT: "PARTIAL_CONTENT",
        HTTP_207_MULTI_STATUS: "MULTI_STATUS",
        HTTP_208_ALREADY_REPORTED: "ALREADY_REPORTED",
        HTTP_226_IM_USED: "IM_USED",
        HTTP_300_MULTIPLE_CHOICES: "MULTIPLE_CHOICES",
        HTTP_301_MOVED_PERMANENTLY: "MOVED_PERMANENTLY",
        HTTP_302_FOUND: "FOUND",
        HTTP_303_SEE_OTHER: "SEE_OTHER",
        HTTP_304_NOT_MODIFIED: "NOT_MODIFIED",
        HTTP_305_USE_PROXY: "USE_PROXY",
        HTTP_307_TEMPORARY_REDIRECT: "TEMPORARY_REDIRECT",
        HTTP_308_PERMANENT_REDIRECT: "PERMANENT_REDIRECT",
        HTTP_400_BAD_REQUEST: "BAD_REQUEST",
        HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
        HTTP_402_PAYMENT_REQUIRED: "PAYMENT_REQUIRED",
        HTTP_403_FORBIDDEN: "FORBIDDEN",
        HTTP_404_NOT_FOUND: "NOT_FOUND",
        HTTP_405_METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
        HTTP_406_NOT_ACCEPTABLE: "NOT_ACCEPTABLE",
        HTTP_407_PROXY_AUTHENTICATION_REQUIRED: "PROXY_AUTHENTICATION_REQUIRED",
        HTTP_408_REQUEST_TIMEOUT: "REQUEST_TIMEOUT",
        HTTP_409_CONFLICT: "CONFLICT",
        HTTP_410_GONE: "GONE",
        HTTP_411_LENGTH_REQUIRED: "LENGTH_REQUIRED",
        HTTP_412_PRECONDITION_FAILED: "PRECONDITION_FAILED",
        HTTP_413_REQUEST_ENTITY_TOO_LARGE: "REQUEST_ENTITY_TOO_LARGE",
        HTTP_414_REQUEST_URI_TOO_LONG: "REQUEST_URI_TOO_LONG",
        HTTP_415_UNSUPPORTED_MEDIA_TYPE: "UNSUPPORTED_MEDIA_TYPE",
        HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE: "REQUESTED_RANGE_NOT_SATISFIABLE",
        HTTP_417_EXPECTATION_FAILED: "EXPECTATION_FAILED",
        HTTP_418_IM_A_TEAPOT: "IM_A_TEAPOT",
        HTTP_422_UNPROCESSABLE_ENTITY: "UNPROCESSABLE_ENTITY",
        HTTP_423_LOCKED: "LOCKED",
        HTTP_424_FAILED_DEPENDENCY: "FAILED_DEPENDENCY",
        HTTP_426_UPGRADE_REQUIRED: "UPGRADE_REQUIRED",
        HTTP_428_PRECONDITION_REQUIRED: "PRECONDITION_REQUIRED",
        HTTP_429_TOO_MANY_REQUESTS: "TOO_MANY_REQUESTS",
        HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE: "REQUEST_HEADER_FIELDS_TOO_LARGE",
        HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS: "UNAVAILABLE_FOR_LEGAL_REASONS",
        HTTP_500_INTERNAL_SERVER_ERROR: "INTERNAL_SERVER_ERROR",
        HTTP_501_NOT_IMPLEMENTED: "NOT_IMPLEMENTED",
        HTTP_502_BAD_GATEWAY: "BAD_GATEWAY",
        HTTP_503_SERVICE_UNAVAILABLE: "SERVICE_UNAVAILABLE",
        HTTP_504_GATEWAY_TIMEOUT: "GATEWAY_TIMEOUT",
        HTTP_505_HTTP_VERSION_NOT_SUPPORTED: "HTTP_VERSION_NOT_SUPPORTED",
        HTTP_507_INSUFFICIENT_STORAGE: "INSUFFICIENT_STORAGE",
        HTTP_508_LOOP_DETECTED: "LOOP_DETECTED",
        HTTP_510_NOT_EXTENDED: "NOT_EXTENDED",
        HTTP_511_NETWORK_AUTHENTICATION_REQUIRED: "NETWORK_AUTHENTICATION_REQUIRED",
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

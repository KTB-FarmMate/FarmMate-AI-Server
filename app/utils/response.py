# app/utils/response.py

from typing import Any, Optional
from fastapi.responses import JSONResponse


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

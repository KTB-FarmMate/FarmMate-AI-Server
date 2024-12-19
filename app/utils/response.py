from pydantic import BaseModel, Field
from typing import Optional, Generic, TypeVar
from fastapi.responses import JSONResponse

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """에러 상세 정보 모델"""
    code: str
    message: str
    details: Optional[str] = None


class ApiResponse(BaseModel, Generic[T]):
    """표준 응답 모델"""
    message: str
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None
    status_code: int = 200  # 내부적으로만 사용

    class Config:
        exclude_none = True  # None 값을 제외하는 설정

    def to_response(self):
        """JSON 응답으로 변환 (status_code는 응답 본문에 포함되지 않음)"""
        # 응답 내용에서 status_code를 제외
        content = self.model_dump(exclude={"status_code"}, exclude_none=True)
        return JSONResponse(
            content=content,
            status_code=self.status_code  # 상태 코드를 HTTP 응답에만 설정
        )

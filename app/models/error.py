# app/models/error.py

from pydantic import BaseModel
from typing import Optional


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

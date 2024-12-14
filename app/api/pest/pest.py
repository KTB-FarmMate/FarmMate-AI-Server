# 타입과 유틸리티 관련 모듈
from typing import List, Any, Optional, Generic, TypeVar
import re
import time
import json
import logging
from enum import Enum
from datetime import datetime

# HTTP 및 API 관련 모듈
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator, ValidationError
from starlette.responses import JSONResponse
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_408_REQUEST_TIMEOUT, HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_404_NOT_FOUND,
)

# 프로젝트 내 모듈
from app.core.config import settings
from app.utils.response import ApiResponse, ErrorDetail

from bs4 import BeautifulSoup

T = TypeVar('T')

router = APIRouter()


class PestResponse(BaseModel):
    """
    특정 작물에 대한 병해충 예보, 주의보, 경보 리스트 클래스
    """
    forecasts: List[str] = Field([], description="병해충 예보 리스트")
    advisories: List[str] = Field([], description="병해충 주의보 리스트")
    warnings: List[str] = Field([], description="병해충 경보 리스트")


@router.get(
    "",
    summary="작물별 병해충 목록",
    response_model=ApiResponse[PestResponse],
    tags=["병해충 관련"],
    responses={
        200: {
            "description": "성공적인 응답.",
            "content": {
                "application/json": {
                    "example": {
                        "message": "채팅방이 성공적으로 생성되었습니다.",
                        "data": {
                            "forecasts": ["무름병", "탄저병"],  # 예보
                            "advisories": ["갈색날개매미충", "복숭아순나방"],  # 주의보
                            "warnings ": ["탄저병"]  # 경보
                        }
                    }
                }
            }
        }
    }
)
async def get_pests(cropName: str) -> ApiResponse:
    """작물이름을 기준으로 병해충 목록을 제공 합니다."""

    def filter_pests(crop_name: str, pest_list):
        result = []
        for li in pest_list:
            text = li.text
            match = re.search(r"\([^-]+-([^)]+)\)", text)
            if match:
                crop = match.group(1)
                if crop == crop_name:
                    result.append(re.sub(r"\(.*?\)", "", text).strip())
                    print(result)
        return result

    pest_list_url = r"https://ncpms.rda.go.kr/npms/NewIndcUserListR.np"

    res = requests.get(pest_list_url)

    html = res.text

    soup = BeautifulSoup(html, "html.parser")
    latest = soup.select_one(".tabelRound tbody tr td:nth-child(2) a")

    latest_number = latest.get_attribute_list("onclick")[0].split("'")[1]
    # latest_number = 229
    pest_detail_url = rf"https://ncpms.rda.go.kr/npms/NewIndcUserR.np?indcMon=&indcSeq={latest_number}"

    res = requests.get(pest_detail_url)

    html = res.text

    soup = BeautifulSoup(html, "html.parser")

    forecast_selector = ".forecast li"
    watch_selector = ".watch li"
    warning_selector = ".warning li"

    forecast_list = soup.select(forecast_selector)

    watch_list = soup.select(watch_selector)

    warning_list = soup.select(warning_selector)

    # cropName = "오이"

    print("예보 개수 : ", len(forecast_list))
    result_forecast = filter_pests(cropName, forecast_list)
    print(f"{cropName} 병해충 예보 : {len(result_forecast)}")

    print("주의보 개수 : ", len(watch_list))
    result_watch = filter_pests(cropName, watch_list)
    print(f"{cropName} 병해충 주의보 : {len(result_watch)}")

    print("경보 개수 : ", len(warning_list))
    result_warning = filter_pests(cropName, warning_list)

    print(f"{cropName} 병해충 경보: {len(result_warning)}")
    return ApiResponse(
        message="병해충 정보가 성공적으로 조회되었습니다.",
        data={
            "forecasts": result_forecast,  # 예보
            "advisories": result_watch,  # 주의보
            "warnings": result_warning  # 경보
        }).to_response()


if __name__ == "__main__":
    pass

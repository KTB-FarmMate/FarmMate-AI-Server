import sys
import os
import pytest
import asyncio
from httpx import AsyncClient
from unittest.mock import Mock
from fastapi import status
from openai import base_url

# 프로젝트의 루트 디렉토리를 모듈 검색 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # FastAPI 앱이 정의된 모듈을 임포트합니다.

pytestmark = pytest.mark.asyncio

# 날씨 호출 관련 테스트

# 1. 정상 날씨 호출 테스트
@pytest.mark.asyncio
async def test_get_weather_success():
    """
    정상 요청으로 정상 반환
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get("/weather?address=경기 성남시 분당구 대왕판교로 660 유스페이스1 A동 405호")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["x"] and data["y"]

# 2. 비정상 주소 입력
@pytest.mark.asyncio
async def test_get_weather_success():
    """
    비정상 요청(존재하지 않는 주소)시 테스트
    """
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.get("/weather?address=UNKNOWN_ADDRESS")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data['detail'] == "주소가 올바르지 않음"
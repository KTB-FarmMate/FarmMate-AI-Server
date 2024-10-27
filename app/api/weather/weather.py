import os
import math
import requests
import json
from datetime import datetime
from typing import List, Any, Optional, Generic, TypeVar
from starlette.status import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from app.core.config import settings
from starlette.responses import JSONResponse
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field, field_validator, ValidationError
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR, HTTP_408_REQUEST_TIMEOUT
)


def create_response(*,
                    status_code: int,
                    message: str,
                    data: Any = None,
                    error: dict[str, str] = None) -> JSONResponse:
    """통합 응답 생성 함수
    - status_code로 성공/실패 판단 (2xx는 성공, 4xx/5xx는 실패)
    """
    return JSONResponse(status_code=status_code, content=
    {
        "message": message,
        "data": data,
        "error": error}
                        )


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


router = APIRouter()


class LamcParameter:
    def __init__(self):
        self.Re = 6371.00877  # 지도 반경 (km)
        self.grid = 5.0  # 격자 간격 (km)
        self.slat1 = 30.0  # 표준 위도 1
        self.slat2 = 60.0  # 표준 위도 2
        self.olon = 126.0  # 기준점 경도
        self.olat = 38.0  # 기준점 위도
        self.xo = 210 / self.grid  # 기준점 X 좌표
        self.yo = 675 / self.grid  # 기준점 Y 좌표
        self.first = 0


def lamcproj(lon, lat, code, map_param):
    PI = math.asin(1.0) * 2.0
    DEGRAD = PI / 180.0
    RADDEG = 180.0 / PI

    re = map_param.Re / map_param.grid
    slat1 = map_param.slat1 * DEGRAD
    slat2 = map_param.slat2 * DEGRAD
    olon = map_param.olon * DEGRAD
    olat = map_param.olat * DEGRAD

    sn = math.tan(PI * 0.25 + slat2 * 0.5) / math.tan(PI * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(PI * 0.25 + slat1 * 0.5)
    sf = (sf ** sn) * math.cos(slat1) / sn
    ro = math.tan(PI * 0.25 + olat * 0.5)
    ro = re * sf / (ro ** sn)
    map_param.first = 1

    if code == 0:  # 위도, 경도 -> X, Y 변환
        ra = math.tan(PI * 0.25 + lat * DEGRAD * 0.5)
        ra = re * sf / (ra ** sn)
        theta = lon * DEGRAD - olon
        if theta > PI:
            theta -= 2.0 * PI
        if theta < -PI:
            theta += 2.0 * PI
        theta *= sn
        x = ra * math.sin(theta) + map_param.xo
        y = ro - ra * math.cos(theta) + map_param.yo
        return round(x), round(y)
    else:
        # 여기에 코드가 있을 경우 역변환 코드 구현
        return lon, lat


class KakaoLocalService:
    KAKAO_API_URL = "https://dapi.kakao.com/v2/local/search/address.json"

    def __init__(self):
        self.API_KEY = settings.KAKAO_LOCAL_API_KEY

    def convert_address_to_coordinate(self, address):
        def get_weather(lon: float, lat: float):
            url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst'
            param = LamcParameter()
            nx, ny = lamcproj(lon, lat, 0, param)  # 위도, 경도를 격자 좌표로 변환

            today = datetime.now().strftime("%Y%m%d")
            times = int(datetime.now().strftime("%H"))

            for i in range(3):
                try:
                    params = {
                        'serviceKey': settings.WEATHER_API_KEY,
                        'pageNo': '1',
                        'numOfRows': '8',
                        'dataType': 'JSON',
                        'base_date': today,
                        'base_time': f"{(times - i):02d}00",
                        'nx': nx,
                        'ny': ny
                    }
                    response = requests.get(url, params=params)
                    response.raise_for_status()  # HTTP 오류 체크
                    response_data = response.json()  # JSON 파싱
                    if response_data["response"]["header"]["resultCode"] != "00":
                        continue
                    values = {
                        item["category"]: item["obsrValue"]
                        for item in response_data["response"]["body"]["items"]["item"]
                    }
                    return values
                except requests.exceptions.RequestException as e:
                    continue
            return HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR)

        headers = {"Authorization": f"KakaoAK {self.API_KEY}"}
        response = requests.get(self.KAKAO_API_URL, headers=headers, params={"query": address})
        response.raise_for_status()
        data = response.json()
        if data["documents"]:
            document = data["documents"][0]
            return get_weather(float(document['x']), float(document['y']))
        else:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="주소가 올바르지 않음")


kakao_service = KakaoLocalService()


@router.get("")
def get_coordinates(address: str):
    try:
        result = kakao_service.convert_address_to_coordinate(address)
        if result:
            return create_response(
                status_code=HTTP_200_OK,
                message="날씨 정보를 성공적으로 조회했습니다.",
                data=result
            )
        else:
            return create_response(
                status_code=HTTP_404_NOT_FOUND,
                message="주소를 찾을 수 없습니다.",
                error=ErrorDetail(
                    code="NOT_FOUND",
                    message="주소가 올바르지 않음",
                    details="Invalid address"
                ).to_dict()
            )
    except HTTPException as e:
        return create_response(
            status_code=e.status_code,
            message="날씨 정보 조회에 실패했습니다.",
            error=ErrorDetail(
                code="NOT_FOUND",
                message=str(e.detail),
                details="Invalid address"
            ).to_dict()
        )
    except Exception as e:
        return create_response(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            message="날씨 정보 조회 중 오류가 발생했습니다.",
            error=ErrorDetail(
                code="SERVER_ERROR",
                message="서버 내부 오류가 발생했습니다.",
                details=str(e)
            ).to_dict()
        )


if __name__ == '__main__':
    result = kakao_service.convert_address_to_coordinate("두정역동 2길 31")
    print(result)

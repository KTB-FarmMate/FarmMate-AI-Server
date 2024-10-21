import os
import requests

from app.core.config import settings
from fastapi import APIRouter, HTTPException, status, Request, Query, Response

router = APIRouter()


class KakaoLocalService:
    KAKAO_API_URL = "https://dapi.kakao.com/v2/local/search/address.json"

    def __init__(self):
        # 환경 변수 또는 설정 파일에서 API 키를 읽어옵니다.
        self.API_KEY = settings.KAKAO_LOCAL_API_KEY

    def convert_address_to_coordinate(self, address):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"KakaoAK {self.API_KEY}"
        }
        params = {
            "query": address
        }
        response = requests.get(self.KAKAO_API_URL, headers=headers, params=params)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 처리

        data = response.json()
        print(data)
        if data['documents']:
            document = data['documents'][0]
            x = document['x']
            y = document['y']
            # CoordinateVO와 유사한 딕셔너리 형태로 반환
            return {'x': x, 'y': y}
        else:
            return None


kakao_service = KakaoLocalService()


@router.get("")
def get_coordinates(address: str):
    result = kakao_service.convert_address_to_coordinate(address)
    if result:
        return result
    else:
        raise HTTPException(status_code=404, detail="주소를 찾을 수 없음")

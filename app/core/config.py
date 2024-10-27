from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()


class Settings(BaseSettings):
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    ASSISTANT_ID: str = os.getenv("ASSISTANT_ID")
    KAKAO_LOCAL_API_KEY: str = os.getenv("KAKAO_LOCAL_API_KEY")
    WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY")


settings = Settings()

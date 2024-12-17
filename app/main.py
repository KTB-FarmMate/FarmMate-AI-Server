from fastapi import FastAPI
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from app.api.openai.chatbot import router as openai_router
from app.api.health.health import router as health_router
from app.front.front import router as front_router
from app.api.pest.pest import router as pest_router
from app.core.globalException import add_exception_handlers
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

# 메인 앱 생성
app = FastAPI(
    debug=True,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    servers=[
        {"url": "/ai", "description": "AI 관련 API"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 허용할 도메인 (배포 환경)
    allow_credentials=True,                     # 자격 증명 (쿠키 등) 허용
    allow_methods=["*"],                        # 허용할 HTTP 메서드
    allow_headers=["*"],                        # 허용할 HTTP 헤더
)
# Front 앱 생성
front_app = FastAPI(
    debug=True,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    servers=[
        {"url": "/front", "description": "프론트엔드 관련 API"},
    ],
)
front_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 허용할 도메인 (배포 환경)
    allow_credentials=True,                     # 자격 증명 (쿠키 등) 허용
    allow_methods=["*"],                        # 허용할 HTTP 메서드
    allow_headers=["*"],                        # 허용할 HTTP 헤더
)

# 메인 앱 라우터 등록
app.include_router(health_router, prefix="/health")
app.include_router(openai_router, prefix="/members/{memberId}/threads")
app.include_router(pest_router, prefix="/pests")

# # Front 앱 라우터 등록
front_app.include_router(front_router)

# 정적 파일 디렉토리 설정
static_dir = Path(__file__).parent / "front/static"
if not static_dir.exists():
    raise RuntimeError(f"Static directory '{static_dir}'가 존재하지 않습니다.")

# Front 앱에 정적 파일 제공
front_app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Front 앱을 메인 앱에 마운트
app.mount("/front", front_app)

# 글로벌 예외 핸들러 추가
add_exception_handlers(app)

# 앱 실행
if __name__ == "__main__":
    uvicorn.run(app, port=8000)

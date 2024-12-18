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
# FastAPI 앱 생성 (servers 설정 제거)
app = FastAPI(
    debug=True,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://farmmate.net",             # FE 도메인 (서브도메인 없이)
        "https://www.farmmate.net",         # FE 도메인 (www 포함)
        "https://api.farmmate.net",         # BE 서버 도메인
        "https://www.api.farmmate.net"      # BE 서버 서브도메인 포함
    ],
    allow_credentials=True,  # 쿠키, 인증 정보 포함 허용 (필요시)
    allow_methods=["*"],     # 모든 HTTP 메소드 허용 (GET, POST 등)
    allow_headers=["*"],     # 모든 헤더 허용
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
# 메인 앱 라우터 등록
app.include_router(health_router, prefix="/health")
app.include_router(openai_router, prefix="/members/{memberId}/threads")
app.include_router(pest_router, prefix="/ai")

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

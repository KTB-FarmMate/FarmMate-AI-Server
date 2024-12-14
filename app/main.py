from fastapi import FastAPI
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from app.api.openai.chatbot import router as openai_router
from app.api.health.health import router as health_router
from app.front.front import router as front_router
from app.api.pest.pest import router as pest_router
from app.core.globalException import add_exception_handlers
import uvicorn

# 메인 앱 생성
app = FastAPI(
    debug=True,
    openapi_url="/openapi.json",  # OpenAPI 스펙 경로
    docs_url="/docs",  # Swagger UI 경로
    redoc_url="/redoc",  # ReDoc 문서 경로
    root_path="/ai",  # 메인 API의 기본 root_path
    servers=[  # Swagger UI에 표시할 서버를 명시적으로 설정
        {"url": "/ai", "description": "AI 관련 API"},
    ],
)

# Front 앱 생성
# front_app = FastAPI(
#     debug=True,
#     openapi_url="/openapi.json",  # Front 앱 OpenAPI 경로
#     docs_url="/docs",  # Front 앱 Swagger 경로
#     redoc_url="/redoc",  # Front 앱 ReDoc 경로
#     root_path="/front",  # Front API의 기본 root_path
#     servers=[  # Swagger UI에 표시할 서버를 명시적으로 설정
#         {"url": "/front", "description": "프론트엔드 관련 API"},
#     ],
# )

# 메인 앱 라우터 등록
app.include_router(health_router, prefix="/health")
app.include_router(openai_router, prefix="/members/{memberId}/threads")
app.include_router(pest_router, prefix="/pests")
#
# # Front 앱 라우터 등록
# front_app.include_router(front_router, prefix="/front")  # Front 앱 내 기본 경로
#
# # Front 앱에 정적 파일 제공
# static_dir = Path(__file__).parent / "front/static"
# if not static_dir.exists():
#     raise RuntimeError(f"Static directory '{static_dir}'가 존재하지 않습니다.")
#
# front_app.mount("/static", StaticFiles(directory=static_dir), name="static")
#
# # Front 앱을 메인 앱에 마운트
# app.mount("/front", front_app)

# 글로벌 예외 핸들러 추가
add_exception_handlers(app)

# 앱 실행
if __name__ == "__main__":
    uvicorn.run(app, port=8000)

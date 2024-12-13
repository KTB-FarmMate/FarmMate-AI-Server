from fastapi import FastAPI, Request
from app.api.openai.chatbot import router as openai_router
from app.api.health.health import router as health_router
# from app.front.front import router as front_router
from app.core.globalException import add_exception_handlers
import uvicorn

# from fastapi.responses import HTMLResponse
# from fastapi.staticfiles import StaticFiles
# from fastapi.templating import Jinja2Templates


app = FastAPI(debug=False)
# 정적 파일 제공
app.include_router(openai_router, prefix="/members/{memberId}/threads")
app.include_router(health_router, prefix="/health")

# react native 에서, 사용자가 해당 webview에서 다른 url로 접근하지 못하도록, 화이트 리스트를 사용하거나 할 것.
# app.include_router(front_router, prefix="/front")

# 정적 파일 제공
# app.mount("/static", StaticFiles(directory="app/front/static"), name="static")


add_exception_handlers(app)


# 실행
if __name__ == "__main__":
    uvicorn.run(app, port=8000)
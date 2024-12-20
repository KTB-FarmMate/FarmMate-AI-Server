from fastapi import FastAPI
from app.api.openai.chatbot import router as openai_router
from app.api.weather.weather import router as weather_router
from app.api.health.health import router as health_router
from app.core.globalException import add_exception_handlers
import uvicorn


app = FastAPI()

app.include_router(openai_router, prefix="/members/{memberId}/threads")
app.include_router(weather_router, prefix="/weather")
app.include_router(health_router, prefix="/health")

add_exception_handlers(app)


# 실행
if __name__ == "__main__":
    uvicorn.run(app, port=8000)
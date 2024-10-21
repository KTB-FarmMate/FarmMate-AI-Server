from fastapi import FastAPI
from app.api.openai import router as openai_router
from app.api.weather import router as weather_router
from app.core.config import Settings
import uvicorn


app = FastAPI()

app.include_router(openai_router, prefix="/threads")
app.include_router(weather_router, prefix="/weather")


# 실행
if __name__ == "__main__":
    uvicorn.run(app, port=8000)
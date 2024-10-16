from fastapi import FastAPI
from app.api.openai import router as openai_router
from app.core.config import Settings
import uvicorn


app = FastAPI()

app.include_router(openai_router, prefix="chat")


# 실행
if __name__ == "__main__":
    uvicorn.run(app, port=8000)
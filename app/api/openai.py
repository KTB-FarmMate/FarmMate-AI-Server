from fastapi import APIRouter, HTTPException
from app.core.config import settings
import openai

client = openai.Client(api_key=settings.OPENAI_API_KEY)
router = APIRouter()


@router.post("/chat")
async def chat():
    try:
        return {"response": client.api_key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

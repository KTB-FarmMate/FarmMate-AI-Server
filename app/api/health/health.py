from fastapi import APIRouter, status
from starlette.responses import JSONResponse

router = APIRouter()


@router.get(
    "",
    summary="헬스체크",
    tags=["헬스체크"],
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": {"status": "200"}
                }
            }
        }
    }
)
async def check_health():
    """
    서버의 상태를 확인하는 엔드포인트입니다.
    """
    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "200"})

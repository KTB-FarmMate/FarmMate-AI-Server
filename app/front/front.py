# app/api/openai/chatbot.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates  # main.py에서 설정한 templates를 임포트

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def splash(request: Request):
    return templates.TemplateResponse(
        "splash.html", {"request": request}
    )


@router.get("/members/{memberId}", response_class=HTMLResponse)
async def index_template(request: Request, memberId: str):
    return templates.TemplateResponse(
        "crop_list/index.html", {"request": request, "memberId": memberId}
    )


@router.get("/members/{memberId}/crop/{cropName}", response_class=HTMLResponse)
async def crop(request: Request, memberId: str, cropName: str):
    return templates.TemplateResponse(
        "crop_dashboard/dashboard.html", {"request": request, "memberId": memberId, "cropName": cropName}
    )


@router.get("/members/{memberId}/recommend", response_class=HTMLResponse)
async def recommend(request: Request, memberId: str):
    return (templates.TemplateResponse(
        "crop_recommend/recommend_page.html", {"request": request, "memberId": memberId}
    ))


@router.get("/members/{memberId}/recommend/{quiz_num}", response_class=HTMLResponse)
async def recommend(request: Request, memberId: str, quiz_num: str):
    if quiz_num == "result":
        return templates.TemplateResponse(
            f"crop_recommend/recommend_result_page.html", {"request": request, "memberId": memberId}
        )
    return templates.TemplateResponse(
        f"crop_recommend/recommend_{quiz_num}_page.html", {"request": request, "memberId": memberId}
    )


@router.get("/members/{memberId}/crop_create/{cropName}", response_class=HTMLResponse)
async def crop_create(request: Request, memberId: str, cropName: str):
    return templates.TemplateResponse(
        "create_crop/crop_create.html", {"request": request, "memberId": memberId, "cropName": cropName}
    )


@router.get("/members/{memberId}/crop_modify/{cropName}", response_class=HTMLResponse)
async def crop_modify(request: Request, memberId: str, cropName: str):
    return templates.TemplateResponse(
        "modify_crop/crop_modify.html", {"request": request, "memberId": memberId, "cropName": cropName}
    )


@router.get("/members/{memberId}/crop/{cropName}/chatbot", response_class=HTMLResponse)
async def chatbot(request: Request, memberId: str, cropName: str):
    return templates.TemplateResponse(
        "chat/chat.html", {"request": request, "memberId": memberId, "cropName": cropName}
    )


@router.get("/members/{memberId}/crop/{cropName}/curriculum", response_class=HTMLResponse)
async def curriculum(request: Request, memberId: str, cropName: str):
    return templates.TemplateResponse(
        "curriculum/curriculum.html", {"request": request, "memberId": memberId, "cropName": cropName}
    )


@router.get("/members/{memberId}/crop/{cropName}/curriculum/detail", response_class=HTMLResponse)
async def curriculum_detail(request: Request, memberId: str, cropName: str):
    return templates.TemplateResponse(
        "curriculum/curriculum_detail.html", {"request": request, "memberId": memberId, "cropName": cropName}
    )


@router.get("/members/{memberId}/crop/{cropName}/alarm", response_class=HTMLResponse)
async def alarm(request: Request, memberId: str, cropName: str):
    return templates.TemplateResponse(
        "alarm/alarm.html", {"request": request, "memberId": memberId, "cropName": cropName}
    )


@router.get("/members/{memberId}/crop/{cropName}/chatbot/bookmark", response_class=HTMLResponse)
async def bookmark(request: Request, memberId: str, cropName: str):
    return templates.TemplateResponse(
        "bookmark/bookmark.html", {"request": request, "memberId": memberId, "cropName": cropName}
    )


@router.get("/members/{memberId}/setting", response_class=HTMLResponse)
async def setting(request: Request, memberId: str):
    return templates.TemplateResponse(
        "setting/setting.html", {"request": request, "memberId": memberId}
    )


@router.get("/members/{memberId}/crop/{cropName}/guidance", response_class=HTMLResponse)
async def guidance(request: Request, memberId: str, cropName: str):
    return templates.TemplateResponse(
        "guidance/guidance.html", {"request": request, "memberId": memberId, "cropName": cropName}
    )


@router.get("/members/{memberId}/crop/{cropName}/pests", response_class=HTMLResponse)
async def pests(request: Request, memberId: str, cropName: str):
    return templates.TemplateResponse(
        "pests/pests.html", {"request": request, "memberId": memberId, "cropName": cropName}
    )


@router.get("/members/{memberId}/crop/{cropName}/pests/{pestName}", response_class=HTMLResponse)
async def pests(request: Request, memberId: str, cropName: str, pestName: str):
    return templates.TemplateResponse(
        "pests/pests_detail.html",
        {"request": request, "memberId": memberId, "cropName": cropName, "pestName": pestName}
    )


@router.get("/members/{memberId}/crop/{cropName}/weather/detail", response_class=HTMLResponse)
async def weather(request: Request, memberId: str, cropName: str):
    return templates.TemplateResponse(
        "weather/weather.html", {"request": request, "memberId": memberId, "cropName": cropName}
    )


@router.get("/test", response_class=HTMLResponse)
async def test(request: Request):
    return templates.TemplateResponse(
        "test.html", {"request": request}
    )

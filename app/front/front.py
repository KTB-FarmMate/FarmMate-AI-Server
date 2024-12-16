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


@router.get("/index", response_class=HTMLResponse)
async def index_template(request: Request):
    return templates.TemplateResponse(
        "crop_list/index.html", {"request": request, "data": "Hello, FastAPI!"}
    )


@router.get("/crop/{cropName}", response_class=HTMLResponse)
async def crop(request: Request, cropName: str):
    return templates.TemplateResponse(
        "crop_dashboard/dashboard.html", {"request": request, "crop_name": cropName}
    )


@router.get("/recommend", response_class=HTMLResponse)
async def recommend(request: Request):
    return (templates.TemplateResponse(
        "crop_recommend/recommend_page.html", {"request": request}
    ))


@router.get("/recommend/{quiz_num}", response_class=HTMLResponse)
async def recommend(request: Request, quiz_num: str):
    if quiz_num == "result":
        return templates.TemplateResponse(
            f"crop_recommend/recommend_result_page.html", {"request": request}
        )
    return templates.TemplateResponse(
        f"crop_recommend/recommend_{quiz_num}_page.html", {"request": request}
    )


@router.get("/crop_create/{crop_name}", response_class=HTMLResponse)
async def crop_create(request: Request, crop_name: str):
    return templates.TemplateResponse(
        "create_crop/crop_create.html", {"request": request, "crop_name": crop_name}
    )


@router.get("/crop_modify/{crop_name}", response_class=HTMLResponse)
async def crop_modify(request: Request, crop_name: str):
    return templates.TemplateResponse(
        "modify_crop/crop_modify.html", {"request": request, "crop_name": crop_name}
    )


@router.get("/chatbot/{crop_name}", response_class=HTMLResponse)
async def chatbot(request: Request, crop_name: str):
    return templates.TemplateResponse(
        "chat/chat.html", {"request": request, "crop_name": crop_name}
    )


@router.get("/curriculum/{crop_name}", response_class=HTMLResponse)
async def curriculum(request: Request, crop_name: str):
    return templates.TemplateResponse(
        "curriculum/curriculum.html", {"request": request, "crop_name": crop_name}
    )


@router.get("/curriculum/{crop_name}/detail", response_class=HTMLResponse)
async def curriculum_detail(request: Request, crop_name: str):
    return templates.TemplateResponse(
        "curriculum/curriculum_detail.html", {"request": request, "crop_name": crop_name}
    )


@router.get("/alarm/{crop_name}", response_class=HTMLResponse)
async def alarm(request: Request, crop_name: str):
    return templates.TemplateResponse(
        "alarm/alarm.html", {"request": request, "crop_name": crop_name}
    )


@router.get("/bookmark/{crop_name}", response_class=HTMLResponse)
async def bookmark(request: Request, crop_name: str):
    return templates.TemplateResponse(
        "bookmark/bookmark.html", {"request": request, "crop_name": crop_name}
    )


@router.get("/setting", response_class=HTMLResponse)
async def setting(request: Request):
    return templates.TemplateResponse(
        "setting/setting.html", {"request": request}
    )

@router.get("/crop/{crop_name}/guidance", response_class=HTMLResponse)
async def guidance(request: Request, crop_name: str):
    return templates.TemplateResponse(
        "guidance/guidance.html", {"request": request, "crop_name": crop_name}
    )

@router.get("/crop/{crop_name}/pests", response_class=HTMLResponse)
async def pests(request: Request, crop_name: str):
    return templates.TemplateResponse(
        "pests/pests.html", {"request": request, "crop_name": crop_name}
    )
@router.get("/crop/{crop_name}/pests/{pest_name}", response_class=HTMLResponse)
async def pests(request: Request, crop_name: str, pest_name:str):
    return templates.TemplateResponse(
        "pests/pests_detail.html", {"request": request, "crop_name": crop_name, "pest_name": pest_name}
    )


@router.get("/crop/{crop_name}/weather/detail", response_class=HTMLResponse)
async def pests(request: Request, crop_name: str):
    return templates.TemplateResponse(
        "weather/weather.html", {"request": request, "crop_name": crop_name}
    )

@router.get("/test", response_class=HTMLResponse)
async def test(request: Request):
    return templates.TemplateResponse(
        "test.html", {"request": request}
    )

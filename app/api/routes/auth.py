from fastapi import APIRouter, Form

from app.core.responses import success_response
from app.schemas.auth import LoginResponse
from app.services.auth import authenticate_demo_user


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
) -> dict:
    token = authenticate_demo_user(username=username, password=password)
    data = LoginResponse(access_token=token, token_type="bearer").model_dump()
    return success_response(data=data, message="login success")

from fastapi import APIRouter, Form, Depends, Request
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.db import get_db
from app.models import User
from app.schemas.user import UserCreate
from app.auth.utils import hash_password

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.post("/register")
async def register_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    hashed_pw = hash_password(password)

    new_user = User(
        username=username,
        email=email,
        password_hash=hashed_pw,
    )

    db.add(new_user)
    db.commit()

    return templates.TemplateResponse(
        "login.html", {"request": request, "msg": "Registration successful"}
    )


@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

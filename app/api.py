import os
from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from pydantic import EmailStr

from app.db import get_db
from app.models import User, WatchlistItem
from app.auth import hash_password, verify_password, get_current_user

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
router = APIRouter()


@router.get("/register", response_class=HTMLResponse)
async def show_register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", response_class=HTMLResponse)
async def register_user(
    request: Request,
    username: str = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "msg": "Email already registered"},
            status_code=400,
        )
    hashed_pw = hash_password(password)
    new_user = User(username=username, email=email, password_hash=hashed_pw)
    db.add(new_user)
    db.commit()
    # After successful registration, show login form with a success message
    return templates.TemplateResponse(
        "login.html", {"request": request, "msg": "Registration successful"}
    )


@router.get("/login", response_class=HTMLResponse)
async def display_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def handle_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "msg": "Invalid username or password"},
            status_code=400,
        )
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="user_id", value=str(user.id), httponly=True)
    return response


@router.get("/watchlist", response_class=HTMLResponse)
async def display_watchlist(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    watchlist_items = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == user.id
    ).all()
    return templates.TemplateResponse(
        "display_watchlist.html",
        {"request": request, "user": user, "watchlist_items": watchlist_items},
    )


@router.post("/add_to_watchlist", response_class=HTMLResponse)
async def add_to_watchlist(
    request: Request,
    user_id: int = Form(...),
    company_name: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "msg": "User not found"},
            status_code=400,
        )

    existing_item = (
        db.query(WatchlistItem)
        .filter(
            WatchlistItem.user_id == user_id,
            WatchlistItem.company_name.ilike(company_name.strip()),
        )
        .first()
    )
    if existing_item:
        items = db.query(WatchlistItem).filter(WatchlistItem.user_id == user.id).all()
        return templates.TemplateResponse(
            "display_watchlist.html",
            {
                "request": request,
                "user": user,
                "watchlist_items": items,
                "msg": f"{company_name} is already in your watchlist",
            },
        )

    new_item = WatchlistItem(user_id=user_id, company_name=company_name.strip())
    db.add(new_item)
    db.commit()
    items = db.query(WatchlistItem).filter(WatchlistItem.user_id == user.id).all()
    return templates.TemplateResponse(
        "display_watchlist.html",
        {
            "request": request,
            "user": user,
            "watchlist_items": items,
            "msg": f"Successfully added {company_name} to your watchlist!",
        },
    )


@router.post("/remove_from_watchlist", response_class=HTMLResponse)
async def remove_from_watchlist(
    request: Request,
    user_id: int = Form(...),
    item_id: int = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "msg": "User not found"},
            status_code=400,
        )
    db.query(WatchlistItem).filter(WatchlistItem.id == item_id).delete()
    db.commit()
    items = db.query(WatchlistItem).filter(WatchlistItem.user_id == user.id).all()
    return templates.TemplateResponse(
        "display_watchlist.html",
        {
            "request": request,
            "user": user,
            "watchlist_items": items,
            "msg": "Successfully removed item",
        },
    )

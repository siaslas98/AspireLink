import os
from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User, WatchlistItem  # Added WatchlistItem import
from app.auth import hash_password, verify_password
from pydantic import BaseModel, EmailStr

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
router = APIRouter()

# User registration page
@router.get("/register", response_class=HTMLResponse)
async def show_register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# User registration posting
@router.post("/register")
async def register_user(
    request: Request,
    username: str = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        # Create a already_registered.html to return for existing
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "msg": "Email already registered"},
            status_code=400,
        )
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

# User login
@router.get("/login", response_class=HTMLResponse)
async def display_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# User's see the watchlist page after logging in
@router.post("/login", response_class=HTMLResponse)
async def handle_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    # display the user's watchlist page
    # allow users to add company names to watchlist
    user = db.query(User).filter(User.username == username).first()
    # Invalid login
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "msg": "Invalid username or password"},
            status_code=400,
        )
    # Valid login - now get user's watchlist items
    watchlist_items = db.query(WatchlistItem).filter(WatchlistItem.user_id == user.id).all()
    
    return templates.TemplateResponse(
        "display_watchlist.html", 
        {
            "request": request, 
            "user": user,
            "watchlist_items": watchlist_items
        }
    )

# Add company to user's watchlist
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

    # Check if company already exists in watchlist
    existing_item = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == user_id,
        WatchlistItem.company_name.ilike(company_name.strip())
    ).first()
    
    if existing_item:
        watchlist_items = db.query(WatchlistItem).filter(WatchlistItem.user_id == user.id).all()
        return templates.TemplateResponse(
            "display_watchlist.html",
            {
                "request": request,
                "user": user,
                "watchlist_items": watchlist_items,
                "msg": f"{company_name} is already in your watchlist"
            }
        )

    # Add new item to watchlist
    new_item = WatchlistItem(
        user_id=user_id,
        company_name=company_name.strip()
    )
    
    db.add(new_item)
    db.commit()
    
    # Get updated watchlist
    watchlist_items = db.query(WatchlistItem).filter(WatchlistItem.user_id == user.id).all()
    
    return templates.TemplateResponse(
        "display_watchlist.html",
        {
            "request": request,
            "user": user,
            "watchlist_items": watchlist_items,
            "msg": f"Successfully added {company_name} to your watchlist!"
        }
    )

# Remove company from watchlist
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

    # Find and remove the item
    item_to_remove = db.query(WatchlistItem).filter(
        WatchlistItem.id == item_id,
        WatchlistItem.user_id == user_id
    ).first()
    
    if item_to_remove:
        company_name = item_to_remove.company_name
        db.delete(item_to_remove)
        db.commit()
        msg = f"Successfully removed {company_name} from your watchlist"
    else:
        msg = "Item not found in your watchlist"
    
    # Get updated watchlist
    watchlist_items = db.query(WatchlistItem).filter(WatchlistItem.user_id == user.id).all()
    
    return templates.TemplateResponse(
        "display_watchlist.html",
        {
            "request": request,
            "user": user,
            "watchlist_items": watchlist_items,
            "msg": msg
        }
    )

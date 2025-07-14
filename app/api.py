import os
from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from datetime import datetime, timedelta

from sqlalchemy import or_
from sqlalchemy.orm import Session
from pydantic import EmailStr

from app.db import get_db
from app.models import (
    User,
    WatchlistItem,
    Internship,
    ApplicationLog,
    CheckIn,
    Reminder,
)

from app.auth import hash_password, verify_password, get_current_user

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "app", "templates"))
router = APIRouter()


# ___ APP Home Page ____________________________________________________________
@router.get("/", response_class=HTMLResponse)
def home(
    request: Request,
):
    return templates.TemplateResponse("index.html", {"request": request})


# ─── DASHBOARD ────────────────────────────────────────────────────────────────
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "user": user}
    )


# ─── NOTIFICATIONS ────────────────────────────────────────────────────────
@router.get("/api/notifications")
async def get_notifications(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    company_names = (
        db.query(WatchlistItem.company_name)
        .filter(WatchlistItem.user_id == user.id)
        .all()
    )
    names = [c[0] for c in company_names]
    
    if not names:
        return {"new_internships": []}
    
    # Check for internships posted in the last 24 hours
    yesterday = datetime.now() - timedelta(days=1)
    conditions = [Internship.company.ilike(name) for name in names]
    
    new_internships = (
        db.query(Internship)
        .filter(or_(*conditions))
        .filter(Internship.active == True)
        .order_by(Internship.date_posted.desc())
        .limit(10)
        .all()
    )
    
    # Format response
    notifications = []
    for internship in new_internships:
        notifications.append({
            "id": internship.id,
            "company": internship.company,
            "role": internship.role,
            "location": internship.location,
            "date_posted": internship.date_posted,
            "link": internship.link
        })
    
    return {"new_internships": notifications}


# ─── CHECK-INS ────────────────────────────────────────────────────────────────
@router.get("/checkins", response_class=HTMLResponse)
async def checkins(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items = (
        db.query(CheckIn)
        .filter(CheckIn.user_id == user.id)
        .order_by(CheckIn.date.desc())
        .all()
    )
    return templates.TemplateResponse(
        "checkins.html", {"request": request, "user": user, "checkins": items}
    )


# ─── REMINDERS ────────────────────────────────────────────────────────────────
@router.get("/reminders", response_class=HTMLResponse)
async def reminders(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items = (
        db.query(Reminder)
        .filter(Reminder.user_id == user.id)
        .order_by(Reminder.due_date.asc())
        .all()
    )
    return templates.TemplateResponse(
        "reminders.html", {"request": request, "user": user, "reminders": items}
    )


# ─── PROFILE ──────────────────────────────────────────────────────────────────
@router.get("/profile", response_class=HTMLResponse)
async def profile(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    watchlist = db.query(WatchlistItem).filter(WatchlistItem.user_id == user.id).all()
    application_logs = (
        db.query(ApplicationLog)
        .filter(ApplicationLog.user_id == user.id)
        .order_by(ApplicationLog.date_applied.desc())
        .all()
    )
    stats = {
        "watchlist_count": len(watchlist),
        "application_count": len(application_logs),
    }
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": user,
            "watchlist": watchlist,
            "application_logs": application_logs,
            "stats": stats,
        },
    )


# ─── AUTH (Register / Login / Logout) ─────────────────────────────────────────
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
            {"request": request, "msg": "Email already in use!"},
            status_code=400,
        )
    hashed_pw = hash_password(password)
    new_user = User(username=username, email=email, password_hash=hashed_pw)
    db.add(new_user)
    db.commit()
    return templates.TemplateResponse(
        "login.html", {"request": request, "msg": "Registration successful"}
    )


@router.get("/login", response_class=HTMLResponse)
async def display_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
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
            {"request": request, "msg": "Invalid username or password!"},
            status_code=400,
        )
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="user_id", value=str(user.id), httponly=True)
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("user_id")
    return response


# ─── WATCHLIST (Display / Add / Remove) ───────────────────────────────────────
@router.get("/watchlist", response_class=HTMLResponse)
async def display_watchlist(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items = db.query(WatchlistItem).filter(WatchlistItem.user_id == user.id).all()
    return templates.TemplateResponse(
        "display_watchlist.html",
        {"request": request, "user": user, "watchlist_items": items},
    )


@router.post("/add_to_watchlist", response_class=HTMLResponse)
async def add_to_watchlist(
    request: Request,
    company_name: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    exists = (
        db.query(WatchlistItem)
        .filter_by(user_id=user.id, company_name=company_name.strip())
        .first()
    )
    if exists:
        msg = f"{company_name} is already in your watchlist"
    else:
        new_item = WatchlistItem(user_id=user.id, company_name=company_name.strip())
        db.add(new_item)
        db.commit()

    return RedirectResponse(url="/watchlist", status_code=303)


@router.post("/remove_from_watchlist", response_class=HTMLResponse)
async def remove_from_watchlist(
    request: Request,
    item_id: int = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = db.query(WatchlistItem).get(item_id)
    if item and item.user_id == user.id:
        db.delete(item)
        db.commit()
        msg = f"Removed {item.company_name} from your watchlist"
    else:
        msg = "Could not find that item."

    items = db.query(WatchlistItem).filter(WatchlistItem.user_id == user.id).all()
    return RedirectResponse(url="/watchlist", status_code=303)


# ─── INTERNSHIPS ───────────────────────────────────────────────────────────────
@router.get("/internships", response_class=HTMLResponse)
async def show_matching_internships(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    company_names = (
        db.query(WatchlistItem.company_name)
        .filter(WatchlistItem.user_id == user.id)
        .all()
    )
    names = [c[0] for c in company_names]
    if not names:
        matched_internships = []

    else:
        conditions = [Internship.company.ilike(name) for name in names]
        matched_internships = (
            db.query(Internship)
            .filter(or_(*conditions))
            .order_by(Internship.date_posted.desc())
            .all()
        )
    return templates.TemplateResponse(
        "internship.html",
        {"request": request, "user": user, "internships": matched_internships},
    )

 # ─── APPLICATION LOGGING ──────────────────────────────────────────────────────
@router.post("/apply_internship")
async def apply_internship(
    request: Request,
    internship_id: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        # Debug: Print the received internship_id
        print(f"Received internship_id: '{internship_id}'")
        
        # Check if internship_id is empty or None
        if not internship_id or internship_id.strip() == "":
            print("Error: internship_id is empty")
            return RedirectResponse(url="/internships?error=empty_id", status_code=303)
        
        # Convert internship_id to integer
        internship_id_int = int(internship_id.strip())
        print(f"Converted internship_id to int: {internship_id_int}")
        
        # Get the internship details
        internship = db.query(Internship).filter(Internship.id == internship_id_int).first()
        
        if not internship:
            print(f"Error: No internship found with ID {internship_id_int}")
            return RedirectResponse(url="/internships?error=not_found", status_code=303)
        
        print(f"Found internship: {internship.company} - {internship.role}")
        
        # Check if user already applied to this specific internship
        existing_log = db.query(ApplicationLog).filter(
            ApplicationLog.user_id == user.id,
            ApplicationLog.company == internship.company,
            ApplicationLog.role == internship.role
        ).first()
        
        if existing_log:
            print(f"User {user.id} already applied to {internship.company} - {internship.role}")
            return RedirectResponse(url="/internships?error=already_applied", status_code=303)
        
        # Create application log with current date
        new_log = ApplicationLog(
            user_id=user.id,
            company=internship.company,
            role=internship.role,
            status="Applied",
            date_applied=datetime.now()
        )
        
        db.add(new_log)
        db.commit()
        db.refresh(new_log)  # Refresh to get the updated object
        
        print(f"Successfully logged application for user {user.id}")
        return RedirectResponse(url="/internships?success=applied", status_code=303)
        
    except ValueError as e:
        print(f"Invalid internship ID - ValueError: {e}")
        print(f"Problematic internship_id value: '{internship_id}'")
        return RedirectResponse(url="/internships?error=invalid_id", status_code=303)
    except Exception as e:
        print(f"Error logging application: {e}")
        db.rollback()
        return RedirectResponse(url="/internships?error=database_error", status_code=303)

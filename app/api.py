import os
from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from datetime import datetime, timezone, timedelta

from sqlalchemy import or_, cast, Date, String
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
    Badge,
)

from app.auth import (
    validate_password_strength,
    hash_password,
    verify_password,
    get_current_user,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "app", "templates"))
router = APIRouter()


# ─── BADGE HELPER FUNCTIONS ──────────────────────────────────────────────────
def get_badge_info(points: int):
    """Get badge information based on points."""
    badges = [
        {"name": "Getting Started", "description": "Earned your first 10 points", "points": 10, "emoji": "🌱"},
        {"name": "On Track", "description": "Reached 20 points", "points": 20, "emoji": "🚀"},
        {"name": "Consistent", "description": "Reached 30 points", "points": 30, "emoji": "⭐"},
        {"name": "Dedicated", "description": "Reached 40 points", "points": 40, "emoji": "💪"},
        {"name": "Achiever", "description": "Reached 50 points", "points": 50, "emoji": "🏆"},
        {"name": "Champion", "description": "Reached 60 points", "points": 60, "emoji": "👑"},
        {"name": "Master", "description": "Reached 70 points", "points": 70, "emoji": "🎯"},
        {"name": "Legend", "description": "Reached 80 points", "points": 80, "emoji": "💎"},
        {"name": "Elite", "description": "Reached 90 points", "points": 90, "emoji": "🔥"},
        {"name": "Ultimate", "description": "Reached 100 points", "points": 100, "emoji": "⚡"},
    ]
    
    # Add more badges for every 10 points beyond 100
    if points >= 100:
        extra_badges = (points // 10) - 9  # How many beyond the initial 10
        for i in range(10, 10 + extra_badges):
            badge_points = i * 10
            badges.append({
                "name": f"Superstar {i-9}",
                "description": f"Reached {badge_points} points",
                "points": badge_points,
                "emoji": "🌟"
            })
    
    return badges


def check_and_award_badges(db: Session, user: User):
    """Check if user has earned new badges and award them."""
    available_badges = get_badge_info(user.points)
    
    # Get already earned badges
    earned_badges = db.query(Badge).filter(Badge.user_id == user.id).all()
    earned_points = {badge.points_required for badge in earned_badges}
    
    # Find new badges to award
    new_badges = []
    for badge_info in available_badges:
        if badge_info["points"] <= user.points and badge_info["points"] not in earned_points:
            new_badge = Badge(
                user_id=user.id,
                badge_name=badge_info["name"],
                badge_description=badge_info["description"],
                points_required=badge_info["points"]
            )
            db.add(new_badge)
            new_badges.append(badge_info)
    
    if new_badges:
        db.commit()
    
    return new_badges


# ___ APP Home Page ____________________________________________________________
@router.get("/", response_class=HTMLResponse)
def home(
    request: Request,
):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"msg": "Hello World"},
    )


# ─── DASHBOARD ────────────────────────────────────────────────────────────────
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user_checkins = db.query(CheckIn).filter(user.id == CheckIn.user_id).all()

    # Convert to plain dicts
    checkin_dicts = [
        {"date": c.date.date().isoformat(), "note": c.note}  # "YYYY-MM-DD"
        for c in user_checkins
    ]

    watchlist = db.query(WatchlistItem).filter(WatchlistItem.user_id == user.id).all()
    application_logs = (
        db.query(ApplicationLog)
        .filter(ApplicationLog.user_id == user.id)
        .order_by(ApplicationLog.date_applied.desc())
        .all()
    )
    
    # Get user badges
    user_badges = (
        db.query(Badge)
        .filter(Badge.user_id == user.id)
        .order_by(Badge.earned_at.desc())
        .all()
    )
    
    # Get available badge info for progress display
    all_badge_info = get_badge_info(user.points)
    
    # Create a mapping of points to emoji for earned badges
    badge_info_map = {badge["points"]: badge for badge in all_badge_info}
    
    # Add emoji info to user badges
    user_badges_with_emoji = []
    for badge in user_badges:
        badge_dict = {
            "id": badge.id,
            "badge_name": badge.badge_name,
            "badge_description": badge.badge_description,
            "points_required": badge.points_required,
            "earned_at": badge.earned_at,
            "emoji": badge_info_map.get(badge.points_required, {}).get("emoji", "🏅")
        }
        user_badges_with_emoji.append(badge_dict)
    
    stats = {
        "watchlist_count": len(watchlist),
        "application_count": len(application_logs),
        "points": user.points,
    }

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "checkins": checkin_dicts,
            "current_year": datetime.now().year,
            "dashboard": 1,
            "watchlist": watchlist,
            "application_logs": application_logs,
            "stats": stats,
            "user_badges": user_badges_with_emoji,
            "all_badge_info": all_badge_info,
        },
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
    # .filter(Internship.date_posted >= yesterday)  # this was missing

    # Format response
    notifications = []
    for internship in new_internships:
        notifications.append(
            {
                "id": internship.id,
                "company": internship.company,
                "role": internship.role,
                "location": internship.location,
                "date_posted": internship.date_posted,
                "link": internship.link,
            }
        )

    return {"new_internships": notifications, "current_year": datetime.now().year}


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
        "checkins.html",
        {
            "request": request,
            "user": user,
            "checkins": items,
            "current_year": datetime.now().year,
        },
    )


# ─── REMINDERS ────────────────────────────────────────────────────────────────
# @router.get("/reminders", response_class=HTMLResponse)
# async def reminders(
#     request: Request,
#     db: Session = Depends(get_db),
#     user: User = Depends(get_current_user),
# ):
#     items = (
#         db.query(Reminder)
#         .filter(Reminder.user_id == user.id)
#         .order_by(Reminder.due_date.asc())
#         .all()
#     )
#     return templates.TemplateResponse(
#         "reminders.html",
#         {
#             "request": request,
#             "user": user,
#             "reminders": items,
#             "current_year": datetime.now().year,
#         },
#     )


# ─── AUTH (Register / Login / Logout) ─────────────────────────────────────────
@router.get("/register", response_class=HTMLResponse)
async def show_register_form(request: Request):
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "current_year": datetime.now().year},
    )


@router.post("/register", response_class=HTMLResponse)
async def register_user(
    request: Request,
    username: str = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    existing_user = (
        db.query(User)
        .filter((User.email == email) | (User.username == username))
        .first()
    )

    if existing_user:
        return templates.TemplateResponse(
            request,
            "register.html",
            {"msg": "Either username or email has already been used!"},
            status_code=400,
        )

    validate_password_strength(password)
    hashed_pw = hash_password(password)
    new_user = User(username=username, email=email, password_hash=hashed_pw)
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/login?msg=Registration+successful!", status_code=303)


@router.get("/login", response_class=HTMLResponse)
async def display_login(request: Request):
    msg = request.query_params.get("msg")
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "current_year": datetime.now().year,
            "msg": msg,
        },
    )


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
            {
                "request": request,
                "msg": "Invalid username or password!",
                "current_year": datetime.now().year,
            },
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
    page: int = 1,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    PER_PAGE = 10
    offset = (page - 1) * PER_PAGE

    all_companies = (
        db.query(Internship.company)
        .distinct()
        .order_by(Internship.company)
        .offset(offset)
        .limit(PER_PAGE)
        .all()
    )

    total_companies = db.query(Internship.company).distinct().count()
    total_pages = (total_companies + PER_PAGE - 1) // PER_PAGE

    watchlist_set = {
        item.company_name
        for item in db.query(WatchlistItem).filter(WatchlistItem.user_id == user.id)
    }
    companies = [
        {"name": c.company, "in_watchlist": c.company in watchlist_set}
        for c in all_companies
    ]

    return templates.TemplateResponse(
        "display_watchlist.html",
        {
            "request": request,
            "user": user,
            "companies": companies,
            "page": page,
            "total_pages": total_pages,
        },
    )


@router.post("/add_to_watchlist", response_class=HTMLResponse)
async def add_to_watchlist(
    request: Request,
    company_name: str = Form(...),
    page: int = Form(1),
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

    return RedirectResponse(url=f"/watchlist?page={page}", status_code=303)


@router.post("/remove_from_watchlist", response_class=HTMLResponse)
async def remove_from_watchlist(
    request: Request,
    company_name: str = Form(...),
    page: int = Form(1),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = (
        db.query(WatchlistItem)
        .filter_by(user_id=user.id, company_name=company_name.strip())
        .first()
    )
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse(url=f"/watchlist?page={page}", status_code=303)


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
        watchlist_stats = []
    else:
        conditions = [Internship.company.ilike(f'%{name}%') for name in names]
        matched_internships = (
            db.query(Internship)
            .filter(or_(*conditions))
            .filter(Internship.active == True)
            .order_by(Internship.date_posted.desc())
            .all()
        )
        
        # Generate statistics for each watchlist company
        watchlist_stats = []
        for name in names:
            count = (
                db.query(Internship)
                .filter(Internship.company.ilike(f'%{name}%'))
                .filter(Internship.active == True)
                .count()
            )
            watchlist_stats.append({"company": name, "count": count})
    
    return templates.TemplateResponse(
        "internship.html",
        {
            "request": request,
            "user": user,
            "internships": matched_internships,
            "watchlist_stats": watchlist_stats,
            "current_year": datetime.now().year,
        },
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
        # Check if internship_id is empty or None
        if not internship_id or internship_id.strip() == "":
            print("Error: internship_id is empty")
            return RedirectResponse(url="/internships?error=empty_id", status_code=303)

        # Convert internship_id to integer
        internship_id = internship_id.strip()

        # Get the internship details
        internship = db.query(Internship).filter(Internship.id == internship_id).first()

        if not internship:
            print(f"Error: No internship found with ID {internship_id}")
            return RedirectResponse(url="/internships?error=not_found", status_code=303)

        print(f"Found internship: {internship.company} - {internship.role}")

        # Check if user already applied to this specific internship
        existing_log = (
            db.query(ApplicationLog)
            .filter(
                ApplicationLog.user_id == user.id,
                ApplicationLog.company == internship.company,
                ApplicationLog.role == internship.role,
            )
            .first()
        )

        if existing_log:
            print(
                f"User {user.id} already applied to {internship.company} - {internship.role}"
            )
            return RedirectResponse(
                url="/internships?error=already_applied", status_code=303
            )

        # Create application log with current date
        new_log = ApplicationLog(
            user_id=user.id,
            company=internship.company,
            role=internship.role,
            status="Applied",
            date_applied=datetime.now(),
        )

        db.add(new_log)
        # Increment user points for logging an application
        db_user = db.query(User).filter(User.id == user.id).first()
        db_user.points += 5
        
        # Check for new badges
        new_badges = check_and_award_badges(db, db_user)
        
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
        return RedirectResponse(
            url="/internships?error=database_error", status_code=303
        )


@router.post("/api/checkin")
async def checkin_today(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    today = datetime.now(timezone.utc).date()
    exists = (
        db.query(CheckIn)
        .filter(CheckIn.user_id == user.id)
        .filter(CheckIn.date.cast(Date) == today)
        .first()
    )
    if exists:
        return JSONResponse(content={"message": "Already checked in"}, status_code=400)

    new_checkin = CheckIn(user_id=user.id, date=datetime.now(timezone.utc))
    db_user = db.query(User).filter(User.id == user.id).first()
    db_user.points += 2

    # Check for new badges
    new_badges = check_and_award_badges(db, db_user)

    db.add(new_checkin)
    db.commit()
    
    response_data = {"message": "Check-in successful", "points": db_user.points}
    if new_badges:
        response_data["new_badges"] = new_badges
    
    return JSONResponse(response_data)

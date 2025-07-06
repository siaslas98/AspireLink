import os
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import router            # your existing API routes
from app.auth import get_current_user  # just added

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()

# 1️⃣ Serve CSS/JS under /static
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static",
)

# 2️⃣ Load Jinja2 templates from app/templates
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# 3️⃣ Wire up your existing API router (register, login, watchlist, etc.)
app.include_router(router)

# 4️⃣ Dashboard route (requires login)
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user=Depends(get_current_user)):
    """
    Renders the dashboard for authenticated users.
    """
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": user},
    )

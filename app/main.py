import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import router  # all routes including /dashboard now live here

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()

# Serve CSS/JS under /static
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static",
)

# Setup Jinja2 templates (used by api routes)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Include all your API routes
app.include_router(router)

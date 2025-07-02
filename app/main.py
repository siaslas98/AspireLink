from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

from app.api import router

# Initialize server
app = FastAPI()

# /app
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount(
    "/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static"
)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

app.include_router(router)

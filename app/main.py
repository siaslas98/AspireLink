import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import router  # all routes (including /dashboard & /profile) live here

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()

# Serve your CSS/JS under /static
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static",
)

# Include all of your API routes at the root
app.include_router(router)

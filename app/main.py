import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.routes import jobs

# Initialize the FastAPI Application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Scalable background processing API powered by FastAPI, Redis, and Celery.",
    version="1.0.0",
)

# Set up CORS middleware for third-party integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core API routes registration
app.include_router(jobs.router, prefix="/api")

# Verify directories exist for static assets and templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")
template_dir = os.path.join(BASE_DIR, "templates")

os.makedirs(static_dir, exist_ok=True)
os.makedirs(template_dir, exist_ok=True)

# Mount the static directory for CSS, JS, and Images
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Initialize Jinja2 Templates engine
templates = Jinja2Templates(directory=template_dir)


@app.get("/", response_class=HTMLResponse, tags=["Web Console"])
async def render_dashboard(request: Request):
    """
    Renders the unified, premium dark-mode dashboard serving the Landing page,
    interactive queue console, and detailed task execution progress tracking.
    """
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "project_name": settings.PROJECT_NAME, "env": settings.ENV}
    )


@app.get("/health", tags=["System Health"])
async def health_check():
    """
    Simple health status checker verifying the web API instance is running.
    """
    return {"status": "healthy", "service": settings.PROJECT_NAME}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

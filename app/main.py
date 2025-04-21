# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.db import engine
from app.model import Base
from app.api.upload import router as upload_router
from app.api.stats import router as stats_router
from app.worker import poll_forever 
import asyncio
import contextlib

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

    # kick‑off background poller
    poller_task = asyncio.create_task(poll_forever())
    yield
    # shutdown
    poller_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await poller_task

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/")
def upload_form(request: Request):
    return templates.TemplateResponse("upload_form.html", {"request": request})

@app.get("/stats")
def stats_page(request: Request):
    return templates.TemplateResponse("stats.html", {"request": request})

app.include_router(upload_router, prefix="/api")
app.include_router(stats_router, prefix="/api/stats")
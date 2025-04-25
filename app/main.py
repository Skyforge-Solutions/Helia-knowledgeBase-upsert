# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.database.db import engine
from app.database.model import Base
from app.api.upload import router as upload_router
from app.api.stats import router as stats_router
from pinecone_admin.api import router as pinecone_admin_router
from app.job.worker import poll_forever 
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
pinecone_admin_templates = Jinja2Templates(directory="pinecone_admin/templates")

@app.get("/")
def upload_form(request: Request):
    return templates.TemplateResponse("upload_form.html", {"request": request})

@app.get("/stats")
def stats_page(request: Request):
    return templates.TemplateResponse("stats.html", {"request": request})

@app.get("/pinecone-admin")
def pinecone_admin_page(request: Request):
    return pinecone_admin_templates.TemplateResponse("index.html", {"request": request})

app.include_router(upload_router, prefix="/api")
app.include_router(stats_router, prefix="/api/stats")
app.include_router(pinecone_admin_router, prefix="/pinecone-admin/api")


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
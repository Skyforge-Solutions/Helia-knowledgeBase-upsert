from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.db import engine
from app.model import Base
from app.api.upload import router as upload_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # create tables at startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # clear any prepared plans / old connections
    await engine.dispose()
    yield
    # (shutdown cleanup, if needed)

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/")
def upload_form(request: Request):
    return templates.TemplateResponse("upload_form.html", {"request": request})

app.include_router(upload_router, prefix="/api")
import time

from diskcache import Cache
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import models
from .database import SessionLocal, engine

templates: Jinja2Templates = Jinja2Templates(directory="server/templates")
cache: Cache = Cache(directory=".cache")

models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# application factory pattern
def create_app() -> FastAPI:
    app = FastAPI()
    from .jobs import router as jobs_router

    app.include_router(jobs_router)

    app.mount("/static", StaticFiles(directory="server/static"), name="static")

    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        print(f"call in {time.time() - start_time} sec")
        return response

    return app

import time

from diskcache import Cache
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

templates: Jinja2Templates = Jinja2Templates(directory="server/templates")
cache: Cache = Cache(directory=".cache")


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

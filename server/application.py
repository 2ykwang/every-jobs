import time

from fastapi import FastAPI, Request


# application factory pattern
def create_app() -> FastAPI:
    app = FastAPI()

    from .jobs import router as jobs_router

    app.include_router(jobs_router)

    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        print(f"call in {time.time() - start_time} sec")
        return response

    return app

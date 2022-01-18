import asyncio
import math
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from .application import templates
from .scrapping import IndeedScrapper

router = APIRouter()

a = IndeedScrapper()
PER_PAGE = 10
SEARCH_MAX_PAGE = 10

cache = {}


async def __insert_data(query: str) -> None:
    if query not in cache.keys() or len(cache[query]) < 1:
        results = await asyncio.gather(
            *[a.search(query, x) for x in range(0, SEARCH_MAX_PAGE)]
        )

        jobs = []
        for result in results:
            for job in result:
                jobs.append(job)
        if len(jobs) > 0:
            cache[query] = jobs


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "main.html",
        context={"request": request},
    )


@router.get("/search", response_class=HTMLResponse)
async def read_jobs(request: Request, q: str, page: Optional[int] = 1):
    try:
        await __insert_data(q)
    except Exception as e:
        print(e)

    jobs = cache.get(q, [])
    max_page = math.ceil(len(jobs) / PER_PAGE)

    start = (page - 1) * PER_PAGE
    count = len(jobs)
    print(count)
    display_jobs = jobs[start : start + PER_PAGE]  # noqa:E203
    return templates.TemplateResponse(
        "main.html",
        context={
            "query": q,
            "request": request,
            "jobs": display_jobs,
            "page": page,
            "max_page": max_page,
            "count": count,
        },
    )

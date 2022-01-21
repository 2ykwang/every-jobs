import asyncio
import csv
import io
import math
import random
from typing import Any, Iterable, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy.orm import Session

from .application import cache, get_db, templates
from .models import (
    create_keyword_or_increase,
    get_keyword_count,
    get_keywords,
    get_top_keywords,
)
from .scrapping import IndeedScrapper, SOFScrapper

router = APIRouter()

sof = SOFScrapper()
indeed = IndeedScrapper()
PER_PAGE = 10
SEARCH_MAX_PAGE = 5


def __get_jobs_from_keyword(query: str) -> List[Any]:
    data = cache.get(query, [])
    return data


def __insert_jobs_in_cache(query: str, jobs: List[Any]) -> List[Any]:
    data = cache.get(query, [])
    for job in jobs:
        data.append(job)
    day = 60 * 60 * 24
    cache.set(query, data, expire=day)
    return data


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    keywords = [x.keyword for x in get_top_keywords(db, 7)]

    return templates.TemplateResponse(
        "main.html",
        context={"request": request, "recommend_keywords": keywords},
    )


@router.get("/download")
async def get_csv(request: Request, q: str):
    q = q.lower()
    jobs = __get_jobs_from_keyword(q)

    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["title", "company", "location", "link"])
    for job in jobs:
        try:
            writer.writerow(
                [job["title"], job["company"]["name"], job["location"], job["url"]]
            )
        except Exception as e:
            print(e)

    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")

    response.headers["Content-Disposition"] = "attachment; filename=export.csv"

    return response


async def __add_jobs_work(query: str):
    for i in range(2, SEARCH_MAX_PAGE + 1):
        print(i)
        results = await asyncio.gather(
            sof.search(query, i), indeed.search(query, i), return_exceptions=True
        )
        await run_in_threadpool(__make_jobs_data, query, results)


def __make_jobs_data(query, results):
    data = []
    for result in results:
        if result is None or isinstance(result, Exception):
            continue
        for job in result:
            data.append(job)
    random.shuffle(data)
    __insert_jobs_in_cache(query, data)


async def __add_jobs_wrapper(query: str) -> None:
    loop = asyncio.get_event_loop()
    loop.create_task(__add_jobs_work(query))


@router.get("/search", response_class=HTMLResponse)
async def read_jobs(
    request: Request,
    q: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    page: Optional[int] = 1,
):
    q = q.lower()
    jobs = __get_jobs_from_keyword(q)

    if len(jobs) < 1:
        results = await asyncio.gather(sof.search(q, 1), indeed.search(q, 1))
        data = []
        for result in results:
            if result is None:
                continue
            for job in result:
                data.append(job)

        random.shuffle(data)
        jobs = __insert_jobs_in_cache(q, data)
        background_tasks.add_task(__add_jobs_wrapper, q)

    max_page = math.ceil(len(jobs) / PER_PAGE)
    start = (page - 1) * PER_PAGE
    count = len(jobs)

    display_jobs = jobs[start : start + PER_PAGE]  # noqa:E203

    if page == 1:
        create_keyword_or_increase(db, q)

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

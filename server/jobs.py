import asyncio
import csv
import io
import math
import random
from typing import Any, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Request
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


async def __insert_data(query: str, data: List[Any]) -> None:
    data = cache.get(query, [])
    if len(data) < 1:
        results = await asyncio.gather(
            *[sof.search(query, x) for x in range(0, SEARCH_MAX_PAGE)],
            *[indeed.search(query, x) for x in range(0, SEARCH_MAX_PAGE)]
        )
        jobs = []
        for result in results:
            if result is None:
                continue
            for job in result:
                jobs.append(job)

        random.shuffle(jobs)
        if len(jobs) > 0:
            day = 60 * 60 * 24
            cache.set(query, jobs, expire=day)


async def __get_jobs(q):
    try:
        await __insert_data(q)
    except Exception as e:
        print(e)

    jobs = cache.get(q, [])
    return jobs


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
    jobs = await __get_jobs(q)

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


async def add_jobs(query: str) -> None:
    results = await asyncio.gather(
        *[sof.search(query, x) for x in range(2, 2 + SEARCH_MAX_PAGE)],
        *[indeed.search(query, x) for x in range(2, 2 + SEARCH_MAX_PAGE)]
    )
    data = []
    for result in results:
        if result is None:
            continue
        for job in result:
            data.append(job)
    random.shuffle(data)
    __insert_jobs_in_cache(query, data)


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
        background_tasks.add_task(add_jobs, q)

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

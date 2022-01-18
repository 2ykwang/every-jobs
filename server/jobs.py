import asyncio
import csv
import functools
import io
import math
import random
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse

from .application import cache, templates
from .scrapping import IndeedScrapper, SOFScrapper

router = APIRouter()

sof = SOFScrapper()
indeed = IndeedScrapper()
PER_PAGE = 10
SEARCH_MAX_PAGE = 5


async def __insert_data(query: str) -> None:
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
async def index(request: Request):
    return templates.TemplateResponse(
        "main.html",
        context={"request": request},
    )


@router.get("/download")
async def get_csv(request: Request, q: str):
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


@router.get("/search", response_class=HTMLResponse)
async def read_jobs(request: Request, q: str, page: Optional[int] = 1):
    jobs = await __get_jobs(q)

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

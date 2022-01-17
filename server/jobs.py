import asyncio

from fastapi import APIRouter, Request

from .scrapping import IndeedScrapper

router = APIRouter()

a = IndeedScrapper(per_page=3)


@router.get("/jobs/{query}")
async def read_jobs(request: Request, query: str):
    print(query)
    result = await asyncio.gather(*[a.search(query, x) for x in range(0, 1)])
    print(result)
    # for i in range(1, 5):
    #     await a.search("flask", i)

    return "dd"

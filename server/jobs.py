import asyncio

from fastapi import APIRouter, Request

from .scrapping import IndeedScrapper

router = APIRouter()

a = IndeedScrapper(per_page=50)


@router.get("/jobs/{query}")
async def read_jobs(request: Request, query: str):
    print(query)
    response = []
    results = await asyncio.gather(*[a.search(query, x) for x in range(0, 5)])

    for result in results:
        for job in result:
            response.append(job)

    # print(response)
    return response

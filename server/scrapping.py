from abc import ABCMeta, abstractmethod

import httpx


class BaseScrapper(metaclass=ABCMeta):
    def __init__(self):
        self._client: httpx.AsyncClient = httpx.AsyncClient()

    @abstractmethod
    def search(self, page):
        pass


class IndeedScrapper(BaseScrapper):
    def __init__(
        self,
        per_page: int = 50,
    ):
        super().__init__()
        self.per_page: int = per_page
        self.base_url: str = "https://www.indeed.com"

    async def search(self, query: str, page: int):
        search_page = (page - 1) * self.per_page

        response = await self._client.get(
            f"{self.base_url}/jobs?q={query}&start={search_page}&limit={self.per_page}"
        )
        return response


class ScrapJobs:
    def __init__(self):
        self.client: httpx.AsyncClient = httpx.AsyncClient()

    async def fetch(self) -> httpx.Response:
        pass

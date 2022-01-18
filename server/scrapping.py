from abc import ABCMeta, abstractmethod
from typing import Iterable

import httpx
from bs4 import BeautifulSoup


class BaseScrapper(metaclass=ABCMeta):
    def __init__(self):
        self._client: httpx.AsyncClient = httpx.AsyncClient()
        self.per_page: int = 10
        self.base_url: str = ""

    @abstractmethod
    async def search(self, query: str, page: int) -> Iterable[dict]:
        pass


class SOFScrapper(BaseScrapper):
    def __init__(self):
        super().__init__()
        self.base_url: str = "https://stackoverflow.com/"

    def __parse_page(self, html: str) -> Iterable[dict]:
        pass

    async def search(self, query: str, page: int) -> Iterable[dict]:
        response = await self._client.get(f"{self.base_url}/jobs?q={query}&pg={page}")
        result = self.__parse_page(response.text)

        return result


class IndeedScrapper(BaseScrapper):
    def __init__(
        self,
        per_page: int = 50,
    ):
        super().__init__()
        self.per_page: int = per_page
        self.base_url: str = "https://www.indeed.com"

    def __parse_page(self, html: str) -> Iterable[dict]:
        result = []

        bs = BeautifulSoup(html, "html.parser")

        jobs = bs.find_all("a", {"class", "sponTapItem"})
        for job in jobs:
            # job title
            title = (
                job.find("h2", {"class": "jobTitle"})
                .find("span", {"title": True})
                .get_text()
            )
            # job url
            url = f"{self.base_url}/viewjob?jk={job['data-jk']}"

            # job company
            company = job.find("span", {"class": "companyName"})
            companyUrl = f"{self.base_url}{job.find('a')['href']}"
            companyName = company.get_text()

            # job location
            location = job.find("div", {"class": "companyLocation"}).get_text()

            job_dict = {
                "title": title,
                "url": url,
                "company": {"name": companyName, "url": companyUrl},
                "location": location,
            }
            result.append(job_dict)

        # print(result)
        return result

    async def def_get_max_page(self, query: str):
        pass

    async def search(self, query: str, page: int) -> Iterable[dict]:
        search_page = (page - 1) * self.per_page

        response = await self._client.get(
            f"{self.base_url}/jobs?q={query}&start={search_page}&limit={self.per_page}"
        )
        result = self.__parse_page(response.text)

        return result

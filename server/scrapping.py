import time
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
        self.base_url: str = "https://stackoverflow.com"

    def __parse_page(self, html: str) -> Iterable[dict]:

        result = []
        bs = BeautifulSoup(html, "html.parser")
        jobs = bs.find_all("div", {"class", "js-result"})
        for job in jobs:
            title_selector = job.find("a", {"class", "stretched-link"})
            title = title_selector.get_text()
            url = f"{self.base_url}{title_selector['href']}"

            company_selector = job.find("h3")
            span_selector = company_selector.find_all("span")
            company_name = span_selector[0].get_text().strip()
            company_url = ""

            location = span_selector[1].get_text().strip() if span_selector[1] else ""

            job_dict = {
                "title": title,
                "url": url,
                "company": {"name": company_name, "url": company_url},
                "location": location,
            }
            result.append(job_dict)
        return result

    async def search(self, query: str, page: int) -> Iterable[dict]:
        response = await self._client.get(
            f"{self.base_url}/jobs?q={query}&pg={page}", follow_redirects=True
        )
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
        a = time.time()

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
            company_url_selector = job.find("a")
            company_url = (
                f"{self.base_url}{job.find('a')['href']}"
                if company_url_selector
                else None
            )
            company_name = company.get_text()

            # job location
            location = job.find("div", {"class": "companyLocation"}).get_text()

            job_dict = {
                "title": title,
                "url": url,
                "company": {"name": company_name, "url": company_url},
                "location": location,
            }
            result.append(job_dict)
        print(f"{time.time()-a} tick")
        # print(result)
        return result

    async def def_get_max_page(self, query: str):
        pass

    async def search(self, query: str, page: int) -> Iterable[dict]:
        search_page = (page - 1) * self.per_page
        a = time.time()
        response = await self._client.get(
            f"{self.base_url}/jobs?q={query}&start={search_page}&limit={self.per_page}"
        )
        print(f"{time.time()-a} tick")
        result = self.__parse_page(response.text)

        return result

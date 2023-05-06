from dataclasses import dataclass
from urllib.parse import urlparse
from typing import Iterator, Union

import requests
from flask import abort
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from ozgursozluk.config import DEFAULT_EKSI_BASE_URL


@dataclass
class Gundem:
    title: str
    pinned: bool
    permalink: str
    views: Union[str, None] = None


@dataclass
class Debe:
    title: str
    permalink: str


@dataclass
class Entry:
    id: str
    content: str
    author: str
    datetime: str
    permalink: str


@dataclass
class Author:
    nickname: str
    entry_total_count: int
    user_follower_count: int
    user_following_count: int
    avatar_link: str
    level: Union[str, None] = None
    biography: Union[str, None] = None


@dataclass
class Topic:
    id: str
    title: str
    path: str
    permalink: str
    entrys: Iterator[Entry]
    pagecount: int = 0
    nice: Union[bool, None] = None


class Eksi:
    def __init__(self, base_url: str = DEFAULT_EKSI_BASE_URL) -> None:
        self.base_url = base_url
        self.headers = {"User-Agent": UserAgent().random}

    def _get(self, endpoint: str = "/", params: dict = {}) -> dict:
        response = requests.get(
            f"{self.base_url}{endpoint}", params=params, headers=self.headers,
        )

        if response.status_code != 200:
            abort(response.status_code)

        return response

    def _get_entrys(self, soup: BeautifulSoup) -> Iterator[Entry]:
        entry_items = soup.find_all("li", id="entry-item")

        for entry in entry_items:
            a = entry.find("a", class_="entry-date permalink", href=True)
            yield Entry(
                entry.attrs["data-id"],
                entry.find("div", class_="content"),
                entry.find("a", class_="entry-author").text,
                a.text,
                self.base_url + a["href"],
            )

    def search_topic(self, q: str) -> Topic:
        response = self._get("/", {"q": q})
        soup = BeautifulSoup(response.content, "html.parser")
        h1 = soup.find("h1", id="title")
        pager = soup.find("div", class_="pager")

        return Topic(
            h1.attrs["data-id"],
            h1.attrs["data-title"],
            urlparse(response.url).path[1:],
            self.base_url + h1.find("a", href=True)["href"],
            self._get_entrys(soup),
            int(pager.attrs["data-pagecount"]) if pager is not None else 0,
        )

    def get_topic(self, title: str, page: int = 1, a: str = None) -> Topic:
        if a is None:
            response = self._get(f"/{title}", {"p": page})
        else:
            response = self._get(f"/{title}", {"a": a, "p": page})

        soup = BeautifulSoup(response.content, "html.parser")
        h1 = soup.find("h1", id="title")
        pager = soup.find("div", class_="pager")

        return Topic(
            h1.attrs["data-id"],
            h1.attrs["data-title"],
            urlparse(response.url).path[1:],
            self.base_url + h1.find("a", href=True)["href"],
            self._get_entrys(soup),
            int(pager.attrs["data-pagecount"]) if pager is not None else 0,
            a == "nice",
        )

    def get_entry(self, id: str) -> Topic:
        response = self._get(f"/entry/{id}")
        soup = BeautifulSoup(response.content, "html.parser")
        h1 = soup.find("h1", id="title")

        return Topic(
            h1.attrs["data-id"],
            h1.attrs["data-title"],
            h1.find("a")["href"][1:],
            self.base_url + h1.find("a", href=True)["href"],
            self._get_entrys(soup),
        )

    def get_gundem(self, page: int = 1) -> Iterator[Gundem]:
        response = self._get("/basliklar/gundem", {"p": page})
        soup = BeautifulSoup(response.content, "html.parser")
        topic_list = soup.find("ul", class_="topic-list").find_all("a", href=True)

        for topic in topic_list:
            yield Gundem(
                topic.contents[0],
                topic.has_attr("class"),
                topic["href"],
                None if len(topic.contents) < 2 else topic.contents[1],
            )

    def get_debe(self) -> Iterator[Debe]:
        response = self._get("/debe")
        soup = BeautifulSoup(response.content, "html.parser")
        topic_list = soup.find("ul", class_="topic-list").find_all("a", href=True)

        for topic in topic_list:
            yield Debe(
                topic.find("span", class_="caption").text,
                topic["href"],
            )

    def get_author(self, nickname: str) -> Author:
        response = self._get(f"/biri/{nickname}")
        soup = BeautifulSoup(response.content, "html.parser")
        muted = soup.find("p", class_="muted")
        biography = soup.find("div", id="profile-biography")

        return Author(
            nickname,
            soup.find("span", id="entry-count-total").text,
            soup.find("span", id="user-follower-count").text,
            soup.find("span", id="user-following-count").text,
            soup.find("img", class_="logo avatar").attrs["src"],
            None if muted is None else muted.text,
            None if biography is None else biography.find("div"),
        )

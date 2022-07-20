import os
import re
from datetime import date
from logging import DEBUG, INFO, Formatter, StreamHandler, getLogger
from pathlib import Path
from time import sleep
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from urllib3.util.retry import Retry


class Crawler:
    def __init__(self, outdir: Path, target_year: Optional[int], verbose: bool) -> None:
        self.outdir = outdir.resolve(strict=True)
        if not self.outdir.is_dir():
            raise FileNotFoundError(f"{self.outdir} is not a directory")
        self.target_year = target_year if target_year is not None else date.today().year

        # logger
        self.logger = getLogger(__name__)
        if verbose:
            self.logger.setLevel(DEBUG)
        else:
            self.logger.setLevel(INFO)
        sh = StreamHandler()
        sh.setFormatter(
            Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        self.logger.addHandler(sh)
        # http client
        self.client = requests.Session()
        self.client.mount(
            "https://",
            requests.adapters.HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1)),
        )
        # regexp
        self.re_title = re.compile(
            r"^(?P<date_y>\d+)年(?P<date_m>\d+)\s*月(?P<date_d>\d+)\s*日"
            r"の詰将棋（.*?(?P<number>\d+)手詰）"
        )
        self.re_kif_url = re.compile(r"'(.+\.kif)'")

    def run(self) -> None:
        self.get_index("https://www.shogi.or.jp/tsume_shogi/everyday/")

    def get_index(self, url: str) -> None:
        self.logger.info(f"get index: {url}")
        soup = self.get_soup(url)

        for item in soup.select("#contents > ul li a"):
            assert type(item["href"]) == str
            sleep(0.5)
            if self.get(item["href"]):
                return

        if next := soup.select_one("li.next a"):
            assert type(next["href"]) == str
            sleep(1.0)
            self.get_index(next["href"])

    def get(self, url: str) -> bool:
        self.logger.info(f"get: {url}")
        try:
            soup = self.get_soup(url)
            assert soup.title and soup.title.text
            self.logger.debug(soup.title.text)
            match = self.re_title.match(soup.title.text)
            assert match
            d = date(*[int(match.group(g)) for g in ["date_y", "date_m", "date_d"]])
            if d.year < 2000:
                # https://www.shogi.or.jp/tsume_shogi/everyday/02251011.html
                d = d.replace(year=d.year + 2000)
            # Skip or Finish
            if d.year != self.target_year:
                return d.year < self.target_year

            dir = self.outdir / f"{d.year:04d}"
            dir.mkdir(exist_ok=True)
            prefix = "{}_{:03d}_".format(
                d.strftime("%Y-%m-%d"), int(match.group("number"))
            )

            script = soup.find("script", text=self.re_kif_url)
            assert script and script.text
            m = self.re_kif_url.search(script.text)
            assert m
            self.download_kif(m.group(1), dir, prefix)
        except Exception as e:
            self.logger.error(e)

        return False

    def get_soup(self, url: str) -> BeautifulSoup:
        res = self.client.get(url)
        res.raise_for_status()
        return BeautifulSoup(res.content, "html.parser")

    def download_kif(self, url: str, dir: Path, prefix: str) -> None:
        self.logger.info(f"download: {url}")
        filename = os.path.basename(urlparse(url).path)
        res = self.client.get(url)
        with (dir / (prefix + filename)).open("wb") as fp:
            fp.write(res.content)

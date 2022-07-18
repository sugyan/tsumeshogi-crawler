from logging import DEBUG, Formatter, StreamHandler, getLogger
from time import sleep

import requests
from bs4 import BeautifulSoup


class Crawler:
    def __init__(self) -> None:
        self.logger = getLogger(__name__)
        self.logger.setLevel(DEBUG)
        sh = StreamHandler()
        sh.setFormatter(
            Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        self.logger.addHandler(sh)

    def run(self) -> None:
        self.get_index("https://www.shogi.or.jp/tsume_shogi/everyday/")

    def get_index(self, url: str) -> None:
        res = requests.get(url)
        soup = BeautifulSoup(res.content, "html.parser")
        next = soup.select("li.next a")[0].get("href")
        if next and type(next) == str:
            self.logger.debug(next)
            sleep(1.0)
            self.get_index(next)

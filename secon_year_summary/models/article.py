"""
secon.dev の記事を取得・解析するためのモジュール
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set

import aiohttp
from bs4 import BeautifulSoup


@dataclass
class Article:
    """記事データモデル"""

    url: str
    title: str
    content: str
    image_url: Optional[str]
    year: int
    month: int
    day: int

    @property
    def date_str(self) -> str:
        """YYYY年MM月DD日 形式の日付文字列を返す"""
        return f"{self.year}年{self.month}月{self.day}日"


class ArticleFetcher:
    """同じ日付の過去の記事を取得するクラス"""

    BASE_URL = "https://secon.dev/entry"
    TIME_SUFFIX = "210000"  # URLの末尾の固定部分

    def __init__(self, target_date: datetime, years_back: int = 10):
        """
        Args:
            target_date: 対象となる日付
            years_back: 何年前まで遡るか
        """
        self.target_date = target_date
        self.years_back = years_back

    async def fetch_articles(self) -> List[Article]:
        """指定された日付の過去の記事を非同期で取得する"""
        # 取得するURLのリストを作成
        urls_to_fetch = []
        current_year = self.target_date.year

        for year in range(current_year - self.years_back, current_year):
            # 指定された月日の記事URL
            url = (
                f"{self.BASE_URL}/{year}/{self.target_date.month:02d}/"
                f"{self.target_date.day:02d}/{self.TIME_SUFFIX}/"
            )
            urls_to_fetch.append(
                (url, year, self.target_date.month, self.target_date.day)
            )

        # 非同期で記事を取得
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._fetch_article(session, url, year, month, day)
                for url, year, month, day in urls_to_fetch
            ]
            articles = await asyncio.gather(*tasks)

        # Noneを除外
        return [article for article in articles if article is not None]

    async def _fetch_article(
        self, session: aiohttp.ClientSession, url: str, year: int, month: int, day: int
    ) -> Optional[Article]:
        """記事を非同期で取得し、記事オブジェクトを返す"""
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return None

                html = await response.text()
                return self._parse_article(html, url, year, month, day)
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def _parse_article(
        self, html: str, url: str, year: int, month: int, day: int
    ) -> Optional[Article]:
        """HTMLを解析して記事オブジェクトを作成する"""
        soup = BeautifulSoup(html, "html.parser")

        # タイトルの抽出（headのtitleタグから取得）
        title_tag = soup.find("title")
        if not title_tag:
            # head内のtitleがない場合はh1タグから取得を試みる
            title_tag = soup.find("h1")
            if not title_tag:
                return None

        title = title_tag.get_text(strip=True)

        # サイト名がタイトルに含まれているかもしれないので、適切に処理する
        # 例: "記事タイトル - サイト名" の形式であれば、サイト名を除外
        if " - " in title:
            title = title.split(" - ")[0]

        # 本文の抽出（記事本文はentry-contentクラスやarticleタグなどにあると想定）
        content_tag = soup.find(class_="entry-content") or soup.find("article")
        if not content_tag:
            return None

        # 本文からスクリプトやスタイルを除外
        for tag in content_tag.find_all(["script", "style"]):
            tag.decompose()

        content = content_tag.get_text(strip=True)

        # OG画像の抽出
        image_url = None
        og_image = soup.find("meta", property="og:image")
        if og_image and "content" in og_image.attrs:
            image_url = og_image["content"]

        return Article(
            url=url,
            title=title,
            content=content,
            image_url=image_url,
            year=year,
            month=month,
            day=day,
        )


# テスト用のコード
async def test_fetcher():
    """ArticleFetcherのテスト"""
    today = datetime.now()
    fetcher = ArticleFetcher(today, years_back=3)
    articles = await fetcher.fetch_articles()

    for article in articles:
        print(f"Year: {article.year}, Title: {article.title}")
        print(f"URL: {article.url}")
        print(f"Image: {article.image_url}")
        print(f"Content: {article.content[:100]}...")
        print("-" * 50)


if __name__ == "__main__":
    asyncio.run(test_fetcher())

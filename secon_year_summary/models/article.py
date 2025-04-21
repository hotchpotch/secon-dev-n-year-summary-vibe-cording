"""
secon.dev の記事を取得・解析するためのモジュール
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List
from urllib.parse import urlparse

import aiohttp
from bs4 import BeautifulSoup, Tag


@dataclass
class Article:
    """記事データモデル"""

    url: str
    title: str
    content: str
    image_url: str | None
    year: int
    month: int
    day: int
    n_diary_urls: List[str] = field(default_factory=list)  # type: ignore

    @property
    def date_str(self) -> str:
        """YYYY年MM月DD日 形式の日付文字列を返す"""
        return f"{self.year}年{self.month}月{self.day}日"


class ArticleFetcher:
    """同じ日付の過去の記事を取得するクラス"""

    BASE_URL = "https://secon.dev/entry"
    TIME_SUFFIX = "210000"  # URLの末尾の固定部分

    def __init__(self, target_date: datetime, years_back: int = 10) -> None:
        """
        Args:
            target_date: 対象となる日付
            years_back: 何年前まで遡るか
        """
        self.target_date = target_date
        self.years_back = years_back

    async def fetch_articles(self) -> list[Article]:
        """指定された日付の過去の記事を非同期で取得する"""
        # まず対象日の記事を取得し、そこから関連記事のURLを抽出
        target_url = (
            f"{self.BASE_URL}/{self.target_date.year}/{self.target_date.month:02d}/"
            f"{self.target_date.day:02d}/{self.TIME_SUFFIX}/"
        )

        async with aiohttp.ClientSession() as session:
            # 対象日の記事を取得
            target_article = await self._fetch_article(
                session,
                target_url,
                self.target_date.year,
                self.target_date.month,
                self.target_date.day,
            )

            if not target_article:
                print(f"対象日の記事が見つかりませんでした: {target_url}")
                return []

            # 対象日の記事から過去の関連記事のURLを取得
            n_diary_urls = self._get_n_diary_urls(target_article.n_diary_urls, target_article, self.years_back)

            if not n_diary_urls:
                # 関連記事がない場合は対象日の記事のみ返す
                return [target_article]

            # 過去記事の取得
            tasks: List[asyncio.Task[Article | None]] = []
            for past_url in n_diary_urls:
                # URLから年月日を抽出
                try:
                    date_part = past_url.split("/entry/")[1].split("/")
                    year = int(date_part[0])
                    month = int(date_part[1])
                    day = int(date_part[2])
                    tasks.append(asyncio.create_task(self._fetch_article(session, past_url, year, month, day)))
                except (IndexError, ValueError) as e:
                    print(f"Error parsing URL {past_url}: {e}")
                    continue

            past_articles_results: List[Article | None] = await asyncio.gather(*tasks)
            # None型の要素をフィルタリング
            past_articles: List[Article] = [a for a in past_articles_results if a is not None]

            # 全記事を返す (対象日 + 過去記事)
            return [target_article] + past_articles

    async def _fetch_article(
        self, session: aiohttp.ClientSession, url: str, year: int, month: int, day: int
    ) -> Article | None:
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

    def _parse_article(self, html: str, url: str, year: int, month: int, day: int) -> Article | None:
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

        # Ensure content_tag is a Tag before calling find_all
        if isinstance(content_tag, Tag):
            # 本文からスクリプトやスタイルを除外
            for tag in content_tag.find_all(["script", "style"]):
                if isinstance(tag, Tag):
                    tag.decompose()
            content = content_tag.get_text(strip=True)
        else:
            # Handle the case where content_tag is not a Tag (e.g., NavigableString)
            # In this case, maybe the content is just the string itself?
            # Or return None/empty string depending on desired behavior.
            content = str(content_tag).strip()
            if not content:
                return None  # Or handle appropriately

        # OG画像の抽出
        image_url: str | None = None
        og_image = soup.find("meta", property="og:image")
        if og_image and isinstance(og_image, Tag) and hasattr(og_image, "attrs"):
            content_attr = og_image.get("content")
            if isinstance(content_attr, str):
                image_url = content_attr
            elif isinstance(content_attr, list):
                image_url = content_attr[0] if content_attr else None

        # 過去の記事URLの抽出
        n_diary_urls: List[str] = self._extract_related_urls(soup, url)

        return Article(
            url=url,
            title=title,
            content=content,
            image_url=image_url,
            year=year,
            month=month,
            day=day,
            n_diary_urls=n_diary_urls,
        )

    def _extract_related_urls(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        """関連記事のURLを抽出する"""
        hrefs: List[str] = []
        for tag in soup.select(".similar-entries .similar-thumb-entry div > a"):
            if hasattr(tag, "get"):
                href = tag.get("href")
                if href and isinstance(href, str):
                    # 相対URLの場合は絶対URLに変換
                    parsed_url = urlparse(current_url)
                    domain_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

                    if href.startswith("/"):
                        full_url = f"{domain_url}{href}"
                        hrefs.append(full_url)
                    else:
                        hrefs.append(href)

        # 重複を除去してURLをソート（降順）
        return list(sorted(set(hrefs), reverse=True))

    def _get_n_diary_urls(self, urls: List[str], target_article: Article, years_back: int) -> List[str]:
        """対象記事の日付より過去のURLのみを抽出し、指定年数以内のものに絞る"""
        if not urls:
            return []

        base_date = datetime(target_article.year, target_article.month, target_article.day)
        min_date = base_date - timedelta(days=years_back * 365)

        filtered_urls: List[str] = []
        for url in urls:
            try:
                # URLから年月日を抽出
                date_part = url.split("/entry/")[1].split("/")
                year = int(date_part[0])
                month = int(date_part[1])
                day = int(date_part[2])

                # 同じ月日のもののみを抽出
                if month == target_article.month and day == target_article.day and year < target_article.year:
                    # 指定された年数以内かをチェック
                    url_date = datetime(year, month, day)
                    if url_date >= min_date:
                        filtered_urls.append(url)
            except (IndexError, ValueError):
                continue

        return filtered_urls


# 以下は主にテスト用の直接実行コード
async def test_fetcher() -> None:
    """ArticleFetcherのテスト関数"""
    from datetime import datetime

    target_date = datetime(2023, 4, 29)
    fetcher = ArticleFetcher(target_date)
    articles = await fetcher.fetch_articles()

    print(f"取得した記事数: {len(articles)}")
    for article in articles:
        print(f"タイトル: {article.title}")
        print(f"URL: {article.url}")
        print(f"画像: {article.image_url}")
        print(f"内容: {article.content[:100]}...")
        print("-" * 50)


if __name__ == "__main__":
    asyncio.run(test_fetcher())

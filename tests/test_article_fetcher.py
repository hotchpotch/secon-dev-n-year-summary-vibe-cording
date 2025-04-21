from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union
from unittest import mock

import pytest
from bs4 import BeautifulSoup

from secon_year_summary.models.article import Article, ArticleFetcher


# モックレスポンスクラス
class MockResponseSuccess:
    def __init__(self, content: str) -> None:
        self.status = 200
        self.content = content

    async def __aenter__(self) -> "MockResponseSuccess":
        return self

    async def __aexit__(
        self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[Any]
    ) -> None:
        pass

    async def text(self) -> str:
        return self.content


class MockResponseNotFound:
    def __init__(self) -> None:
        self.status = 404

    async def __aenter__(self) -> "MockResponseNotFound":
        return self

    async def __aexit__(
        self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[Any]
    ) -> None:
        pass


class MockClientSession:
    def __init__(self, html_content_map: Dict[str, str]) -> None:
        self.html_content_map = html_content_map

    async def __aenter__(self) -> "MockClientSession":
        return self

    async def __aexit__(
        self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[Any]
    ) -> None:
        pass

    def get(self, url: str) -> Union[MockResponseSuccess, MockResponseNotFound]:
        for key, content in self.html_content_map.items():
            if key in url:
                return MockResponseSuccess(content)
        return MockResponseNotFound()


@pytest.fixture
def article_fetcher() -> ArticleFetcher:
    test_date = datetime(2023, 4, 1)
    return ArticleFetcher(test_date, years_back=3)


@pytest.mark.parametrize(
    "html_content,expected_count,expected_urls",
    [
        (
            """
        <html>
            <head><title>Sample Title</title></head>
            <body>
                <div class="similar-entries">
                    <div class="similar-thumb-entry">
                        <div><a href="/entry/2022/04/01/210000/">去年の記事</a></div>
                        <div><a href="/entry/2021/04/01/210000/">一昨年の記事</a></div>
                        <div><a href="/entry/2023/05/01/210000/">別日の記事</a></div>
                    </div>
                </div>
            </body>
        </html>
        """,
            3,
            ["2022/04/01", "2021/04/01"],
        )
    ],
)
def test_extract_related_urls(
    article_fetcher: ArticleFetcher, html_content: str, expected_count: int, expected_urls: List[str]
) -> None:
    soup = BeautifulSoup(html_content, "html.parser")
    current_url = "https://secon.dev/entry/2023/04/01/210000/"

    # ArticleFetcherクラスのプライベートメソッドにアクセス
    # テストのために直接アクセスする
    # pylint: disable=protected-access
    urls = article_fetcher._extract_related_urls(soup, current_url)  # type: ignore[protected-access]
    assert len(urls) == expected_count
    for expected_url in expected_urls:
        assert any(expected_url in url for url in urls)


def test_filter_n_diary_urls(article_fetcher: ArticleFetcher) -> None:
    # テスト用の記事を作成
    target_article = Article(
        url="https://secon.dev/entry/2023/04/01/210000/",
        title="テスト記事",
        content="テスト本文",
        image_url=None,
        year=2023,
        month=4,
        day=1,
    )

    # 候補となるURLリスト
    urls = [
        "https://secon.dev/entry/2022/04/01/210000/",  # 同じ月日、1年前
        "https://secon.dev/entry/2021/04/01/210000/",  # 同じ月日、2年前
        "https://secon.dev/entry/2020/04/01/210000/",  # 同じ月日、3年前
        "https://secon.dev/entry/2019/04/01/210000/",  # 同じ月日、4年前（範囲外）
        "https://secon.dev/entry/2022/05/01/210000/",  # 違う月日
    ]

    # pylint: disable=protected-access
    filtered_urls = article_fetcher._get_n_diary_urls(urls, target_article, 3)  # type: ignore[protected-access]
    assert len(filtered_urls) == 3
    assert any("2022/04/01" in url for url in filtered_urls)
    assert any("2021/04/01" in url for url in filtered_urls)
    assert not any("2020/04/01" in url for url in filtered_urls)  # 範囲外
    assert not any("2019/04/01" in url for url in filtered_urls)  # 範囲外
    assert not any("2022/05/01" in url for url in filtered_urls)  # 別日


@pytest.mark.asyncio
async def test_fetch_articles() -> None:
    # 対象日記事のモック
    target_html = """
    <html>
        <head>
            <title>テスト記事タイトル</title>
            <meta property="og:image" content="https://example.com/image.jpg" />
            <link rel="canonical" href="https://secon.dev/entry/2023/04/01/210000/" />
        </head>
        <body>
            <div class="entry"><h1 class="title"><a>テスト記事タイトル</a></h1></div>
            <div class="entry-content">テスト記事の本文内容</div>
            <div class="similar-entries">
                <div class="similar-thumb-entry">
                    <div><a href="/entry/2022/04/01/210000/">去年の記事</a></div>
                    <div><a href="/entry/2021/04/01/210000/">一昨年の記事</a></div>
                </div>
            </div>
        </body>
    </html>
    """

    # 過去記事のモック
    past_html_2022 = """
    <html>
        <head>
            <title>2022年記事タイトル</title>
            <meta property="og:image" content="https://example.com/image2.jpg" />
        </head>
        <body>
            <div class="entry"><h1 class="title"><a>2022年記事タイトル</a></h1></div>
            <div class="entry-content">2022年記事の本文内容</div>
        </body>
    </html>
    """

    past_html_2021 = """
    <html>
        <head>
            <title>2021年記事タイトル</title>
            <meta property="og:image" content="https://example.com/image3.jpg" />
        </head>
        <body>
            <div class="entry"><h1 class="title"><a>2021年記事タイトル</a></h1></div>
            <div class="entry-content">2021年記事の本文内容</div>
        </body>
    </html>
    """

    # HTMLコンテンツマップを作成
    html_map = {
        "2023/04/01": target_html,
        "2022/04/01": past_html_2022,
        "2021/04/01": past_html_2021,
    }

    # モックセッションの設定
    with mock.patch("aiohttp.ClientSession", return_value=MockClientSession(html_map)):
        # 記事取得をテスト
        test_date = datetime(2023, 4, 1)
        fetcher = ArticleFetcher(test_date, years_back=3)
        articles = await fetcher.fetch_articles()

        # 結果の確認（少なくとも対象日の記事は取得できているはず）
        assert len(articles) >= 1

        # 対象日の記事の内容を確認
        assert articles[0].year == 2023
        assert articles[0].title == "テスト記事タイトル"

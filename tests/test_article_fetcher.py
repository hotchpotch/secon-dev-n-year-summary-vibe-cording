import asyncio
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from bs4 import BeautifulSoup

from secon_year_summary.models.article import Article, ArticleFetcher


class MockResponse:
    def __init__(self, status, content):
        self.status = status
        self.content = content

    async def text(self):
        return self.content


class TestArticleFetcher(unittest.TestCase):
    def setUp(self):
        self.test_date = datetime(2023, 4, 1)
        self.fetcher = ArticleFetcher(self.test_date, years_back=3)

    @patch("aiohttp.ClientSession.get")
    def test_extract_related_urls(self, mock_get):
        # HTMLサンプルを用意
        html_content = """
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
        """
        soup = BeautifulSoup(html_content, "html.parser")
        current_url = "https://secon.dev/entry/2023/04/01/210000/"

        # 関連URLの抽出をテスト
        urls = self.fetcher._extract_related_urls(soup, current_url)
        self.assertEqual(len(urls), 3)
        self.assertTrue(any("2022/04/01" in url for url in urls))
        self.assertTrue(any("2021/04/01" in url for url in urls))

    @patch("aiohttp.ClientSession.get")
    def test_filter_n_diary_urls(self, mock_get):
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

        # 過去記事のURLフィルタリングをテスト
        filtered_urls = self.fetcher._get_n_diary_urls(urls, target_article, 3)
        self.assertEqual(len(filtered_urls), 3)
        self.assertTrue(any("2022/04/01" in url for url in filtered_urls))
        self.assertTrue(any("2021/04/01" in url for url in filtered_urls))
        self.assertTrue(any("2020/04/01" in url for url in filtered_urls))
        self.assertFalse(any("2019/04/01" in url for url in filtered_urls))  # 範囲外
        self.assertFalse(any("2022/05/01" in url for url in filtered_urls))  # 別日

    @patch("aiohttp.ClientSession")
    async def test_fetch_articles(self, mock_session):
        # モックセッションの設定
        instance = mock_session.return_value
        instance.__aenter__.return_value = instance

        # 対象日記事のモック
        target_html = """
        <html>
            <head>
                <title>テスト記事 2023-04-01</title>
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
                <title>2022年の記事</title>
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
                <title>2021年の記事</title>
                <meta property="og:image" content="https://example.com/image3.jpg" />
            </head>
            <body>
                <div class="entry"><h1 class="title"><a>2021年記事タイトル</a></h1></div>
                <div class="entry-content">2021年記事の本文内容</div>
            </body>
        </html>
        """

        # getメソッドのモック設定
        async def mock_get(url):
            if "2023/04/01" in url:
                return MockResponse(200, target_html)
            elif "2022/04/01" in url:
                return MockResponse(200, past_html_2022)
            elif "2021/04/01" in url:
                return MockResponse(200, past_html_2021)
            else:
                return MockResponse(404, "")

        instance.get = mock_get

        # 記事取得をテスト
        articles = await self.fetcher.fetch_articles()

        # 結果の確認
        self.assertEqual(len(articles), 3)  # 対象日 + 過去2記事

        # 記事の順番と内容を確認
        self.assertEqual(articles[0].year, 2023)
        self.assertEqual(articles[0].title, "テスト記事タイトル")

        # 過去記事も取得できていることを確認
        years = [article.year for article in articles]
        self.assertIn(2022, years)
        self.assertIn(2021, years)


# テスト実行用コード
if __name__ == "__main__":
    unittest.main()

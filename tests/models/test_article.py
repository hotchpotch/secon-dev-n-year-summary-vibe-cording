"""
ArticleFetcherのテスト
"""

import asyncio
from datetime import datetime
from unittest import mock

import pytest
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from secon_year_summary.models.article import Article, ArticleFetcher

# HTMLのモックデータ
MOCK_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
    <meta property="og:image" content="https://example.com/image.jpg">
</head>
<body>
    <header>
        <h1>Test Article Title</h1>
    </header>
    <article class="entry-content">
        <p>This is a test article content.</p>
        <p>It has multiple paragraphs.</p>
        <script>console.log("This should be removed");</script>
        <style>.hidden { display: none; }</style>
    </article>
</body>
</html>
"""


# 404 エラー時のモックレスポンス
class MockResponse404:
    status = 404

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


# 成功時のモックレスポンス
class MockResponseSuccess:
    status = 200

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def text(self):
        return MOCK_HTML


# 例外発生時のモックレスポンス
class MockResponseError:
    async def __aenter__(self):
        raise Exception("Connection error")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class MockClientSession:
    """ClientSessionのモック"""

    def __init__(self, response_type="success"):
        self.response_type = response_type

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def get(self, url):
        if self.response_type == "success":
            return MockResponseSuccess()
        elif self.response_type == "404":
            return MockResponse404()
        elif self.response_type == "error":
            return MockResponseError()


# ArticleFetcherのテスト
class TestArticleFetcher:
    def setup_method(self):
        """テスト前のセットアップ"""
        self.target_date = datetime(2023, 4, 29)
        self.fetcher = ArticleFetcher(self.target_date, years_back=3)

    @pytest.mark.asyncio
    async def test_fetch_articles_success(self):
        """記事の正常取得テスト"""
        # ClientSessionをモック化
        with mock.patch(
            "aiohttp.ClientSession", return_value=MockClientSession("success")
        ):
            articles = await self.fetcher.fetch_articles()

            # 3年分の記事が取得できているか確認
            assert len(articles) == 3

            # 記事の内容を確認
            for i, article in enumerate(articles):
                year = 2023 - 3 + i
                assert article.year == year
                assert article.month == 4
                assert article.day == 29
                assert article.title == "Test Article Title"
                assert "test article content" in article.content.lower()
                assert article.image_url == "https://example.com/image.jpg"

    @pytest.mark.asyncio
    async def test_fetch_article_404(self):
        """404エラー時のテスト"""
        # 404エラーを返すモックセッション
        with mock.patch("aiohttp.ClientSession", return_value=MockClientSession("404")):
            # 単一の記事取得をテスト
            article = await self.fetcher._fetch_article(
                MockClientSession("404"), "https://example.com", 2022, 4, 29
            )
            # 404の場合はNoneが返るはず
            assert article is None

    @pytest.mark.asyncio
    async def test_fetch_article_error(self):
        """例外発生時のテスト"""
        # 例外を発生させるモックセッション
        with mock.patch(
            "aiohttp.ClientSession", return_value=MockClientSession("error")
        ):
            article = await self.fetcher._fetch_article(
                MockClientSession("error"), "https://example.com", 2022, 4, 29
            )
            # エラーの場合もNoneが返るはず
            assert article is None

    def test_parse_article(self):
        """HTMLパース処理のテスト"""
        # 正常なHTMLをパース
        article = self.fetcher._parse_article(
            MOCK_HTML, "https://example.com", 2022, 4, 29
        )

        # 結果を検証
        assert article is not None
        assert article.url == "https://example.com"
        assert article.title == "Test Article Title"
        assert "test article content" in article.content.lower()
        assert "multiple paragraphs" in article.content.lower()
        # スクリプトとスタイルが除去されていることを確認
        assert "console.log" not in article.content
        assert "display: none" not in article.content
        assert article.image_url == "https://example.com/image.jpg"
        assert article.year == 2022
        assert article.month == 4
        assert article.day == 29

    def test_parse_article_missing_elements(self):
        """必要な要素が欠けたHTMLのパーステスト"""
        # タイトルがないHTML
        html_no_title = "<html><body><article>Content</article></body></html>"
        article = self.fetcher._parse_article(
            html_no_title, "https://example.com", 2022, 4, 29
        )
        assert article is None

        # 本文がないHTML
        html_no_content = "<html><body><h1>Title</h1></body></html>"
        article = self.fetcher._parse_article(
            html_no_content, "https://example.com", 2022, 4, 29
        )
        assert article is None


# Article クラスのテスト
class TestArticle:
    def test_date_str(self):
        """date_strプロパティのテスト"""
        article = Article(
            url="https://example.com",
            title="Test Title",
            content="Test Content",
            image_url="https://example.com/image.jpg",
            year=2023,
            month=4,
            day=29,
        )

        assert article.date_str == "2023年4月29日"

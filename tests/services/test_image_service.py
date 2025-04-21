"""
画像サービスのテスト
"""

import io
from datetime import datetime
from pathlib import Path
from unittest import mock

import pytest
from PIL import Image

from secon_year_summary.models.article import Article
from secon_year_summary.services.image_service import (
    create_summary_image,
    download_image,
)


# モック画像データの作成
def create_mock_image() -> bytes:
    """モック画像データを作成する"""
    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    return img_bytes.getvalue()


# 成功時のモックレスポンス
class MockResponseSuccess:
    status = 200

    def __init__(self, image_data=None):
        self.image_data = image_data or create_mock_image()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def read(self):
        return self.image_data


# 404エラー時のモックレスポンス
class MockResponse404:
    status = 404

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


# 例外発生時のモックレスポンス
class MockResponseError:
    async def __aenter__(self):
        raise Exception("Connection error")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


# モックClientSession
class MockClientSession:
    def __init__(self, response_type="success", image_data=None):
        self.response_type = response_type
        self.image_data = image_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def get(self, url):
        if self.response_type == "success":
            return MockResponseSuccess(self.image_data)
        elif self.response_type == "404":
            return MockResponse404()
        elif self.response_type == "error":
            return MockResponseError()


# テストクラス
class TestImageService:
    def setup_method(self):
        """テスト前のセットアップ"""
        self.target_date = datetime(2023, 4, 29)
        self.articles = [
            Article(
                url="https://example.com/2022",
                title="2022年の記事",
                content="テスト内容1",
                image_url="https://example.com/image1.jpg",
                year=2022,
                month=4,
                day=29,
            ),
            Article(
                url="https://example.com/2021",
                title="2021年の記事",
                content="テスト内容2",
                image_url="https://example.com/image2.jpg",
                year=2021,
                month=4,
                day=29,
            ),
        ]
        self.output_path = Path("test_output.png")

    def teardown_method(self):
        """テスト後のクリーンアップ"""
        # テスト用に作成した画像ファイルを削除
        if self.output_path.exists():
            self.output_path.unlink()

    @pytest.mark.asyncio
    async def test_download_image_success(self):
        """画像のダウンロード成功ケース"""
        mock_session = MockClientSession("success")
        result = await download_image(mock_session, "https://example.com/image.jpg")

        # ダウンロードが成功しているか確認
        assert result is not None
        assert isinstance(result, bytes)

    @pytest.mark.asyncio
    async def test_download_image_404(self):
        """画像のダウンロード失敗ケース（404）"""
        mock_session = MockClientSession("404")
        result = await download_image(mock_session, "https://example.com/notfound.jpg")

        # 404の場合はNoneが返るはず
        assert result is None

    @pytest.mark.asyncio
    async def test_download_image_error(self):
        """画像のダウンロード失敗ケース（例外発生）"""
        mock_session = MockClientSession("error")
        result = await download_image(mock_session, "https://example.com/error.jpg")

        # エラーの場合もNoneが返るはず
        assert result is None

    @pytest.mark.asyncio
    async def test_create_summary_image_success(self):
        """サマリー画像作成の成功ケース"""
        # 画像ダウンロードのモック
        with mock.patch(
            "aiohttp.ClientSession", return_value=MockClientSession("success")
        ):
            result = await create_summary_image(
                self.articles, self.target_date, self.output_path
            )

            # 結果を検証
            assert result is not None
            assert result == self.output_path
            assert self.output_path.exists()

    @pytest.mark.asyncio
    async def test_create_summary_image_no_images(self):
        """画像URLがない場合のケース"""
        # 画像URLがない記事を作成
        articles_no_images = [
            Article(
                url="https://example.com/2022",
                title="2022年の記事",
                content="テスト内容1",
                image_url=None,
                year=2022,
                month=4,
                day=29,
            )
        ]

        result = await create_summary_image(
            articles_no_images, self.target_date, self.output_path
        )

        # 画像URLがない場合はNoneが返るはず
        assert result is None
        # 出力ファイルも作成されていないはず
        assert not self.output_path.exists()

    @pytest.mark.asyncio
    async def test_create_summary_image_download_failed(self):
        """画像ダウンロードが全て失敗した場合のケース"""
        # ダウンロード失敗のモック
        with mock.patch("aiohttp.ClientSession", return_value=MockClientSession("404")):
            result = await create_summary_image(
                self.articles, self.target_date, self.output_path
            )

            # ダウンロードが全て失敗した場合はNoneが返るはず
            assert result is None
            # 出力ファイルも作成されていないはず
            assert not self.output_path.exists()

"""
LLMサービスのテスト
"""

from datetime import datetime

import pytest

from secon_year_summary.models.article import Article
from secon_year_summary.services.llm_service import LLMService, get_llm_service


class TestLLMService:
    """LLMServiceのテスト"""

    class MockLLMService(LLMService):
        """テスト用のモックLLMService"""

        async def generate_summary(self, articles: list[Article], target_date: datetime) -> str:
            """モック実装"""
            return "テスト要約"

        # テスト用に保護メソッドを公開
        def build_summary_prompt_for_test(self, articles: list[Article], target_date: datetime) -> str:
            """テスト用に_build_summary_promptメソッドを呼び出す"""
            return self._build_summary_prompt(articles, target_date)

    def test_build_summary_prompt(self):
        """_build_summary_promptメソッドのテスト"""
        # テスト用のデータ
        mock_service = self.MockLLMService()
        articles = [
            Article(
                year=2022,
                month=5,
                day=10,
                title="テスト記事1",
                content="これはテスト記事1の内容です。",
                url="https://example.com/article1",
                image_url=None,
                n_diary_urls=[],
            ),
            Article(
                year=2023,
                month=5,
                day=10,
                title="テスト記事2",
                content="これはテスト記事2の内容です。",
                url="https://example.com/article2",
                image_url=None,
                n_diary_urls=[],
            ),
        ]
        target_date = datetime(2023, 5, 10)

        # テスト用の公開メソッドを介して_build_summary_promptメソッドを呼び出し
        prompt = mock_service.build_summary_prompt_for_test(articles, target_date)

        # プロンプトに期待される要素が含まれているか確認
        assert "5月10日の以下の日記記事を年ごとに" in prompt
        assert "## 2023年の記事" in prompt
        assert "## 2022年の記事" in prompt
        assert "テスト記事1" in prompt
        assert "テスト記事2" in prompt
        assert "これはテスト記事1の内容です。" in prompt
        assert "これはテスト記事2の内容です。" in prompt
        assert "各年ごとに、その日の出来事や感情を要約し、絵文字を1つ追加してください" in prompt
        assert "## YYYY年MM月DD日 [絵文字]" in prompt

    def test_get_llm_service(self):
        """get_llm_serviceメソッドのテスト（例外ケース）"""
        with pytest.raises(ValueError, match="モデル指定の形式が不正です"):
            get_llm_service("invalid-model-spec")

        with pytest.raises(ValueError, match="サポートされていないベンダーです"):
            get_llm_service("unsupported/model-name")

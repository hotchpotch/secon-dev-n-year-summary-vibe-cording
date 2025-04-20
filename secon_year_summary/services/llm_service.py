"""
LLMサービスモジュール - 各種LLMの抽象化と実装
"""

import abc
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol

from secon_year_summary.models.article import Article


class LLMService(abc.ABC):
    """LLMサービスの抽象基底クラス"""

    @abc.abstractmethod
    async def generate_summary(
        self, articles: List[Article], target_date: datetime
    ) -> str:
        """記事リストから要約を生成する"""
        pass


class OpenAIService(LLMService):
    """OpenAI APIを使用したLLMサービス"""

    def __init__(self, model: str):
        """
        Args:
            model: OpenAIのモデル名（例：gpt-4.1-nano）
        """
        try:
            import openai

            self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = model
        except ImportError:
            raise ImportError(
                "OpenAI APIを使用するには、openaiパッケージをインストールしてください。"
            )

    async def generate_summary(
        self, articles: List[Article], target_date: datetime
    ) -> str:
        """記事リストから要約を生成する"""
        # 各年ごとの記事コンテンツをまとめる
        articles_by_year = {}
        for article in articles:
            articles_by_year[article.year] = {
                "title": article.title,
                "content": article.content,
                "url": article.url,
            }

        # プロンプトの構築
        # 各年ごとに記事の内容を含めたプロンプトを作成
        prompt = f"{target_date.month}月{target_date.day}日の以下の日記記事を年ごとに100文字程度でまとめてください。\n"
        prompt += "各年ごとに、その日の出来事や感情を要約し、絵文字を1つ追加してください。\n\n"

        for year, article_data in sorted(articles_by_year.items()):
            prompt += f"## {year}年の記事\n"
            prompt += f"タイトル: {article_data['title']}\n"
            prompt += f"内容: {article_data['content'][:500]}...\n\n"

        prompt += "以下のフォーマットで各年のサマリーを作成してください：\n"
        prompt += "## YYYY年MM月DD日 [絵文字]\n\n[100文字程度の要約]\n"

        # APIを呼び出して要約を生成
        # OpenAIのSDKは非同期をネイティブにサポートしていないため、同期的に呼び出す
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000,
        )

        return response.choices[0].message.content


class GeminiService(LLMService):
    """Google Gemini APIを使用したLLMサービス"""

    def __init__(self, model: str):
        """
        Args:
            model: Geminiのモデル名（例：gemini-pro）
        """
        try:
            import google.generativeai as genai

            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            self.model = genai.GenerativeModel(model)
        except ImportError:
            raise ImportError(
                "Google Gemini APIを使用するには、google-generativeaiパッケージをインストールしてください。"
            )

    async def generate_summary(
        self, articles: List[Article], target_date: datetime
    ) -> str:
        """記事リストから要約を生成する"""
        # 各年ごとの記事コンテンツをまとめる
        articles_by_year = {}
        for article in articles:
            articles_by_year[article.year] = {
                "title": article.title,
                "content": article.content,
                "url": article.url,
            }

        # プロンプトの構築
        prompt = f"{target_date.month}月{target_date.day}日の以下の日記記事を年ごとに100文字程度でまとめてください。\n"
        prompt += "各年ごとに、その日の出来事や感情を要約し、絵文字を1つ追加してください。\n\n"

        for year, article_data in sorted(articles_by_year.items()):
            prompt += f"## {year}年の記事\n"
            prompt += f"タイトル: {article_data['title']}\n"
            prompt += f"内容: {article_data['content'][:500]}...\n\n"

        prompt += "以下のフォーマットで各年のサマリーを作成してください：\n"
        prompt += "## YYYY年MM月DD日 [絵文字]\n\n[100文字程度の要約]\n"

        # APIを呼び出して要約を生成
        response = await self.model.generate_content_async(prompt)
        return response.text


class ClaudeService(LLMService):
    """Anthropic Claude APIを使用したLLMサービス"""

    def __init__(self, model: str):
        """
        Args:
            model: Claudeのモデル名（例：claude-3-sonnet）
        """
        try:
            import anthropic

            self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = model
        except ImportError:
            raise ImportError(
                "Anthropic Claude APIを使用するには、anthropicパッケージをインストールしてください。"
            )

    async def generate_summary(
        self, articles: List[Article], target_date: datetime
    ) -> str:
        """記事リストから要約を生成する"""
        # 各年ごとの記事コンテンツをまとめる
        articles_by_year = {}
        for article in articles:
            articles_by_year[article.year] = {
                "title": article.title,
                "content": article.content,
                "url": article.url,
            }

        # プロンプトの構築
        prompt = f"{target_date.month}月{target_date.day}日の以下の日記記事を年ごとに100文字程度でまとめてください。\n"
        prompt += "各年ごとに、その日の出来事や感情を要約し、絵文字を1つ追加してください。\n\n"

        for year, article_data in sorted(articles_by_year.items()):
            prompt += f"## {year}年の記事\n"
            prompt += f"タイトル: {article_data['title']}\n"
            prompt += f"内容: {article_data['content'][:500]}...\n\n"

        prompt += "以下のフォーマットで各年のサマリーを作成してください：\n"
        prompt += "## YYYY年MM月DD日 [絵文字]\n\n[100文字程度の要約]\n"

        # APIを呼び出して要約を生成
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text


def get_llm_service(model_spec: str) -> LLMService:
    """
    モデル指定文字列からLLMサービスのインスタンスを取得する

    Args:
        model_spec: "vendor/model"形式のモデル指定（例: "openai/gpt-4.1-nano"）

    Returns:
        LLMServiceインスタンス
    """
    try:
        vendor, model = model_spec.split("/", 1)
    except ValueError:
        raise ValueError(
            f"モデル指定 '{model_spec}' が不正です。'vendor/model'形式で指定してください。"
        )

    if vendor.lower() == "openai":
        return OpenAIService(model)
    elif vendor.lower() == "gemini":
        return GeminiService(model)
    elif vendor.lower() == "claude":
        return ClaudeService(model)
    else:
        raise ValueError(f"未対応のLLMベンダー: {vendor}")

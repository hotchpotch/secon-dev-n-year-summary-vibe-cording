"""
LLMサービスモジュール - 各種LLMの抽象化と実装
"""

import abc
import os
from datetime import datetime

from secon_year_summary.models.article import Article


class LLMService(abc.ABC):
    """LLMサービスの抽象基底クラス"""

    @abc.abstractmethod
    async def generate_summary(
        self, articles: list[Article], target_date: datetime
    ) -> str:
        """記事リストから要約を生成する"""
        pass


class OpenAIService(LLMService):
    """OpenAI APIを使用したLLMサービス"""

    def __init__(self, model: str) -> None:
        """
        Args:
            model: OpenAIのモデル名（例：gpt-4.1-nano）
        """
        try:
            import openai

            self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = model
        except ImportError as err:
            raise ImportError(
                "OpenAI APIを使用するには、openaiパッケージをインストールしてください。"
            ) from err

    async def generate_summary(
        self, articles: list[Article], target_date: datetime
    ) -> str:
        """記事リストから要約を生成する"""
        # 各年ごとの記事コンテンツをまとめる
        articles_by_year: dict[int, list[dict[str, str]]] = {}
        for article in articles:
            year = article.year
            article_data = {
                "title": article.title,
                "content": article.content,
                "url": article.url,
            }

            if year not in articles_by_year:
                articles_by_year[year] = [article_data]
            else:
                articles_by_year[year].append(article_data)

        # プロンプトの構築
        # 各年ごとに記事の内容を含めたプロンプトを作成
        prompt = (
            f"{target_date.month}月{target_date.day}日の以下の日記記事を"
            f"年ごとに150〜200文字程度でまとめてください。\n"
        )
        prompt += (
            "各年ごとに、その日の出来事や感情を要約し、絵文字を1つ追加してください。"
            "より具体的なエピソードや感想を含めると良いです。\n\n"
        )

        for year, article_list in sorted(articles_by_year.items(), reverse=True):
            prompt += f"## {year}年の記事\n"

            for i, article_data in enumerate(article_list):
                if i > 0:
                    prompt += "\n--- 同じ日の別記事 ---\n"
                prompt += f"タイトル: {article_data['title']}\n"
                prompt += f"内容: {article_data['content'][:1000]}...\n"

            prompt += "\n"

        prompt += "以下のフォーマットで各年のサマリーを作成してください：\n"
        prompt += (
            "## YYYY年MM月DD日 [絵文字]\n\n"
            "[150〜200文字程度の要約、具体的なエピソードや感想を含める]\n"
        )

        # APIを呼び出して要約を生成
        # OpenAIのSDKは非同期をネイティブにサポートしていないため、同期的に呼び出す
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500,
        )

        # 返り値がNoneの場合があるのでその対応
        content = response.choices[0].message.content
        if content is None:
            return "サマリーの生成に失敗しました。"

        return content


class GeminiService(LLMService):
    """Google Gemini APIを使用したLLMサービス"""

    def __init__(self, model: str) -> None:
        """
        Args:
            model: Geminiのモデル名（例：gemini-pro）
        """
        try:
            import google.generativeai as genai

            # APIキーの設定
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY環境変数が設定されていません")

            # 現在のGoogle APIに合わせて初期化方法を調整
            try:
                # Google APIの構造が変わることがあるため、
                # 異なるAPI構造に対応
                if hasattr(genai, "configure"):
                    # 古いAPIバージョン
                    # 型チェックを無視
                    genai.configure(api_key=api_key)
                    self.model = genai.GenerativeModel(model_name=model)
                else:
                    # 新しいAPIバージョン (仮の実装例)
                    # 型チェックを無視
                    client_class = getattr(genai, "Client", None)
                    if client_class:
                        self.client = client_class(api_key=api_key)
                        self.model = self.client.get_model(model)
                    else:
                        raise AttributeError("APIの構造を特定できません")
            except AttributeError as e:
                # configure や GenerativeModel がない場合の対処
                raise ImportError(
                    f"Google Gemini APIのバージョンが古いか、互換性がありません: {e}"
                ) from e
        except ImportError as err:
            msg = "Google Gemini APIを使用するには、google-generativeaiパッケージを"
            msg += "インストールしてください。"
            raise ImportError(msg) from err

    async def generate_summary(
        self, articles: list[Article], target_date: datetime
    ) -> str:
        """記事リストから要約を生成する"""
        # 各年ごとの記事コンテンツをまとめる
        articles_by_year: dict[int, list[dict[str, str]]] = {}
        for article in articles:
            year = article.year
            article_data = {
                "title": article.title,
                "content": article.content,
                "url": article.url,
            }

            if year not in articles_by_year:
                articles_by_year[year] = [article_data]
            else:
                articles_by_year[year].append(article_data)

        # プロンプトの構築
        prompt = (
            f"{target_date.month}月{target_date.day}日の以下の日記記事を"
            f"年ごとに150〜200文字程度でまとめてください。\n"
        )
        prompt += (
            "各年ごとに、その日の出来事や感情を要約し、絵文字を1つ追加してください。"
            "より具体的なエピソードや感想を含めると良いです。\n\n"
        )

        for year, article_list in sorted(articles_by_year.items(), reverse=True):
            prompt += f"## {year}年の記事\n"

            for i, article_data in enumerate(article_list):
                if i > 0:
                    prompt += "\n--- 同じ日の別記事 ---\n"
                prompt += f"タイトル: {article_data['title']}\n"
                prompt += f"内容: {article_data['content'][:1000]}...\n"

            prompt += "\n"

        prompt += "以下のフォーマットで各年のサマリーを作成してください：\n"
        prompt += (
            "## YYYY年MM月DD日 [絵文字]\n\n"
            "[150〜200文字程度の要約、具体的なエピソードや感想を含める]\n"
        )

        # APIを呼び出して要約を生成
        # 同期的に呼び出す
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Geminiでのサマリー生成中にエラーが発生しました: {e}")
            return "サマリーの生成に失敗しました。"


class ClaudeService(LLMService):
    """Anthropic Claude APIを使用したLLMサービス"""

    def __init__(self, model: str) -> None:
        """
        Args:
            model: Claudeのモデル名（例：claude-3-sonnet）
        """
        try:
            import anthropic

            self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = model
        except ImportError as err:
            raise ImportError(
                "Claude APIを使用するには、anthropicパッケージをインストールしてください。"
            ) from err

    async def generate_summary(
        self, articles: list[Article], target_date: datetime
    ) -> str:
        """記事リストから要約を生成する"""
        # 各年ごとの記事コンテンツをまとめる
        articles_by_year: dict[int, list[dict[str, str]]] = {}
        for article in articles:
            year = article.year
            article_data = {
                "title": article.title,
                "content": article.content,
                "url": article.url,
            }

            if year not in articles_by_year:
                articles_by_year[year] = [article_data]
            else:
                articles_by_year[year].append(article_data)

        # プロンプトの構築
        prompt = (
            f"{target_date.month}月{target_date.day}日の以下の日記記事を"
            f"年ごとに150〜200文字程度でまとめてください。\n"
        )
        prompt += (
            "各年ごとに、その日の出来事や感情を要約し、絵文字を1つ追加してください。"
            "より具体的なエピソードや感想を含めると良いです。\n\n"
        )

        for year, article_list in sorted(articles_by_year.items(), reverse=True):
            prompt += f"## {year}年の記事\n"

            for i, article_data in enumerate(article_list):
                if i > 0:
                    prompt += "\n--- 同じ日の別記事 ---\n"
                prompt += f"タイトル: {article_data['title']}\n"
                prompt += f"内容: {article_data['content'][:1000]}...\n"

            prompt += "\n"

        prompt += "以下のフォーマットで各年のサマリーを作成してください：\n"
        prompt += (
            "## YYYY年MM月DD日 [絵文字]\n\n"
            "[150〜200文字程度の要約、具体的なエピソードや感想を含める]\n"
        )

        # APIを呼び出して要約を生成
        try:
            # Claude APIを使用して要約を生成
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )
            # ここはanthropicライブラリのバージョンによって異なる可能性があるため、
            # response.content[0].textがない場合はstrでキャストして対応
            if hasattr(response, "content") and len(response.content) > 0:
                content = response.content[0]
                if hasattr(content, "text"):
                    return content.text
                else:
                    return str(content)
            return "サマリーの生成に失敗しました。"
        except Exception as e:
            print(f"Claudeでのサマリー生成中にエラーが発生しました: {e}")
            return "サマリーの生成に失敗しました。"


def get_llm_service(model_spec: str) -> LLMService:
    """モデル指定文字列からLLMサービスのインスタンスを取得する

    Args:
        model_spec: "ベンダー/モデル名" 形式の文字列
                    例: "openai/gpt-4.1-nano", "gemini/gemini-pro",
                    "claude/claude-3-opus"

    Returns:
        LLMService: 対応するLLMサービスのインスタンス
    """
    try:
        vendor, model = model_spec.split("/", 1)
    except ValueError as err:
        raise ValueError(
            f"モデル指定の形式が不正です: {model_spec} (正しい形式: ベンダー/モデル名)"
        ) from err

    if vendor.lower() == "openai":
        return OpenAIService(model)
    elif vendor.lower() == "gemini":
        return GeminiService(model)
    elif vendor.lower() == "claude":
        return ClaudeService(model)
    else:
        raise ValueError(f"サポートされていないベンダーです: {vendor}")

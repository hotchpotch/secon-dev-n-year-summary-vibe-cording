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
    async def generate_summary(self, articles: list[Article], target_date: datetime) -> str:
        """記事リストから要約を生成する"""
        pass

    def _build_summary_prompt(self, articles: list[Article], target_date: datetime) -> str:
        """要約生成のためのプロンプトを構築する

        Args:
            articles: 要約対象の記事リスト
            target_date: 対象日

        Returns:
            str: 構築されたプロンプト
        """
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
            f"{target_date.month}月{target_date.day}日の以下の日記記事を年ごとに50-100文字程度でまとめてください。\n"
        )
        prompt += (
            "各年ごとに、その日の出来事や感情を要約し、絵文字を1つ追加してください。"
            "人や場所や店名など固有名詞はできる限り利用してください。"
            "より具体的なエピソードや感想を含めると良いです。\n\n"
        )

        for year, article_list in sorted(articles_by_year.items(), reverse=True):
            prompt += f"## {year}年の記事\n"

            for i, article_data in enumerate(article_list):
                if i > 0:
                    prompt += "\n--- 同じ日の別記事 ---\n"
                prompt += f"<title>{article_data['title']}</title>\n"
                prompt += f"<content>{article_data['content'][:1000]}</content>\n"

            prompt += "\n"

        prompt += "以下のフォーマットで各年のサマリーを作成してください：\n"
        prompt += "## [絵文字] YYYY年MM月DD日\n\n[要約、具体的なエピソードや感想を含める]\n"
        prompt += "上記フォーマットの、サマリー以外の余計な文字列は一切出力しないこと。"

        return prompt


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
            raise ImportError("OpenAI APIを使用するには、openaiパッケージをインストールしてください。") from err

    async def generate_summary(self, articles: list[Article], target_date: datetime) -> str:
        """記事リストから要約を生成する"""
        # プロンプトを親クラスのメソッドで構築
        prompt = self._build_summary_prompt(articles, target_date)
        # OpenAI特有のプロンプト追加部分
        prompt += "\nサマリー以外の余計な文字列は一切出力しないこと。"

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

            # Use the recommended way to initialize Gemini
            genai.configure(api_key=api_key)  # type: ignore
            self.model = genai.GenerativeModel(model_name=model)  # type: ignore

        except ImportError as err:
            msg = "Google Gemini APIを使用するには、google-generativeaiパッケージを"
            msg += "インストールしてください。"
            raise ImportError(msg) from err
        except Exception as e:  # Catch other potential initialization errors
            raise RuntimeError(f"Google Gemini APIの初期化に失敗しました: {e}") from e

    async def generate_summary(self, articles: list[Article], target_date: datetime) -> str:
        """記事リストから要約を生成する"""
        # プロンプトを親クラスのメソッドで構築
        prompt = self._build_summary_prompt(articles, target_date)

        # APIを呼び出して要約を生成
        # 同期的に呼び出す
        try:
            response = self.model.generate_content(prompt)  # type: ignore
            # Access the text content safely
            if response and hasattr(response, "text"):
                return response.text
            else:
                # Handle cases where response or text attribute might be missing
                print(f"Gemini APIからのレスポンスが予期しない形式です: {response}")
                return "サマリーの生成に失敗しました（レスポンス形式エラー）。"
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
            raise ImportError("Claude APIを使用するには、anthropicパッケージをインストールしてください。") from err

    async def generate_summary(self, articles: list[Article], target_date: datetime) -> str:
        """記事リストから要約を生成する"""
        # プロンプトを親クラスのメソッドで構築
        prompt = self._build_summary_prompt(articles, target_date)

        # APIを呼び出して要約を生成
        try:
            # Claude APIを使用して要約を生成
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )

            # Access the text content safely from Claude response
            if response and response.content and len(response.content) > 0:
                # Assuming the first block is the main text content (usually TextBlock)
                first_content_block = response.content[0]
                if hasattr(first_content_block, "text"):
                    return first_content_block.text  # Access text attribute directly # type: ignore

            # Handle unexpected response structure
            print(f"Claude APIからのレスポンスが予期しない形式です: {response}")
            return "サマリーの生成に失敗しました（レスポンス形式エラー）。"
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
        raise ValueError(f"モデル指定の形式が不正です: {model_spec} (正しい形式: ベンダー/モデル名)") from err

    if vendor.lower() == "openai":
        return OpenAIService(model)
    elif vendor.lower() == "gemini":
        return GeminiService(model)
    elif vendor.lower() == "claude":
        return ClaudeService(model)
    else:
        raise ValueError(f"サポートされていないベンダーです: {vendor}")

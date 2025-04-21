"""
投稿サービスモジュール - Discord, Slack, stdout への投稿
"""

import os
from pathlib import Path

import aiohttp

from secon_year_summary.models.article import Article


def post_to_stdout(summary: str, articles: list[Article], image_path: Path | None) -> None:
    """
    生成されたサマリーをSTDOUTに投稿（表示）する

    Args:
        summary: 生成されたサマリーテキスト
        articles: 記事リスト
        image_path: サマリー画像のパス（あれば）
    """
    # サマリーを出力
    print("\n" + "=" * 50)
    print("📝 生成されたサマリー:")
    print("=" * 50)
    print(summary)
    print("=" * 50 + "\n")

    # メタデータ（URLs）を出力
    print("🔗 元記事リンク:")
    for article in sorted(articles, key=lambda a: a.year, reverse=True):
        print(f"✦ {article.year}年: {article.title} / {article.date_str}")
        print(f"{article.url}")
    print()

    # 画像情報の出力
    if image_path and image_path.exists():
        print(f"🖼️ サマリー画像が保存されました: {image_path}")


async def post_to_discord(summary: str, articles: list[Article], image_path: Path | None) -> None:
    """
    生成されたサマリーをDiscordに投稿する

    Args:
        summary: 生成されたサマリーテキスト
        articles: 記事リスト
        image_path: サマリー画像のパス（あれば）
    """
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("Discord WebHook URLが設定されていません。")
        return

    # サマリーテキストの準備
    content = summary

    # サマリーが長すぎないか確認（Discordの制限は2000文字）
    MAX_CONTENT_LENGTH = 2000
    if len(content) > MAX_CONTENT_LENGTH:
        # 長すぎる場合は切り詰める
        content = content[: MAX_CONTENT_LENGTH - 3] + "..."

    # メタデータを構築（URLリスト）
    metadata = ""
    for article in sorted(articles, key=lambda a: a.year, reverse=True):
        metadata += f"✦ **{article.year}年:** {article.title}\n{article.url}\n"

    # POSTするJSONデータを構築
    payload = {
        "content": content,
        "embeds": [
            {
                "description": metadata,
                "color": 5814783,  # カラーコード（青色）
            }
        ],
    }

    try:
        # サマリーテキストを投稿
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status not in [200, 204]:
                    response_text = await response.text()
                    print(f"Discordへの投稿に失敗: ステータス {response.status}, レスポンス: {response_text}")
                    return

            # 画像がある場合は、別途アップロード
            if image_path and image_path.exists():
                data = aiohttp.FormData()
                data.add_field("file", open(image_path, "rb"), filename=image_path.name)

                async with session.post(webhook_url, data=data) as response:
                    if response.status not in [200, 204]:
                        response_text = await response.text()
                        print(f"Discordへの投稿に失敗: ステータス {response.status}, レスポンス: {response_text}")
                        return

        print("Discordへの投稿に成功しました。")
    except Exception as e:
        print(f"Discordへの投稿中にエラーが発生: {e}")


async def post_to_slack(summary: str, articles: list[Article], image_path: Path | None) -> None:
    """
    生成されたサマリーをSlackに投稿する

    Args:
        summary: 生成されたサマリーテキスト
        articles: 記事リスト
        image_path: サマリー画像のパス（あれば）
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("Slack WebHook URLが設定されていません。")
        return

    # Slackのブロック形式のメッセージを構築
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*secon.dev 年間サマリー*\n\n{summary}",
            },
        },
        {"type": "divider"},
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "元記事リンク 🔗", "emoji": True},
        },
    ]

    # 各記事へのリンクをブロックに追加
    for article in sorted(articles, key=lambda a: a.year, reverse=True):
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"✦ *{article.year}年*: {article.title} / {article.date_str}\n{article.url}",
                },
            }
        )

    # Slackに投稿するペイロードを構築
    payload = {
        "blocks": blocks,
    }

    # Slackに投稿
    async with aiohttp.ClientSession() as session:
        async with session.post(webhook_url, json=payload) as response:
            if response.status != 200:
                print(f"Slackへの投稿に失敗: {response.status}")
                return

    # 画像のアップロード（本来はSlack APIトークンが必要）
    # ここでは簡略化して、画像がある場合はその旨を表示するだけ
    if image_path and image_path.exists():
        print(f"Slackへの画像アップロードはこの実装ではサポートされていません。画像パス: {image_path}")

    print("Slackへの投稿に成功しました。")

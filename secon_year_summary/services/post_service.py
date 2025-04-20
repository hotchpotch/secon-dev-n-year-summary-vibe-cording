"""
投稿サービスモジュール - Discord、Slack、標準出力への投稿機能
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp

from secon_year_summary.models.article import Article


def post_to_stdout(
    summary: str, articles: List[Article], image_path: Optional[Path]
) -> None:
    """
    標準出力に投稿する

    Args:
        summary: サマリー文字列
        articles: 記事リスト
        image_path: 画像パス
    """
    print("\n" + "-" * 50)
    print("📅 サマリー")
    print("-" * 50)
    print(summary)
    print("-" * 50)

    print("\n📊 メタデータ")
    print("-" * 50)
    for article in sorted(articles, key=lambda a: a.year, reverse=True):
        print(f"✦ {article.year}年: {article.title}")
        print(f"  URL: {article.url}")
    print("-" * 50)

    if image_path:
        print(f"\n🖼️ 画像: {image_path}")
        print("-" * 50)


async def post_to_discord(
    summary: str, articles: List[Article], image_path: Optional[Path]
) -> None:
    """
    Discordに投稿する

    Args:
        summary: サマリー文字列
        articles: 記事リスト
        image_path: 画像パス
    """
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("Discordへの投稿に失敗: DISCORD_WEBHOOK_URL が設定されていません。")
        return

    # メタデータ部分の作成
    metadata = "**📊 メタデータ**\n"
    for article in sorted(articles, key=lambda a: a.year, reverse=True):
        metadata += f"✦ **{article.year}年**: {article.title}\n"
        metadata += f"  URL: {article.url}\n"

    # 投稿内容の作成
    content = f"**📅 {articles[0].month}月{articles[0].day}日のサマリー**\n\n"
    content += summary

    # ファイルの準備
    files = []
    form_data = aiohttp.FormData()

    if image_path and image_path.exists():
        form_data.add_field(
            "file",
            open(image_path, "rb"),
            filename=image_path.name,
            content_type="image/png",
        )
        files.append({"id": 0, "description": "Generated summary image"})

    # webhookデータの準備
    webhook_data = {
        "content": content,
        "embeds": [
            {
                "title": "メタデータ",
                "description": metadata,
                "color": 5814783,  # カラーコード（青色）
            }
        ],
        "attachments": files,
    }

    # 投稿処理
    async with aiohttp.ClientSession() as session:
        if files:
            # 画像ありの場合はマルチパートフォームデータとして送信
            form_data.add_field("payload_json", json.dumps(webhook_data))
            async with session.post(webhook_url, data=form_data) as response:
                if response.status != 200:
                    print(f"Discordへの投稿に失敗: {response.status}")
                    return
        else:
            # 画像なしの場合はJSONとして送信
            async with session.post(webhook_url, json=webhook_data) as response:
                if response.status != 204:
                    print(f"Discordへの投稿に失敗: {response.status}")
                    return

    print("Discordへの投稿に成功しました。")


async def post_to_slack(
    summary: str, articles: List[Article], image_path: Optional[Path]
) -> None:
    """
    Slackに投稿する

    Args:
        summary: サマリー文字列
        articles: 記事リスト
        image_path: 画像パス
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("Slackへの投稿に失敗: SLACK_WEBHOOK_URL が設定されていません。")
        return

    # Slack用のメッセージブロック
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📅 {articles[0].month}月{articles[0].day}日のサマリー",
                "emoji": True,
            },
        },
        {"type": "section", "text": {"type": "mrkdwn", "text": summary}},
        {"type": "divider"},
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "📊 メタデータ", "emoji": True},
        },
    ]

    # メタデータの追加
    for article in sorted(articles, key=lambda a: a.year, reverse=True):
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"✦ *{article.year}年*: {article.title}\nURL: {article.url}",
                },
            }
        )

    # 画像の投稿準備
    if image_path and image_path.exists():
        # 画像を投稿する場合はSlackのファイルアップロードAPIを使用
        # 一般的なWebhookからは直接ファイルを投稿できないため、
        # 画像があることを知らせるメッセージを追加
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "🖼️ 画像は別途アップロードされます"},
            }
        )

    # メッセージペイロード
    payload = {"blocks": blocks}

    # 投稿処理
    async with aiohttp.ClientSession() as session:
        async with session.post(webhook_url, json=payload) as response:
            if response.status != 200:
                print(f"Slackへの投稿に失敗: {response.status}")
                return

    # 画像のアップロード（本来はSlack APIトークンが必要）
    # ここでは簡略化して、画像がある場合はその旨を表示するだけ
    if image_path and image_path.exists():
        print(
            f"Slackへの画像アップロードはこの実装ではサポートされていません。画像パス: {image_path}"
        )

    print("Slackへの投稿に成功しました。")

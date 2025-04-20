"""
画像生成サービスモジュール - 年間サマリーの画像生成
"""

import asyncio
import io
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import aiohttp
from PIL import Image, ImageDraw, ImageFont

from secon_year_summary.models.article import Article


async def download_image(session: aiohttp.ClientSession, url: str) -> Optional[bytes]:
    """画像URLから画像データを非同期でダウンロードする"""
    try:
        async with session.get(url) as response:
            if response.status != 200:
                return None
            return await response.read()
    except Exception as e:
        print(f"画像のダウンロードに失敗しました: {url} - {e}")
        return None


async def create_summary_image(
    articles: List[Article], target_date: datetime, output_path: Path
) -> Optional[Path]:
    """
    記事リストから年間サマリー画像を生成する

    Args:
        articles: 記事リスト
        target_date: 対象日付
        output_path: 出力先パス

    Returns:
        生成された画像のパス（失敗した場合はNone）
    """
    # 画像URLの収集（重複を除外）
    image_urls = set()
    article_dates = {}  # 画像URLと記事の年月日を関連付ける辞書

    for article in articles:
        if article.image_url:
            image_urls.add(article.image_url)
            # 画像URLと日付情報を関連付ける
            article_dates[article.image_url] = (
                article.year,
                article.month,
                article.day,
            )

    if not image_urls:
        print("画像URLが見つかりませんでした。")
        return None

    # 非同期で画像をダウンロード
    async with aiohttp.ClientSession() as session:
        tasks = [download_image(session, url) for url in image_urls]
        image_data_list = await asyncio.gather(*tasks)

    # 成功したダウンロードのみフィルタリング
    successful_downloads = []
    for i, data in enumerate(image_data_list):
        if data:
            url = list(image_urls)[i]
            successful_downloads.append((data, article_dates.get(url)))

    if not successful_downloads:
        print("画像のダウンロードに失敗しました。")
        return None

    # 画像の読み込みと日付の追加
    images = []
    for data, date_info in successful_downloads:
        try:
            img = Image.open(io.BytesIO(data))
            # サイズを統一（サムネイルサイズに）
            img.thumbnail((300, 300))

            # 日付情報を追加（右下、オレンジ色、半透明、小さめ）
            if date_info:
                year, month, day = date_info
                draw = ImageDraw.Draw(img, "RGBA")  # "RGBA"モードを使って透明度を設定
                try:
                    # フォントの設定
                    font = ImageFont.truetype("Arial", 12)
                except IOError:
                    # フォントが見つからない場合はデフォルトフォントを使用
                    font = ImageFont.load_default()

                # 日付テキスト
                date_text = f"{year}.{month:02d}.{day:02d}"

                # テキストのサイズを取得
                # textlengthはPIL 9.2.0以降で使えるが、古いバージョンではtextsize[0]を使う
                try:
                    text_width = draw.textlength(date_text, font=font)
                    text_height = font.size
                except AttributeError:
                    text_width, text_height = draw.textsize(date_text, font=font)

                # 右下に配置するための座標
                x = img.width - text_width - 10
                y = img.height - text_height - 5

                # 半透明のオレンジ色で日付を描画（RGBA形式で透明度を指定）
                draw.text(
                    (x, y),
                    date_text,
                    font=font,
                    fill=(255, 128, 0, 180),  # オレンジ色、透明度180/255
                )

            images.append(img)
        except Exception as e:
            print(f"画像の処理に失敗しました: {e}")

    if not images:
        print("画像の処理に失敗しました。")
        return None

    # 最大4枚までの画像を使用
    images = images[:4]

    # 画像の配置を決定
    if len(images) == 1:
        # 1枚の場合
        width = images[0].width
        height = images[0].height  # テキスト用の余白を削除
        layout = [(0, 0)]
    elif len(images) == 2:
        # 2枚の場合は横に並べる
        width = images[0].width + images[1].width
        height = max(images[0].height, images[1].height)
        layout = [(0, 0), (images[0].width, 0)]
    elif len(images) == 3:
        # 3枚の場合は上に1枚、下に2枚
        width = max(images[0].width, images[1].width + images[2].width)
        height = images[0].height + max(images[1].height, images[2].height)
        layout = [
            ((width - images[0].width) // 2, 0),
            (0, images[0].height),
            (images[1].width, images[0].height),
        ]
    else:
        # 4枚の場合は2x2グリッド
        width = images[0].width + images[1].width
        height = images[0].height + images[2].height
        layout = [
            (0, 0),
            (images[0].width, 0),
            (0, images[0].height),
            (images[1].width, images[1].height),
        ]

    # 新しい画像を作成
    result = Image.new("RGB", (width, height), color=(255, 255, 255))

    # 画像の貼り付け
    for i, img in enumerate(images):
        if i < len(layout):
            result.paste(img, layout[i])

    # 画像の保存
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(output_path)

    return output_path

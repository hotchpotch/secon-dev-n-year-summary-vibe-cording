"""
画像生成サービスモジュール - 年間サマリーの画像生成
"""

import asyncio
import io
import math
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
    images_with_dates = []
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

                # 日付情報と画像を格納
                images_with_dates.append((img, date_info))
        except Exception as e:
            print(f"画像の処理に失敗しました: {e}")

    if not images_with_dates:
        print("画像の処理に失敗しました。")
        return None

    # 日付の新しい順（降順）にソート
    images_with_dates.sort(key=lambda x: x[1], reverse=True)

    # ソートされた画像のみを取得
    images = [img for img, _ in images_with_dates]

    if not images:
        print("画像の処理に失敗しました。")
        return None

    # 最適なグリッドレイアウトの決定
    num_images = len(images)

    # グリッドのレイアウトを決定（行と列の数）
    if num_images <= 1:
        rows, cols = 1, 1
    elif num_images <= 2:
        rows, cols = 1, 2
    elif num_images <= 4:
        rows, cols = 2, 2
    elif num_images <= 6:
        rows, cols = 2, 3
    elif num_images <= 9:
        rows, cols = 3, 3
    elif num_images <= 12:
        rows, cols = 3, 4
    else:
        # それ以上の場合、ほぼ正方形に近いグリッドを作成
        cols = math.ceil(math.sqrt(num_images))
        rows = math.ceil(num_images / cols)

    # 画像の幅と高さを取得（均一サイズを前提）
    img_width = images[0].width
    img_height = images[0].height

    # 全体の画像サイズを計算
    width = cols * img_width
    height = rows * img_height

    # 新しい画像を作成
    result = Image.new("RGB", (width, height), color=(255, 255, 255))

    # 画像を配置
    for i, img in enumerate(images):
        if i >= rows * cols:
            break  # グリッドに収まる数だけ処理

        row = i // cols
        col = i % cols

        x = col * img_width
        y = row * img_height

        result.paste(img, (x, y))

    # 画像の保存
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(output_path)

    return output_path

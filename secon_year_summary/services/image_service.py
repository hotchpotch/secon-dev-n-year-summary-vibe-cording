"""
画像生成サービスモジュール - 年間サマリーの画像生成
"""

import asyncio
import io
import math
from datetime import datetime
from pathlib import Path
from typing import Set, Tuple

import aiohttp
from PIL import Image, ImageDraw, ImageFont

from secon_year_summary.models.article import Article


async def download_image(session: aiohttp.ClientSession, url: str) -> bytes | None:
    """画像URLから画像データを非同期でダウンロードする"""
    try:
        async with session.get(url) as response:
            if response.status != 200:
                return None
            return await response.read()
    except Exception as e:
        print(f"画像のダウンロードに失敗しました: {url} - {e}")
        return None


def crop_to_aspect_ratio(img: Image.Image, target_ratio: float = 3 / 2) -> Image.Image:
    """
    画像を指定されたアスペクト比（デフォルト3:2）になるようにクリッピングする

    Args:
        img: 入力画像
        target_ratio: 目標のアスペクト比（幅/高さ）

    Returns:
        クリッピングされた画像
    """
    width, height = img.size
    current_ratio = width / height

    if current_ratio > target_ratio:
        # 幅が広すぎる場合は左右をクリッピング
        new_width = int(height * target_ratio)
        left = (width - new_width) // 2
        return img.crop((left, 0, left + new_width, height))
    elif current_ratio < target_ratio:
        # 高さが高すぎる場合は上下をクリッピング
        new_height = int(width / target_ratio)
        top = (height - new_height) // 2
        return img.crop((0, top, width, top + new_height))

    # すでに指定された比率なら変更なし
    return img


async def create_summary_image(articles: list[Article], target_date: datetime, output_path: Path) -> Path | None:
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
    image_urls: Set[str] = set()
    article_dates: dict[str, Tuple[int, int, int]] = {}  # 画像URLと記事の年月日を関連付ける辞書

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
        image_data_list: list[bytes | None] = await asyncio.gather(*tasks)

    # 成功したダウンロードのみフィルタリング
    successful_downloads: list[tuple[bytes, tuple[int, int, int] | None]] = []
    url_list = list(image_urls)
    for i, data in enumerate(image_data_list):
        if data:
            url = url_list[i]
            successful_downloads.append((data, article_dates.get(url)))

    if not successful_downloads:
        print("画像のダウンロードに失敗しました。")
        return None

    # 統一サイズを設定（3:2アスペクト比）
    THUMBNAIL_WIDTH = 300
    THUMBNAIL_HEIGHT = 200  # 3:2比率で高さは200px
    UNIFORM_SIZE = (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT)

    # 画像の読み込みと日付の追加
    images_with_dates: list[tuple[Image.Image, tuple[int, int, int]]] = []
    for data, date_info in successful_downloads:
        try:
            # PILのImageオブジェクトを作成
            img = Image.open(io.BytesIO(data))

            # まず3:2のアスペクト比にクリッピング
            img = crop_to_aspect_ratio(img, 3 / 2)

            # クリッピングした画像をサムネイルサイズに変換
            img.thumbnail(UNIFORM_SIZE)

            # 正確に指定サイズにするために新しいキャンバスにリサイズした画像を配置
            canvas = Image.new("RGBA", UNIFORM_SIZE, (51, 51, 51, 255))
            paste_x = (UNIFORM_SIZE[0] - img.width) // 2
            paste_y = (UNIFORM_SIZE[1] - img.height) // 2
            canvas.paste(img, (paste_x, paste_y))
            img = canvas

            # 日付情報を追加（右下、オレンジ色、半透明、小さめ）
            if date_info:
                year, month, day = date_info
                draw = ImageDraw.Draw(img)

                try:
                    # フォントの設定
                    font = ImageFont.truetype("Arial", 12)
                except OSError:
                    # フォントが見つからない場合はデフォルトフォントを使用
                    font = ImageFont.load_default()

                # 日付テキスト
                date_text = f"{year}.{month:02d}.{day:02d}"

                # テキストのサイズを取得
                try:
                    # PIL 9.2.0以降の場合
                    text_width = draw.textlength(date_text, font=font)
                    text_bbox = font.getbbox(date_text)
                    text_height = text_bbox[3] if text_bbox else 12  # フォントの高さを取得
                except AttributeError:
                    # 古いバージョンの場合
                    text_bbox = font.getbbox(date_text)
                    if text_bbox:
                        text_width, text_height = (
                            text_bbox[2] - text_bbox[0],
                            text_bbox[3] - text_bbox[1],
                        )
                    else:
                        text_width, text_height = 80, 12  # デフォルト値

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

            # 日付情報と画像を格納（日付情報がない場合でも画像は格納する）
            date_tuple = date_info if date_info else (0, 0, 0)
            images_with_dates.append((img, date_tuple))
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
    else:
        # 9より多い場合は適切な行数と列数を計算
        cols = min(int(math.ceil(math.sqrt(num_images))), 4)  # 最大4列までに制限
        rows = math.ceil(num_images / cols)

    # マージンとパディングの設定
    padding = 3  # 画像間のパディング
    canvas_width = cols * THUMBNAIL_WIDTH + (cols - 1) * padding
    canvas_height = rows * THUMBNAIL_HEIGHT + (rows - 1) * padding

    # 背景色（ダークグレー）
    bg_color = (51, 51, 51, 255)  # RGB + alpha

    # 画像の合成
    canvas = Image.new("RGBA", (canvas_width, canvas_height), bg_color)

    # 画像の配置（グリッドレイアウト）
    for i, img in enumerate(images[: rows * cols]):  # 最大行×列の画像だけ配置
        row = i // cols
        col = i % cols
        x = col * (THUMBNAIL_WIDTH + padding)
        y = row * (THUMBNAIL_HEIGHT + padding)
        canvas.paste(img, (x, y))

    # PNG形式で保存
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas = canvas.convert("RGB")  # RGBモードに変換（PNGで透明度が必要なければ）
    canvas.save(output_path, format="PNG")

    return output_path

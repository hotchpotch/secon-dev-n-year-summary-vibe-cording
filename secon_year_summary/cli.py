#!/usr/bin/env python
import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from secon_year_summary.models.article import ArticleFetcher
from secon_year_summary.services.image_service import create_summary_image
from secon_year_summary.services.llm_service import get_llm_service
from secon_year_summary.services.post_service import (
    post_to_discord,
    post_to_slack,
    post_to_stdout,
)


async def main_async(
    target_date: datetime,
    model_name: str,
    years_back: int,
    post_to: list[str],
    verbose: bool,
) -> None:
    """非同期メイン処理"""
    # 記事の取得
    if verbose:
        print(f"🔍 {target_date.date()} の記事を {years_back} 年分取得しています...")

    fetcher = ArticleFetcher(target_date, years_back)
    articles = await fetcher.fetch_articles()

    if not articles:
        print(f"⚠️ {target_date.date()} の記事が見つかりませんでした。")
        return

    # LLMサービスの初期化
    llm_service = get_llm_service(model_name)

    if verbose:
        print(f"🤖 {model_name} を使用してサマリーを生成しています...")

    # サマリーの生成
    summary = await llm_service.generate_summary(articles, target_date)

    # 保存パスの作成
    date_str = target_date.strftime("%Y%m%d")
    vendor, model = model_name.split("/", 1)

    # 出力ディレクトリの確認
    output_text_dir = Path(f"output/texts/{date_str}")
    output_text_dir.mkdir(parents=True, exist_ok=True)

    # サマリーテキストの保存
    output_file = output_text_dir / f"{vendor}_{model}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(summary)

    if verbose:
        print(f"✅ サマリーを {output_file} に保存しました。")

    # サマリー画像の生成
    output_image_path = Path(f"output/images/{date_str}.png")
    image_path = await create_summary_image(articles, target_date, output_image_path)

    if verbose and image_path:
        print(f"🖼️ サマリー画像を {image_path} に保存しました。")

    # 投稿処理
    for dest in post_to:
        if dest == "stdout":
            post_to_stdout(summary, articles, image_path)
        elif dest == "discord":
            await post_to_discord(summary, articles, image_path)
        elif dest == "slack":
            await post_to_slack(summary, articles, image_path)


def main() -> None:
    """コマンドラインエントリーポイント"""
    # .envファイルの読み込み
    load_dotenv()

    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(
        description="secon.dev の同じ日付の過去の記事をまとめるツール"
    )

    parser.add_argument(
        "-d",
        "--date",
        help="対象となる日付（YYYY-MM-DD形式）。指定しない場合は今日の日付が使用されます。",
        type=str,
        default=None,
    )

    parser.add_argument(
        "-m",
        "--model",
        help="使用するLLMモデル（ベンダー/モデル名の形式）",
        type=str,
        default="openai/gpt-4.1-nano",
    )

    parser.add_argument(
        "-y", "--years", help="過去何年分の記事を取得するか", type=int, default=10
    )

    parser.add_argument(
        "-p",
        "--post",
        help="投稿先（複数指定可）",
        choices=["stdout", "discord", "slack"],
        action="append",
        default=[],
    )

    parser.add_argument("-v", "--verbose", help="詳細な出力を表示", action="store_true")

    args = parser.parse_args()

    # デフォルトの投稿先の設定
    if not args.post:
        args.post = ["stdout"]

    # 日付の解析
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print(
                "エラー: 日付の形式が正しくありません。YYYY-MM-DD形式で指定してください。"
            )
            sys.exit(1)
    else:
        # 対象日時が指定されない場合は「一年前の今日」
        target_date = datetime.now()
        target_date = target_date.replace(year=target_date.year - 1)

    # 非同期メイン処理の実行
    asyncio.run(
        main_async(
            target_date=target_date,
            model_name=args.model,
            years_back=args.years,
            post_to=args.post,
            verbose=args.verbose,
        )
    )


if __name__ == "__main__":
    main()

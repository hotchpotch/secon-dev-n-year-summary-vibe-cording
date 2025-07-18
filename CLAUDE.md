# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

secon.devサイトの日記から過去の同日記事を収集し、LLMで年間サマリーを生成するCLIツール。vibe-codingの練習として、ほぼ全てCursorで実装されています。

## 開発コマンド

```bash
# 依存関係のインストール
uv sync --all-extras

# テスト実行
uv run pytest
# または
pytest  # 仮想環境内

# コードフォーマット
ruff format .

# リントチェック
ruff check .

# 型チェック
pyright

# CLIツール実行
uv run secon-year-summary [OPTIONS]
# または
secon-year-summary [OPTIONS]  # 仮想環境内
```

## アーキテクチャ概要

### ディレクトリ構造
- `secon_year_summary/cli.py` - CLIエントリーポイント、引数パース
- `secon_year_summary/models/` - データモデル（記事フェッチャー含む）
- `secon_year_summary/services/` - ビジネスロジック層
  - `llm_service.py` - LLM抽象化レイヤー（OpenAI/Gemini/Claude）
  - `image_service.py` - 画像生成（記事画像を1枚にまとめる）
  - `post_service.py` - 投稿先への送信（Discord/Slack/stdout）

### 主要な設計パターン

1. **非同期処理**: asyncioを使用した並列処理で複数年の記事を効率的に取得
2. **LLM抽象化**: 基底クラス`LLMService`で各ベンダーのAPIを統一インターフェースで扱う
3. **環境変数管理**: `.env`ファイルでAPIキーやWebhook URLを管理（python-dotenv使用）

### 重要な仕様

- **サマリー文字数**: 各年50-100文字程度（`services/llm_service.py`で定義）
- **記事取得ロジック**: 対象日の記事ページから`.similar-entries`セレクタで過去記事リンクを抽出
- **画像生成**: 背景色`#333333`、各画像右下に日付表示（オレンジ色、12px）
- **デフォルト動作**: 1年前の今日の記事を過去10年分取得し、OpenAI GPT-4.1-nanoで要約

### テスト・品質管理

- pytestでの単体テスト（モック使用）
- ruffでのリント（Python 3.12対応、行長120文字）
- pyrightでの厳密な型チェック（strictモード）
- GitHub Actionsでの自動テスト（PR/push時）

### デプロイ・自動実行

- GitHub Actions `daily_summary.yml`で毎日JST午前1時に自動実行
- デフォルトでGemini Flash使用、Discord投稿
- 必要なシークレット: `GOOGLE_API_KEY`, `DISCORD_WEBHOOK_URL`
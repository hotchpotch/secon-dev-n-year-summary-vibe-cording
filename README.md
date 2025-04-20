# secon-year-summary

secon.dev サイトの日記を読み込み、同日に書かれた過去の記事をまとめて年間サマリーを生成するツールです。

## インストール

```bash
# uv を使ったインストール（推奨）
uv pip install -e .

# または pip でもインストール可能
pip install -e .
```

## 使い方

```bash
# 基本的な使い方（今日の日付の記事を対象に）
secon-year-summary

# 特定の日付の記事を対象に
secon-year-summary --date 2024-04-29

# 使用するLLMモデルを指定
secon-year-summary --model openai/gpt-4.1-nano

# Discordに投稿
secon-year-summary --post discord

# Slackに投稿
secon-year-summary --post slack

# 複数の投稿先に送信
secon-year-summary --post discord --post slack
```

## 環境変数

`.env` ファイルに以下の変数を設定します：

```
# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# Google Gemini API
GOOGLE_API_KEY=your_google_api_key

# Anthropic Claude API
ANTHROPIC_API_KEY=your_anthropic_api_key

# Discord Webhook URL
DISCORD_WEBHOOK_URL=your_discord_webhook_url

# Slack Webhook URL
SLACK_WEBHOOK_URL=your_slack_webhook_url
``` 
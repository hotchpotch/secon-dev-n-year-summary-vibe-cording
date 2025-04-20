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
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_id/your_webhook_token

# Slack Webhook URL
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your_slack_webhook_path
```

注意: Discord WebhookのURLは必ず`https://discord.com/api/webhooks/`から始まるURLを設定してください。

## Discord Webhookの設定方法

1. Discordのサーバー設定を開く
2. 「インテグレーション」→「ウェブフック」を選択
3. 「新しいウェブフック」を作成
4. ウェブフックに名前をつけ、投稿したいチャンネルを選択
5. 「ウェブフックURLをコピー」をクリック
6. コピーしたURLを`.env`ファイルの`DISCORD_WEBHOOK_URL`に設定

## Slack Webhookの設定方法

1. Slack APIのウェブサイト(https://api.slack.com/apps)にアクセス
2. 「Create New App」をクリック
3. アプリを作成し「Incoming Webhooks」を有効化
4. 「Add New Webhook to Workspace」をクリック
5. 投稿先のチャンネルを選択
6. 生成されたWebhook URLをコピー
7. コピーしたURLを`.env`ファイルの`SLACK_WEBHOOK_URL`に設定

## 実行例

指定した日付の過去記事をまとめ、Discordに投稿：

```bash
# .envファイルに環境変数を設定後
secon-year-summary --date 2024-04-20 --post discord --model openai/gpt-4.1-nano
```

同様にSlackに投稿：

```bash
secon-year-summary --date 2024-04-20 --post slack
```

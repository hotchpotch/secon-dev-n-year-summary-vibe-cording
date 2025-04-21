# secon-year-summary

secon.dev サイトの日記を読み込み、指定された日付と同日に書かれた過去の記事をまとめて年間サマリーを生成するツールです。

[詳細な仕様はこちら](docs/specification.md)

## 特徴

- 特定の日付の過去記事（デフォルトは1年前の今日）を自動で収集
- 複数のLLM（OpenAI, Gemini, Claude）を選択してサマリーを生成
- 生成されたサマリーと記事の画像をDiscord, Slack, または標準出力に投稿
- 記事の画像（OGP画像）をまとめて1枚の画像に生成

## インストール

1. リポジトリをクローンします:
   ```bash
   git clone https://github.com/hotchpotch/secon-dev-n-year-summary-vibe-cording.git
   cd secon-dev-n-year-summary-vibe-cording
   ```

2. 依存関係をインストールします:
   - [uv](https://github.com/astral-sh/uv) がインストールされている必要があります。
   ```bash
   # 仮想環境を作成 (推奨)
   uv venv
   source .venv/bin/activate

   # 依存関係を同期
   uv sync
   ```
   または `pip` を使用する場合:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .[dev] # 開発用依存関係も含む場合
   # pip install -e .
   ```

## 設定

プロジェクトルートに `.env` ファイルを作成し、必要な環境変数を設定します。

```dotenv
# .envファイル の例

# --- APIキー (使用するLLMに応じて設定) ---
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIzaSy...
ANTHROPIC_API_KEY=sk-ant-api03-...

# --- Webhook URL (投稿先に応じて設定) ---
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# --- その他 (必要に応じて) ---
# 例: プロキシ設定など
# HTTP_PROXY=http://proxy.example.com:8080
# HTTPS_PROXY=https://proxy.example.com:8080
```

- 各種APIキーは、利用するLLMサービスのものを設定してください。
- DiscordやSlackに投稿する場合は、それぞれのWebhook URLを設定してください。設定方法は各サービスのドキュメントを参照してください。

## 使い方

基本的なコマンド:

```bash
secon-year-summary [OPTIONS]
```

**オプション:**

- `-d, --date <YYYY-MM-DD>`: 対象とする日付を指定します。指定しない場合は**一年前の今日**が使用されます。
- `-m, --model <VENDOR/MODEL_NAME>`: 使用するLLMモデルを指定します。 (デフォルト: `openai/gpt-4.1-nano`)
  - 例: `openai/gpt-4o`, `google/gemini-1.5-pro`, `anthropic/claude-3-sonnet-20240229`
- `-y, --years <NUMBER>`: 過去何年分の記事を遡るかを指定します。 (デフォルト: `10`)
- `-p, --post <DESTINATION>`: 投稿先を指定します。複数指定可能です (`stdout`, `discord`, `slack`)。指定しない場合は `stdout` に出力されます。
  - 例: `-p discord -p slack`
- `-v, --verbose`: 詳細なログを出力します。

**実行例:**

1.  **デフォルト設定で実行 (1年前の今日の記事を対象に、OpenAIモデルを使用し、標準出力へ):**
    ```bash
    secon-year-summary
    ```

2.  **特定の日付を指定して実行:**
    ```bash
    secon-year-summary -d 2023-05-15
    ```

3.  **使用するLLMモデルを変更 (Geminiを使用):**
    ```bash
    secon-year-summary -m google/gemini-1.5-pro
    ```

4.  **遡る年数を変更 (過去5年分):**
    ```bash
    secon-year-summary -y 5
    ```

5.  **Discordに投稿:**
    ```bash
    secon-year-summary -p discord
    ```

6.  **Slackと標準出力に投稿し、詳細ログを表示:**
    ```bash
    secon-year-summary -p slack -p stdout -v
    ```

7.  **特定の日付の過去15年分の記事をClaudeモデルで処理し、DiscordとSlackに投稿:**
    ```bash
    secon-year-summary -d 2024-01-01 -y 15 -m anthropic/claude-3-opus-20240229 -p discord -p slack
    ```

## 開発

- **テスト:** `pytest` を使用します。
  ```bash
  uv run pytest
  ```
- **フォーマット & Lint:** `ruff` と `pyright` を使用します。
  ```bash
  # フォーマット
  uv run ruff format .
  # Lint
  uv run ruff check .
  uv run pyright
  ```

## ライセンス

[MIT](LICENSE)

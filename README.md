# secon-year-summary

※このプロジェクトは、vibe-cording の練習として、ほぼ全て cursor に書いてもらった実装のみで構成されています。

secon.dev サイトの日記を読み込み、指定された日付と同日に書かれた過去の記事をまとめて年間サマリーを生成するツールです。

[詳細な仕様はこちら](docs/specification.md)

## 特徴

- 特定の日付の過去記事（デフォルトは1年前の今日）を自動で収集
- 複数のLLM（OpenAI, Gemini, Claude）を選択してサマリーを生成
- 生成されたサマリーと記事の画像をDiscord, Slack, または標準出力に投稿
- 記事の画像（OGP画像）をまとめて1枚の画像に生成

## 実行例

```bash
$ uv run secon-year-summary --model google/gemini-1.5-flash-latest -v -d 2024-01-27
🔍 2024-01-27 の記事を 10 年分取得しています...
🤖 google/gemini-1.5-flash-latest を使用してサマリーを生成しています...
✅ サマリーを output/texts/20240127/google_gemini-1.5-flash-latest.md に保存しました。
🖼️ サマリー画像を output/images/20240127.png に保存しました。

==================================================
📝 生成されたサマリー:
==================================================
## 2024年01月27日 🎶

昔聴いたジャズアルバム（Greetje KauffeldのAnd Let The Music Play）をlast.fmの過去履歴で発見！SpotifyになくYouTube Musicで聴けたが音質に疑問、中古CD購入を決意。last.fmの自分の記録の価値を再認識し、Spotify連携を設定。夕食は南国食堂マムアンでタイラーメンとガパオを堪能 、特にタイラーメンの絶妙な味付けに満足した。

## 2023年01月27日 ♨️

個人事業主から法人成り直後だと住宅ローン審査が厳しいという落とし穴を知るも、建築事務所の尽力で無事仮審査通過。生涯で何度もない経験に 勉強になった一日。夜は雪が残る那須山温泉へ。外気温の影響でキンキンに冷えた水風呂がヤバい気持ちよさ。Kindle Paperwhiteでフォントサイズを大きくして読むのが老眼に優しく快適だった。

## 2022年01月27日 🎬

15年使用したshibuyajs.orgドメインの更新失敗通知。更新継続か手放すか悩む。shibuya.pmの継続的な活動に感心。フィルムカメラにiPhoneを付けるデジスワップ技術を知り、過去の類似品Imagek EFS-1に興味。久しぶりにCOLOR-SKOPAR 21mmで撮影。映画ターミネーター3を鑑賞、ド派手なアク ションを楽しんだ。最適化数学の本も読み進め、仕事に活かせそうな知識が増えて楽しい。

## 2021年01月27日 😲

近所の新店舗開店祝いにフラワーギフトを贈る。Gmailの過去メールを遡っていたら、なんと2005年にプログラマーの_whyから英語のメールが来ており、自身がつたない英語で返信していたことを発見！全く記憶になかったことに衝撃を受け、_whyが今も元気にしていることを願った一日だった。

## 2020年01月27日 🚂

前日の風邪薬が効いて体調回復！午後、リヤドからペルシャ湾岸の都市ダンマームへ列車で移動。車窓には延々と砂漠が広がり、電線や道路以外は 何も見えない光景に土地柄を実感。ダンマーム到着後、リヤドとは違う高層ビル群に発展を感じる。乗客の女性にニカブが多いことに地域差を感じ 、ホテルではフィリピン人と間違えられて納得した。
==================================================

🔗 元記事リンク:
  • 2024年: https://secon.dev/entry/2024/01/27/210000/
  • 2023年: https://secon.dev/entry/2023/01/27/210000/
  • 2022年: https://secon.dev/entry/2022/01/27/210000/
  • 2021年: https://secon.dev/entry/2021/01/27/210000/
  • 2020年: https://secon.dev/entry/2020/01/27/000000/

🖼️ サマリー画像が保存されました: output/images/20240127.png
```

![サマリー画像例](examples/images/20240127.png)


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
   uv sync --all-extras
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

仮想環境を有効化した後 (`source .venv/bin/activate`)、以下のいずれかの方法でコマンドを実行できます。

1. **直接実行:**

    ```bash
    secon-year-summary [OPTIONS]
    ```

2. **`uv run` を使用:**

    ```bash
    uv run secon-year-summary [OPTIONS]
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

以降の例では `secon-year-summary` を直接実行していますが、代わりに `uv run secon-year-summary` を使用することも可能です。

1. **デフォルト設定で実行 (1年前の今日の記事を対象に、OpenAIモデルを使用し、標準出力へ):**

    ```bash
    # 直接実行
    secon-year-summary
    # または uv run を使用
    # uv run secon-year-summary
    ```

2. **特定の日付を指定して実行:**

    ```bash
    secon-year-summary -d 2023-05-15
    # uv run secon-year-summary -d 2023-05-15
    ```

3. **使用するLLMモデルを変更 (Geminiを使用):**

    ```bash
    secon-year-summary -m google/gemini-1.5-pro
    # uv run secon-year-summary -m google/gemini-1.5-pro
    ```

4. **遡る年数を変更 (過去5年分):**

    ```bash
    secon-year-summary -y 5
    # uv run secon-year-summary -y 5
    ```

5. **Discordに投稿:**

    ```bash
    secon-year-summary -p discord
    # uv run secon-year-summary -p discord
    ```

6. **Slackと標準出力に投稿し、詳細ログを表示:**

    ```bash
    secon-year-summary -p slack -p stdout -v
    # uv run secon-year-summary -p slack -p stdout -v
    ```

7. **特定の日付の過去15年分の記事をClaudeモデルで処理し、DiscordとSlackに投稿:**

    ```bash
    secon-year-summary -d 2024-01-01 -y 15 -m anthropic/claude-3-opus-20240229 -p discord -p slack
    # uv run secon-year-summary -d 2024-01-01 -y 15 -m anthropic/claude-3-opus-20240229 -p discord -p slack
    ```

## 開発

- **テスト:** `pytest` を使用します。

  ```bash
  pytest
  ```

- **フォーマット & Lint:** `ruff` と `pyright` を使用します。

  ```bash
  ruff format .
  ruff check .
  pyright
  ```

## ライセンス

[MIT](LICENSE)

## GitHub Actionsでの実行

このツールは GitHub Actions を利用して自動化されています。

### 1. シークレットの設定

ワークフローを実行するには、まずリポジトリの Actions secrets に以下の情報を設定する必要があります。これにより、APIキーやWebhook URLがワークフローファイルに直接書き込まれるのを防ぎます。

1. GitHubリポジトリの `Settings` -> `Secrets and variables` -> `Actions` に移動します。
2. `New repository secret` をクリックして、以下のシークレットを追加します（利用する機能に応じて必要なもののみ）。
    - `OPENAI_API_KEY`: OpenAI APIキー
    - `GOOGLE_API_KEY`: Google Gemini APIキー
    - `ANTHROPIC_API_KEY`: Anthropic Claude APIキー
    - `DISCORD_WEBHOOK_URL`: Discord Webhook URL
    - `SLACK_WEBHOOK_URL`: Slack Webhook URL

### 2. 既存のワークフロー

`.github/workflows/` ディレクトリに、以下のワークフローが定義されています。

- **`daily_summary.yml`**:
  - 毎日定刻 (JST 午前1時 / UTC 16時) に自動実行されます (`schedule` トリガー)。
  - GitHub ActionsのUIから手動で実行することも可能です (`workflow_dispatch` トリガー)。
  - 1年前の今日の記事を取得し、指定されたLLMモデル（デフォルトではGemini）で要約を生成し、Discordに投稿します。
  - 実行するモデルや投稿先などの詳細は、ワークフローファイル内の `Run summary script` ステップで設定されています。
  - 実行には `GOOGLE_API_KEY` と `DISCORD_WEBHOOK_URL` のシークレット設定が必要です（ワークフロー内で他のLLMや投稿先を使う場合は、対応するシークレットも必要）。

- **`pytest.yml`**:
  - `main` ブランチへの `push` または `pull_request` をトリガーとして自動実行されます。
  - `pytest` を使用して、プロジェクトのテストを実行します。
  - このワークフローは、コードの品質を維持するために重要です。

これらのワークフローファイルを参照し、必要に応じて設定（特に `daily_summary.yml` 内の実行コマンドオプションや利用するシークレット）を調整してください。

# LINE Chat Bot with Google Gemini AI

Google Gemini AIを利用したLINE Botです。Geminiの検索機能を活用して、より正確で最新の情報を含む応答を提供します。

## 機能

- Google Gemini AIによる自然言語処理
- Google検索機能の統合
- マークダウン形式でのリッチな応答表示
- コードブロックの適切な表示
- エラーハンドリングとロギング

## 技術スタック

- Python 3.11
- FastAPI
- LINE Messaging API
- Google Gemini AI
- Docker & Docker Compose
- ngrok（開発環境用トンネリング）

## セットアップ

1. 必要な環境変数を設定
   ```bash
   cp .env.example .env
   ```
   以下の環境変数を設定してください：
   - `LINE_CHANNEL_SECRET`
   - `LINE_CHANNEL_ACCESS_TOKEN`
   - `GOOGLE_API_KEY`
   - `NGROK_AUTHTOKEN`

2. Dockerでビルド・起動
   ```bash
   docker-compose up --build
   ```

## 環境変数

| 変数名 | 説明 | 必須 |
|--------|------|------|
| LINE_CHANNEL_SECRET | LINE Messaging APIのチャンネルシークレット | ✅ |
| LINE_CHANNEL_ACCESS_TOKEN | LINE Messaging APIのアクセストークン | ✅ |
| GOOGLE_API_KEY | Google Gemini AIのAPIキー | ✅ |
| NGROK_AUTHTOKEN | ngrokの認証トークン | ✅ |
| DEBUG | デバッグモードの有効化（true/false） | - |

## 開発環境の準備

1. LINE Developersでチャンネルを作成
2. Google Cloud Platformでプロジェクトを作成し、Gemini APIを有効化
3. ngrokアカウントを作成し、認証トークンを取得

## デプロイ

1. 本番環境用のWebhook URLを設定
2. 環境変数を本番環境に設定
3. Dockerコンテナをビルド・起動

## API仕様

### Webhook エンドポイント

```
POST /callback
```

### リクエスト例（LINEからのWebhook）

```json
{
  "destination": "xxxxxxxxxx",
  "events": [
    {
      "type": "message",
      "message": {
        "type": "text",
        "id": "xxxxx",
        "text": "fizzbuzzのpython"
      },
      "timestamp": 1703999771818,
      "source": {
        "type": "user",
        "userId": "xxxxx"
      },
      "replyToken": "xxxxx",
      "mode": "active"
    }
  ]
}
```

### Gemini APIレスポンス構造

```json
{
  "candidates": [
    {
      "content": {
        "parts": [
          {
            "text": "はい、FizzBuzzをPythonで実装する方法ですね。..."
          },
          {
            "text": "```python\ndef fizzbuzz(n):\n    for i in range(1, n + 1):\n        ..."
          }
        ],
        "role": "model"
      },
      "grounding_metadata": {
        "web_search_queries": [
          "fizzbuzz explanation",
          "what is fizzbuzz"
        ]
      }
    }
  ]
}
```

### LINE応答メッセージ構造（Flex Message）

```json
{
  "type": "flex",
  "altText": "Geminiからの応答",
  "contents": {
    "type": "bubble",
    "body": {
      "type": "box",
      "layout": "vertical",
      "contents": [
        {
          "type": "text",
          "text": "説明テキスト",
          "wrap": true,
          "size": "md"
        },
        {
          "type": "box",
          "layout": "vertical",
          "backgroundColor": "#f5f5f5",
          "contents": [
            {
              "type": "text",
              "text": "コードブロック",
              "wrap": true,
              "size": "sm",
              "color": "#333333"
            }
          ]
        }
      ]
    }
  }
}
```

### データフロー

1. LINEからのWebhookを受信
2. メッセージテキストを抽出しGemini APIに送信
3. Geminiからの応答をパース
4. マークダウン形式のテキストをFlex Messageに変換
5. LINEへ応答を送信

## ディレクトリ構造
```
/
├── app/
│ ├── __init__.py
│ ├── main.py
│ └── config.py
├── docker-compose.yml
├── docker-compose.example.yml
├── Dockerfile
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
└── readme.md
```

## ライセンス

MIT License

## 注意事項

- Google Gemini AIの利用料金が発生する可能性があります
- LINE Messaging APIの利用制限に注意してください
- 本番環境では適切なセキュリティ対策を実施してください

## 貢献

1. このリポジトリをフォーク
2. 新しいブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 作者

jydie5

## 謝辞

- Google Gemini AI
- LINE Messaging API
- FastAPI
- その他、利用しているオープンソースプロジェクト

## 設定ファイル

### .env.example

```
DEBUG=true
LINE_CHANNEL_SECRET=your_line_channel_secret_here
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token_here
GOOGLE_API_KEY=your_google_api_key_here
NGROK_AUTHTOKEN=your_ngrok_auth_token_here
```

### docker-compose.example.yml

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app/app
      - ./.env:/app/.env
    environment:
      - DEBUG=true
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - LINE_CHANNEL_SECRET=${LINE_CHANNEL_SECRET}
      - LINE_CHANNEL_ACCESS_TOKEN=${LINE_CHANNEL_ACCESS_TOKEN}
    restart: unless-stopped

  ngrok:
    image: ngrok/ngrok:latest
    depends_on:
      - api
    ports:
      - "4040:4040"
    volumes:
      - ./.env:/app/.env
    command: http --domain=your-domain-here.ngrok-free.app api:8000 --log stdout
    environment:
      - NGROK_AUTHTOKEN=${NGROK_AUTHTOKEN}
```
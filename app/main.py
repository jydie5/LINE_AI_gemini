from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import logging
from google import genai
import asyncio
import json
import os

from .config import settings

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# LINE Bot設定
line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

# Gemini設定
client = genai.Client()  # 環境変数GOOGLE_API_KEYから自動的に取得

# チャットの初期化
chat = client.chats.create(
    model='gemini-2.0-flash-exp',
    config={
        'tools': [{'google_search': {}}]
    }
)

def format_response(response) -> str:
    try:
        # レスポンス全体をログに記録
        logger.info("Raw response structure:")
        logger.info(json.dumps(response.model_dump(), indent=2, ensure_ascii=False))

        parts = response.candidates[0].content.parts
        if parts is None:
            logger.warning("Response parts is None")
            return "応答を生成できませんでした。"

        # 各パートの構造をログに記録
        for i, part in enumerate(parts):
            logger.info(f"Part {i} structure:")
            logger.info(json.dumps(part.model_dump(), indent=2, ensure_ascii=False))

        formatted_response = []
        for part in parts:
            if hasattr(part, 'text') and part.text:
                # テキストの内容をログに記録
                logger.info(f"Text content: {part.text}")
                formatted_response.append(part.text)
            else:
                # テキスト以外の内容をログに記録
                logger.info(f"Non-text content: {json.dumps(part.model_dump(), indent=2, ensure_ascii=False)}")

        # 検索結果の処理
        metadata = getattr(response.candidates[0], 'grounding_metadata', None)
        if metadata:
            logger.info("Search metadata found:")
            logger.info(json.dumps(metadata.model_dump(), indent=2, ensure_ascii=False))
            
            search_results = getattr(metadata, 'web_search_results', [])
            if search_results:
                formatted_response.append("\n\n参考情報：")
                for result in search_results:
                    formatted_response.append(f"- {result.title}")
                    formatted_response.append(f"  {result.url}\n")

        final_response = "\n".join(formatted_response)
        logger.info(f"Final formatted response: {final_response}")
        return final_response

    except Exception as e:
        logger.error(f"Error formatting response: {str(e)}", exc_info=True)
        return "申し訳ありません。応答の処理中にエラーが発生しました。"

async def get_gemini_response(question: str) -> str:
    try:
        # 非同期的に応答を取得
        response = await asyncio.to_thread(chat.send_message, question)
        return format_response(response)
    
    except Exception as e:
        logger.error(f"Gemini API error: {str(e)}")
        return "申し訳ありません。現在応答を生成できません。しばらく後でもう一度お試しください。"

async def handle_text_message(event: MessageEvent):
    try:
        question = event.message.text.strip()
        user_id = event.source.user_id
        logger.info(f"Received message from {user_id}: {question}")

        # Geminiから応答を取得
        response = await get_gemini_response(question)
        
        # LINE経由で応答を送信
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response)
        )

    except LineBotApiError as e:
        logger.error(f"LINE API Error: {str(e)}", exc_info=True)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="申し訳ありません。エラーが発生しました。")
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)

@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    body_text = body.decode()

    try:
        events = parser.parse(body_text, signature)
        for event in events:
            if isinstance(event, MessageEvent):
                if isinstance(event.message, TextMessage):
                    await handle_text_message(event)
        
        logger.info("Webhook handled successfully")
        return JSONResponse(content={"message": "OK"})
        
    except InvalidSignatureError:
        logger.error("Invalid signature error")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Unexpected error in callback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
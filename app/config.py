# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "LINE Chat Bot with Gemini"
    DEBUG: bool = False
    
    # LINE Bot設定
    LINE_CHANNEL_SECRET: str
    LINE_CHANNEL_ACCESS_TOKEN: str
    
    # Gemini API設定
    GEMINI_API_KEY: str
    
    # Ngrok設定
    NGROK_AUTHTOKEN: str | None = None

    class Config:
        env_file = ".env"
        extra = "ignore"  # 追加の環境変数を無視する

settings = Settings()
"""
애플리케이션 설정

환경변수 기반 설정 관리
"""

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API 키들
    openai_api_key: str = ""
    google_maps_api_key: str = ""
    notion_token: str = ""
    notion_database_id: str = ""
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
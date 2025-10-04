import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    telegram_bot_token: str
    openai_api_key: str
    tin_client_id: str
    tin_client_secret: str
    tin_token: str
    tin_api_base: str = "https://invest-public-api.tinkoff.ru/rest"
    feature_tbank: bool = True

    moex_iss_timeout: int = 8
    moex_iss_cache_ttl: int = 60
    feature_moex_iss: bool = True

    news_rss_rbc: str = "https://rssexport.rbc.ru/rbcnews/news/30/full.rss"
    news_rss_smartlab: str = "https://smart-lab.ru/rss/news/"

    vision_provider: str = "openai"
    vision_model: str = "gpt-4o"

    feature_news_alerts: bool = True
    feature_analysis_v13: bool = True
    feature_analysis_v14: bool = True
    feature_ocr_v2: bool = True
    feature_ocr_v3: bool = True

    database_url: str = "sqlite:///radar_bot.db"

    cache_ttl: int = 300

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            tin_client_id=os.getenv("TIN_CLIENT_ID", ""),
            tin_client_secret=os.getenv("TIN_CLIENT_SECRET", ""),
            tin_token=os.getenv("TIN_TOKEN", ""),
            tin_api_base=os.getenv("TIN_API_BASE", "https://invest-public-api.tinkoff.ru/rest"),
            feature_tbank=os.getenv("FEATURE_TBANK", "1") == "1",
            moex_iss_timeout=int(os.getenv("MOEX_ISS_TIMEOUT", "8")),
            moex_iss_cache_ttl=int(os.getenv("MOEX_ISS_CACHE_TTL", "60")),
            feature_moex_iss=os.getenv("FEATURE_MOEX_ISS", "1") == "1",
            news_rss_rbc=os.getenv("NEWS_RSS_RBC", "https://rssexport.rbc.ru/rbcnews/news/30/full.rss"),
            news_rss_smartlab=os.getenv("NEWS_RSS_SMARTLAB", "https://smart-lab.ru/rss/news/"),
            vision_provider=os.getenv("VISION_PROVIDER", "openai"),
            vision_model=os.getenv("VISION_MODEL", "gpt-4o"),
            feature_news_alerts=os.getenv("FEATURE_NEWS_ALERTS", "1") == "1",
            feature_analysis_v13=os.getenv("FEATURE_ANALYSIS_V13", "1") == "1",
            feature_analysis_v14=os.getenv("FEATURE_ANALYSIS_V14", "1") == "1",
            feature_ocr_v2=os.getenv("FEATURE_OCR_V2", "1") == "1",
            feature_ocr_v3=os.getenv("FEATURE_OCR_V3", "1") == "1",
            database_url=os.getenv("DATABASE_URL", "sqlite:///radar_bot.db"),
            cache_ttl=int(os.getenv("CACHE_TTL", "300")),
        )

    def validate(self) -> None:
        missing = [field for field in ["telegram_bot_token", "openai_api_key", "tin_token"] if not getattr(self, field)]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")


config = Config.from_env()
"""应用配置：仅从 backend/config.env 读取，禁止硬编码密钥。"""
import os

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ 根目录（本文件位于 backend/app/core/config.py）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, "config.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # 应用
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8003
    CORS_ORIGINS: str = "http://127.0.0.1:3003,http://localhost:3003"

    # 数据库
    DATABASE_URL: str = "sqlite:///./data/xunmeng.db"

    # 阶跃星辰。文本与图像共用同一把服务端密钥。
    STEPFUN_API_BASE: str = "https://api.stepfun.com/step_plan/v1"
    STEPFUN_API_KEY: str = ""
    LLM_MODEL: str = "step-3.5-flash"
    IMAGE_MODEL: str = "step-image-edit-2"

    # 默认内置账号（网站自带，可直接登录体验；留空则不创建）
    DEFAULT_USERNAME: str = ""
    DEFAULT_PASSWORD: str = ""

    # 语音合成（可选）
    TTS_API_BASE_URL: str = ""
    TTS_API_KEY: str = ""
    TTS_VOICE: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def api_key(self) -> str:
        """仅返回阶跃星辰密钥，禁止从前端或源码读取。"""
        return self.STEPFUN_API_KEY.strip()

    @property
    def image_model(self) -> str:
        return self.IMAGE_MODEL.strip()

    @property
    def ai_enabled(self) -> bool:
        """填了 API Key 即启用真实生成；否则走降级/占位模式（仍可演示）。"""
        return bool(self.api_key)


settings = Settings()

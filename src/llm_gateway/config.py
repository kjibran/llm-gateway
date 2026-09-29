from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str = ""
    groq_api_key: str = ""
    openrouter_api_key: str = ""

    gemini_model: str = ""
    groq_model: str = ""
    openrouter_model: str = ""

    request_timeout: float = 30.0

    gateway_api_key: str = ""


settings = Settings()

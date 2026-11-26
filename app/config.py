from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "AutoReel AI"
    secret_key: str = "change-me"
    database_url: str = "sqlite:///./autoreel.db"
    cookie_secure: bool = False
    public_base_url: str = "http://localhost:8000"
    storage_dir: str = "./storage"
    instagram_publish_enabled: bool = False
    meta_api_version: str = "v24.0"
    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_redirect_uri: str = "http://localhost:8000/api/instagram/callback"
    ai_provider: str = "mock"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
settings = Settings()


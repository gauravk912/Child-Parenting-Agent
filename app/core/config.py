from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TinyTriggers"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Supabase project settings
    supabase_url: str = ""
    supabase_key: str = ""

    # Supabase Postgres connection fields
    supabase_db_host: str = ""
    supabase_db_port: int = 5432
    supabase_db_name: str = "postgres"
    supabase_db_user: str = "postgres"
    supabase_db_password: str = ""

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "password"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    auth_secret_key: str = "change-me-in-env"
    auth_algorithm: str = "HS256"
    auth_access_token_expire_minutes: int = 60

    # OpenAI + Tavily
    openai_api_key: str = ""
    openai_model: str = "gpt-5.4-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    tavily_api_key: str = ""
    enable_live_evidence_search: bool = True

    # Weather
    openweather_api_key: str = ""
    default_weather_location: str = "Columbus,OH,US"
    weather_units: str = "imperial"

    # Local calendar
    local_calendar_data_file: str = "data/calendar_events.json"

    # Phase 2 MCP-style toggles
    enable_mcp_weather_adapter: bool = True
    enable_mcp_calendar_adapter: bool = True
    
    local_vector_store_file: str = "data/processed/vector_store.json"
    
    local_notification_store_file: str = "data/processed/notifications.json"
    notification_high_risk_threshold: float = 0.75
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.supabase_db_user}:"
            f"{self.supabase_db_password}@{self.supabase_db_host}:"
            f"{self.supabase_db_port}/{self.supabase_db_name}"
        )


settings = Settings()
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
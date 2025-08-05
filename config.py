"""Config reader for ts-cf-dns."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Define the settings we need."""

    CLOUDFLARE_API_KEY: str
    CLOUDFLARE_ZONE_ID: str
    DNS_DOMAIN: str

    class Config:
        """Define our settings file."""
        env_file = ".env"


settings = Settings()

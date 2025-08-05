"""Config reader for ts-cf-dns."""

from pydantic_settings import BaseSettings
from pydantic import field_validator, Field



class Settings(BaseSettings):
    """Define the settings we need."""
    TS_AUTH_KEY: str
    TAILSCALE_TAILNET: str
    TAILSCALE_IGNORE_HOSTNAMES: str | None = None
    CLOUDFLARE_API_KEY: str
    CLOUDFLARE_ZONE_ID: str
    DNS_DOMAIN: str

    class Config:
        """Define our settings file."""
        env_file = ".env"


settings = Settings()

# Process the ignore list string into a set for efficient lookup
TAILSCALE_IGNORED_HOSTNAMES_SET: set[str] = set()
if settings.TAILSCALE_IGNORE_HOSTNAMES:
    TAILSCALE_IGNORED_HOSTNAMES_SET = {
        name.strip() for name in settings.TAILSCALE_IGNORE_HOSTNAMES.split(',') if name.strip()
    }
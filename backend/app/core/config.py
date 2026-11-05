from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Adaptive Zero Trust IAM"
    APP_VERSION: str = "1.0.0"

    APP_ENV: Literal["development", "demo", "production"] = "development"
    DEBUG: bool = True

    DATABASE_HOST: str = "127.0.0.1"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "zero_trust_iam"

    DATABASE_USER: str = "iam_app"
    DATABASE_PASSWORD: str = Field(
        validation_alias="IAM_APP_PASSWORD"
    )

    MIGRATOR_DATABASE_USER: str = "iam_migrator"
    MIGRATOR_DATABASE_PASSWORD: str = Field(
        validation_alias="IAM_MIGRATOR_PASSWORD"
    )

    KEYCLOAK_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "adaptive-iam"
    KEYCLOAK_API_CLIENT_ID: str = "adaptive-iam-api"

    GEOIP_DATABASE_PATH: str = "data/geolocation/GeoLite2-City.mmdb"
    GEOIP_ENABLED: bool = True
    REVERSE_GEOCODER_USER_AGENT: str = "AdaptiveZeroTrustIAM/1.0"

    DEMO_LOCATION_SIMULATION_ENABLED: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_environment(self):
        if self.APP_ENV == "production":
            self.DEBUG = False
            self.DEMO_LOCATION_SIMULATION_ENABLED = False

        if (
            self.DEMO_LOCATION_SIMULATION_ENABLED
            and self.APP_ENV != "demo"
        ):
            raise ValueError(
                "Location simulation is permitted only in demo environment."
            )

        return self

    @property
    def keycloak_issuer(self) -> str:
        return (
            f"{self.KEYCLOAK_URL}/realms/"
            f"{self.KEYCLOAK_REALM}"
        )

    @property
    def keycloak_jwks_url(self) -> str:
        return f"{self.keycloak_issuer}/protocol/openid-connect/certs"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
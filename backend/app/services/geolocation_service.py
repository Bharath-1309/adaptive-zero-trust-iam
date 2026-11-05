import ipaddress
from pathlib import Path
from typing import Any

import geoip2.database
import geoip2.errors

from app.core.config import settings


class GeolocationService:

    def __init__(self, database_path: str | None = None):
        self.database_path = Path(
            database_path or settings.GEOIP_DATABASE_PATH
        )
        self.reader = None

        if not settings.GEOIP_ENABLED:
            return

        if not self.database_path.is_file():
            raise FileNotFoundError(
                f"GeoLite2 database not found: {self.database_path}"
            )

        self.reader = geoip2.database.Reader(
            str(self.database_path)
        )

    @staticmethod
    def validate_ip_address(ip_address: str) -> str:
        try:
            address = ipaddress.ip_address(ip_address.strip())
        except (ValueError, AttributeError):
            raise ValueError("Invalid IP address.")

        if not address.is_global:
            raise ValueError(
                "Private, reserved or non-public IP addresses "
                "cannot be geolocated."
            )

        return str(address)

    def lookup(self, ip_address: str) -> dict[str, Any] | None:
        if self.reader is None:
            raise RuntimeError("GeoIP geolocation is disabled.")

        validated_ip = self.validate_ip_address(ip_address)

        try:
            response = self.reader.city(validated_ip)
        except geoip2.errors.AddressNotFoundError:
            return None

        country = response.country
        subdivisions = response.subdivisions
        city = response.city
        location = response.location

        return {
            "source": "IP_GEOIP",
            "country_code": country.iso_code,
            "country_name": country.name,
            "region": (
                subdivisions.most_specific.name
                if subdivisions
                else None
            ),
            "city": city.name,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "accuracy_meters": (
                location.accuracy_radius * 1000
                if location.accuracy_radius is not None
                else None
            ),
        }

    def close(self) -> None:
        if self.reader is not None:
            self.reader.close()
            self.reader = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
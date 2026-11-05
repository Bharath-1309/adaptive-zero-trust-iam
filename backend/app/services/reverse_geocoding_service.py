import time
from threading import Lock
from typing import Any

import httpx

from app.core.config import settings


class ReverseGeocodingService:
    BASE_URL = "https://nominatim.openstreetmap.org/reverse"

    CACHE_TTL_SECONDS = 86400

    _cache: dict[tuple[float, float], tuple[float, dict[str, Any]]] = {}
    _lock = Lock()
    _last_request_time = 0.0

    def reverse_lookup(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any] | None:

        if not -90 <= latitude <= 90:
            raise ValueError("Invalid latitude.")

        if not -180 <= longitude <= 180:
            raise ValueError("Invalid longitude.")

        cache_key = (
            round(latitude, 4),
            round(longitude, 4),
        )

        with self._lock:
            cached = self._cache.get(cache_key)

            if cached:
                timestamp, result = cached

                if time.monotonic() - timestamp < self.CACHE_TTL_SECONDS:
                    return result.copy()

                del self._cache[cache_key]

            elapsed = time.monotonic() - self._last_request_time

            if elapsed < 1:
                time.sleep(1 - elapsed)

            try:
                response = httpx.get(
                    self.BASE_URL,
                    params={
                        "lat": latitude,
                        "lon": longitude,
                        "format": "jsonv2",
                        "addressdetails": 1,
                        "zoom": 10,
                    },
                    headers={
                        "User-Agent": settings.REVERSE_GEOCODER_USER_AGENT,
                    },
                    timeout=10,
                )

                self._last_request_time = time.monotonic()

                response.raise_for_status()

                data = response.json()

            except (httpx.HTTPError, ValueError):
                return None

            address = data.get("address", {})

            city = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("municipality")
                or address.get("county")
            )

            region = (
                address.get("state")
                or address.get("state_district")
                or address.get("region")
            )

            country = address.get("country")

            if not country:
                return None

            result = {
                "city": city,
                "region": region,
                "country_name": country,
                "country_code": (
                    address.get("country_code", "").upper() or None
                ),
            }

            self._cache[cache_key] = (
                time.monotonic(),
                result,
            )

            return result.copy()
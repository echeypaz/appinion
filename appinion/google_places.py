"""Integración sencilla con Google Places para obtener reseñas dinámicas."""
from __future__ import annotations

import time
from typing import List, Optional

import requests

from .aggregator import ServiceOption

PLACES_TEXTSEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"

# Mapeo heurístico de los niveles de precio de Google (0-4) a importes aproximados.
PRICE_LEVEL_TO_AMOUNT = {
    0: 1.0,   # gratuito
    1: 15.0,  # económico
    2: 40.0,  # medio
    3: 75.0,  # alto
    4: 150.0,  # muy alto
}


def price_from_level(price_level: Optional[int]) -> Optional[float]:
    """Convierte el nivel de precio de Google en una cantidad aproximada."""

    if price_level is None:
        return None
    return PRICE_LEVEL_TO_AMOUNT.get(price_level)


def build_notes(place: dict) -> Optional[str]:
    components = []
    if formatted_address := place.get("formatted_address"):
        components.append(formatted_address)
    price_level = place.get("price_level")
    if price_level is not None:
        components.append(f"Nivel de precio Google: {price_level}")
    if not components:
        return None
    return " · ".join(components)


def fetch_service_options(
    *,
    service: str,
    location: Optional[str],
    api_key: str,
    language: str = "es",
    max_results: int = 20,
    currency: str = "EUR",
) -> List[ServiceOption]:
    """Obtiene proveedores desde Google Places Text Search."""

    session = requests.Session()
    results: List[ServiceOption] = []
    next_page_token: Optional[str] = None
    query = service if not location else f"{service} en {location}"

    while len(results) < max_results:
        params = {"key": api_key, "language": language}
        if next_page_token:
            params["pagetoken"] = next_page_token
        else:
            params["query"] = query

        response = session.get(PLACES_TEXTSEARCH_URL, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()

        status = payload.get("status")
        if status == "ZERO_RESULTS":
            break
        if status != "OK":
            error_message = payload.get("error_message") or status or "Error desconocido"
            raise RuntimeError(f"Error de la API de Google Places: {error_message}")

        for place in payload.get("results", []):
            rating = place.get("rating")
            review_count = place.get("user_ratings_total")
            if rating is None or review_count is None:
                continue

            price_level = place.get("price_level")
            price = price_from_level(price_level)
            option = ServiceOption(
                service=service,
                provider=place.get("name", "Proveedor sin nombre"),
                rating=float(rating),
                review_count=int(review_count),
                price=price,
                currency=currency if price is not None else None,
                pricing_unit="aprox. (nivel Google)" if price is not None else None,
                link=f"https://www.google.com/maps/place/?q=place_id:{place['place_id']}"
                if place.get("place_id")
                else None,
                notes=build_notes(place),
            )
            results.append(option)

            if len(results) >= max_results:
                break

        next_page_token = payload.get("next_page_token")
        if not next_page_token:
            break

        # La API requiere esperar un breve periodo antes de usar el token de la siguiente página.
        time.sleep(2)

    return results


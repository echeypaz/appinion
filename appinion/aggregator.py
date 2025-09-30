"""Herramientas para comparar proveedores de servicios basándose en reseñas de Google."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence


@dataclass(frozen=True)
class ServiceOption:
    """Representa una alternativa de servicio obtenida de reseñas de Google."""

    service: str
    provider: str
    rating: float
    review_count: int
    price: Optional[float] = None
    currency: Optional[str] = None
    pricing_unit: Optional[str] = None
    link: Optional[str] = None
    notes: Optional[str] = None

    def display_name(self) -> str:
        """Nombre amigable para mostrar."""

        return f"{self.provider} ({self.service})"


class ServiceRepository:
    """Gestiona y consulta las opciones disponibles para cada servicio."""

    def __init__(self, options: Sequence[ServiceOption]):
        self._options: List[ServiceOption] = list(options)
        self._index = {}
        for option in self._options:
            normalized = _normalize_service_name(option.service)
            self._index.setdefault(normalized, []).append(option)

    def services(self) -> List[str]:
        """Devuelve una lista con los servicios disponibles."""

        return sorted({option.service for option in self._options})

    def for_service(self, service: str) -> List[ServiceOption]:
        """Obtiene todas las opciones de un servicio específico."""

        normalized = _normalize_service_name(service)
        return sorted(
            self._index.get(normalized, []),
            key=lambda option: (
                -option.rating,
                -option.review_count,
                option.price if option.price is not None else float("inf"),
            ),
        )


def best_rated(options: Iterable[ServiceOption]) -> Optional[ServiceOption]:
    """Devuelve la mejor opción valorada."""

    return _best_option(
        options,
        key=lambda option: (
            option.rating,
            option.review_count,
            -option.price if option.price is not None else float("-inf"),
        ),
    )


def cheapest(options: Iterable[ServiceOption]) -> Optional[ServiceOption]:
    """Devuelve la opción más económica."""

    priced_options = [option for option in options if option.price is not None]
    if not priced_options:
        return None

    return min(
        priced_options,
        key=lambda option: (option.price, -option.rating, -option.review_count),
    )


def best_value(options: Iterable[ServiceOption]) -> Optional[ServiceOption]:
    """Calcula la mejor relación calidad-precio usando una métrica ponderada simple."""

    priced_options = [option for option in options if option.price is not None and option.price > 0]
    if not priced_options:
        return best_rated(options)

    def value(option: ServiceOption) -> float:
        # Usa una métrica intuitiva: mayor rating y mayor número de reseñas mejoran el valor,
        # mientras que un precio más bajo lo incrementa.
        engagement_factor = 1 + (option.review_count / 100)
        return option.rating * engagement_factor / option.price

    return _best_option(
        priced_options,
        key=lambda option: (value(option), option.rating, option.review_count),
    )


def _best_option(options: Iterable[ServiceOption], key) -> Optional[ServiceOption]:
    iterable = list(options)
    if not iterable:
        return None

    return max(iterable, key=key)


def _normalize_service_name(service: str) -> str:
    return service.strip().lower()

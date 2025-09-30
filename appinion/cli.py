"""Interfaz de línea de comandos para comparar opciones de servicios."""
from __future__ import annotations

import argparse
import json
import os
from importlib import resources
from typing import Iterable, List, Optional

from .aggregator import ServiceOption, ServiceRepository, best_rated, best_value, cheapest


def load_options_from_path(data_path: str) -> List[ServiceOption]:
    """Carga las opciones disponibles desde un archivo JSON externo."""

    with open(data_path, "r", encoding="utf-8") as file:
        raw_data = json.load(file)
    return [ServiceOption(**item) for item in raw_data]


def load_packaged_options() -> List[ServiceOption]:
    """Carga los datos de ejemplo empaquetados con la librería."""

    with resources.files("appinion.data").joinpath("services.json").open("r", encoding="utf-8") as file:
        raw_data = json.load(file)
    return [ServiceOption(**item) for item in raw_data]


def format_currency(price: float, currency: Optional[str]) -> str:
    if not currency:
        return f"{price:,.2f}".replace(",", ".")

    symbol_map = {
        "EUR": "€",
        "USD": "$",
        "MXN": "$",
        "COP": "$",
    }
    symbol = symbol_map.get(currency.upper(), currency.upper())
    return f"{price:,.2f} {symbol}".replace(",", ".")


def describe_price(option: ServiceOption) -> Optional[str]:
    if option.price is None:
        return None

    base = format_currency(option.price, option.currency)
    if option.pricing_unit:
        return f"{base} {option.pricing_unit}"
    return base


def render_service_summary(options: Iterable[ServiceOption]) -> str:
    options = list(options)
    if not options:
        return "No se encontraron opciones para este servicio."

    best = best_rated(options)
    cheap = cheapest(options)
    value = best_value(options)

    lines = ["Resumen rápido:"]
    if best:
        price_text = describe_price(best)
        price_part = f" por {price_text}" if price_text else ""
        lines.append(
            f"  ⭐ Mejor valorado: {best.provider} - {best.rating:.1f} ⭐ ({best.review_count} reseñas){price_part}"
        )
    if cheap:
        price_text = describe_price(cheap)
        price_part = f" - {price_text}" if price_text else ""
        lines.append(
            f"  💰 Más económico: {cheap.provider}{price_part} con {cheap.rating:.1f} ⭐"
        )
    if value:
        price_text = describe_price(value)
        price_part = f" por {price_text}" if price_text else ""
        lines.append(
            f"  ⚖️ Mejor relación calidad-precio: {value.provider} - {value.rating:.1f} ⭐{price_part}"
        )

    return "\n".join(lines)


def render_ranking(options: Iterable[ServiceOption], limit: int | None = None) -> str:
    options = list(options)
    if not options:
        return ""

    if limit:
        options = options[:limit]

    lines = ["\nRanking detallado:"]
    for index, option in enumerate(options, start=1):
        price_text = describe_price(option) or "Precio no disponible"
        lines.append(
            f"  {index}. {option.provider}: {option.rating:.1f} ⭐ ({option.review_count} reseñas) - {price_text}"
        )
        if option.notes:
            lines.append(f"     Nota: {option.notes}")
        if option.link:
            lines.append(f"     Ficha: {option.link}")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compara proveedores con base en reseñas y precios para encontrar la mejor opción."
    )
    parser.add_argument(
        "service",
        help="Servicio que quieres evaluar (por ejemplo, 'limpieza', 'mudanzas', 'fontanero').",
    )
    parser.add_argument(
        "--data",
        help="Ruta alternativa al archivo JSON con los datos de proveedores.",
    )
    parser.add_argument(
        "--use-sample",
        action="store_true",
        help="Utiliza los datos de ejemplo empaquetados en lugar de la API de Google.",
    )
    parser.add_argument(
        "--api-key",
        help="Clave de Google Places. Si no se indica, se toma de la variable GOOGLE_MAPS_API_KEY.",
    )
    parser.add_argument(
        "--location",
        help="Ciudad o zona donde quieres buscar el servicio (por ejemplo, 'Madrid, España').",
    )
    parser.add_argument(
        "--language",
        default="es",
        help="Idioma para la respuesta de Google Places (por defecto 'es').",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=20,
        help="Número máximo de resultados a solicitar a Google Places (por defecto 20).",
    )
    parser.add_argument(
        "--currency",
        default="EUR",
        help="Moneda a utilizar para la estimación de precios (por defecto EUR).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Número de resultados a mostrar en el ranking (por defecto 5).",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.data:
        options = load_options_from_path(args.data)
        repository = ServiceRepository(options)
        service_options = repository.for_service(args.service)
        if not service_options:
            available = ", ".join(repository.services())
            message = "No encontramos opciones para ese servicio."
            if available:
                message += f" Servicios disponibles: {available}."
            print(message)
            return
        service_name = service_options[0].service
    elif args.use_sample:
        options = load_packaged_options()
        repository = ServiceRepository(options)
        service_options = repository.for_service(args.service)
        if not service_options:
            available = ", ".join(repository.services())
            message = "No encontramos opciones para ese servicio en los datos de ejemplo."
            if available:
                message += f" Servicios disponibles: {available}."
            print(message)
            return
        service_name = service_options[0].service
    else:
        from .google_places import fetch_service_options

        api_key = args.api_key or os.getenv("GOOGLE_MAPS_API_KEY")
        if not api_key:
            print("Debes proporcionar una clave de Google Places mediante --api-key o la variable GOOGLE_MAPS_API_KEY.")
            return

        service_options = fetch_service_options(
            service=args.service,
            location=args.location,
            api_key=api_key,
            language=args.language,
            max_results=args.max_results,
            currency=args.currency,
        )

        if not service_options:
            print("Google Places no devolvió resultados para esa búsqueda. Prueba con otro término o ubicación.")
            return

        service_name = args.service

    print(f"Comparativa para: {service_name}\n")
    print(render_service_summary(service_options))
    print(render_ranking(service_options, args.top))


if __name__ == "__main__":  # pragma: no cover
    main()

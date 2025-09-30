# Appinion

Aplicación de línea de comandos para comparar alternativas de servicios utilizando calificaciones y precios recopilados en tiempo real desde Google Places. Permite identificar rápidamente la opción mejor valorada, la más económica y la que ofrece mejor relación calidad-precio dentro de un mismo tipo de servicio.

## Requisitos

- Python 3.10 o superior.
- Una clave válida de Google Places API.
- Dependencias de Python: `requests`.

## Instalación

1. (Opcional) Crea y activa un entorno virtual.
2. Instala las dependencias necesarias:

```bash
pip install -r requirements.txt
```

3. Configura tu clave de Google Places como variable de entorno (o proporciónala al ejecutar el comando):

```bash
export GOOGLE_MAPS_API_KEY="tu_clave_de_google"
```

## Uso

Ejecuta el módulo principal indicando el servicio y opcionalmente la ubicación en la que quieres realizar la búsqueda:

```bash
python -m appinion.cli "Limpieza del hogar" --location "Madrid, España"
```

El comando consultará Google Places en tiempo real, calculará las mejores opciones según valoración, precio aproximado y relación calidad-precio, y mostrará el resultado en consola.

### Ejecución con Docker

Si prefieres no instalar Python localmente, puedes construir una imagen de Docker y ejecutar la CLI dentro del contenedor:

```bash
docker build -t appinion .
docker run --rm appinion "Limpieza del hogar" --use-sample
```

La imagen utiliza el módulo `appinion.cli` como punto de entrada, por lo que puedes pasar los mismos argumentos que usarías en la línea de comandos.

### Opciones adicionales

- `--top N`: controla cuántos proveedores se muestran en el ranking (por defecto 5).
- `--location`: define la zona de búsqueda (por ejemplo, `--location "Barcelona, España"`).
- `--language`: idioma para la información devuelta por Google (por defecto `es`).
- `--max-results`: número máximo de resultados a solicitar a Google Places (por defecto 20).
- `--currency`: moneda que se utilizará para estimar el coste basado en el nivel de precio de Google.
- `--api-key`: permite indicar la clave de Google Places manualmente. Si no se proporciona, se utiliza `GOOGLE_MAPS_API_KEY`.
- `--data ruta`: permite usar un archivo JSON alternativo con información de proveedores.
- `--use-sample`: utiliza los datos de ejemplo empaquetados en lugar de consultar la API.

## Estructura del archivo de datos

El archivo `appinion/data/services.json` incluye ejemplos de proveedores con la siguiente estructura:

```json
{
  "service": "Limpieza del hogar",
  "provider": "Brillo Express",
  "rating": 4.8,
  "review_count": 215,
  "price": 32.0,
  "currency": "EUR",
  "pricing_unit": "por hora",
  "link": "https://maps.google.com/?cid=1234567890",
  "notes": "Incluye productos ecológicos"
}
```

Puedes ampliar el archivo con tus propios datos exportados desde Google o elaborados manualmente siguiendo el mismo formato.

> **Nota:** cuando se consulta Google Places, el campo `price` se deriva del `price_level` devuelto por la API, utilizando una conversión heurística para poder comparar opciones (por ejemplo, niveles 0-4 se transforman en importes estimados). Siempre revisa la ficha original para conocer precios exactos.

## Ejemplo de salida

```
Comparativa para: Limpieza del hogar

Resumen rápido:
  ⭐ Mejor valorado: Servicio A - 4.7 ⭐ (180 reseñas) por 40.00 € aprox. (nivel Google)
  💰 Más económico: Servicio B - 15.00 € aprox. (nivel Google) con 4.2 ⭐
  ⚖️ Mejor relación calidad-precio: Servicio A - 4.7 ⭐ por 40.00 € aprox. (nivel Google)

Ranking detallado:
  1. Servicio A: 4.7 ⭐ (180 reseñas) - 40.00 € aprox. (nivel Google)
     Nota: Calle Ejemplo 123 · Nivel de precio Google: 2
     Ficha: https://www.google.com/maps/place/?q=place_id:XXXXX
  2. Servicio B: 4.2 ⭐ (75 reseñas) - 15.00 € aprox. (nivel Google)
```

> **Importante:** la salida anterior es ilustrativa; al ejecutar el comando con tu clave y ubicación obtendrás resultados reales procedentes de Google.

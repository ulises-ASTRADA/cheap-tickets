"""
Cliente de la Travelpayouts (Aviasales) Data API.
Doc: https://support.travelpayouts.com/hc/en-us/articles/203956163

Nota importante: los datos vienen de una CACHE (búsquedas reales de usuarios de
Aviasales en los últimos días), no de un shopping en vivo. Eso significa:
  - No vas a ver TODOS los vuelos posibles, solo lo que la gente buscó.
  - Para rutas populares (EZE->MAD, SCL->MIA) hay mucha data. Para rutas raras, poca.
  - Es gratis e ilimitado en la práctica, ideal para correr cada pocas horas.
Para validar un precio antes de comprar, siempre abrí el link real.
"""
import requests

from . import config

BASE = "http://api.travelpayouts.com"


def _headers():
    return {"X-Access-Token": config.TP_TOKEN}


def get_latest_prices(origin, destination=None):
    """
    Trae las tarifas más baratas cacheadas para un origen (y destino opcional).
    Devuelve lista de dicts normalizados.
    """
    params = {
        "currency": config.CURRENCY,
        "origin": origin,
        "period_type": "year",
        "one_way": "false",
        "page": 1,
        "limit": 1000,
        "show_to_affiliates": "true",
        "sorting": "price",
        "token": config.TP_TOKEN,
    }
    if destination:
        params["destination"] = destination

    url = f"{BASE}/aviasales/v3/get_latest_prices"
    try:
        r = requests.get(url, params=params, headers=_headers(),
                         timeout=config.REQUEST_TIMEOUT)
        r.raise_for_status()
        payload = r.json()
    except (requests.RequestException, ValueError) as e:
        print(f"  [!] Error consultando {origin}->{destination or '*'}: {e}")
        return []

    if not payload.get("success"):
        return []

    out = []
    for row in payload.get("data", []):
        out.append({
            "origin": row.get("origin", origin),
            "destination": row.get("destination"),
            "price": row.get("value"),
            "airline": row.get("airline", ""),
            "depart_date": row.get("depart_date"),
            "return_date": row.get("return_date"),
            "one_way": not row.get("return_date"),
        })
    return out


def search_link(origin, destination, depart_date, return_date=None):
    """
    Construye el link de Aviasales para abrir la búsqueda real.
    Formato: ORIGENddmmDESTINO[ddmm], ej EZE1208MAD2008
    """
    def fmt(d):
        # d viene como 'YYYY-MM-DD'
        try:
            y, m, day = d.split("-")
            return f"{day}{m}"
        except (ValueError, AttributeError):
            return ""

    seg = f"{origin}{fmt(depart_date)}{destination}"
    if return_date:
        seg += fmt(return_date)
    marker = config.TP_TOKEN[:6] if config.TP_TOKEN else ""
    return f"https://www.aviasales.com/search/{seg}1?marker={marker}"

"""
Scraper de EMPTY LEGS (tramos vacíos de vuelos privados).
Esto NO está en ninguna API de líneas comerciales. Son operadores de jets privados
que reposicionan aviones vacíos y venden esos asientos a precio de descuento.

Realidad: cada operador tiene su propio sitio. Acá te dejo el esqueleto con
Playwright (maneja JS/Cloudflare mejor que requests) y un parser de ejemplo.
Vas a tener que ajustar los selectores CSS a cada sitio que elijas.

Operadores con empty legs públicos para Sudamérica / vuelos desde/hacia AR-CL:
  - Catarata / Baires Fly (charter regional)
  - Flapper (Brasil, fuerte en Sudamérica)
  - Algunos brokers internacionales (Victor, GlobeAir) listan tramos hacia/desde EZE

INSTALAR:  pip install playwright && playwright install chromium

Este módulo es opcional y artesanal: arranca con la API comercial (main.py),
y sumá esto cuando quieras cazar empty legs.
"""
from . import notifier

# Configurá acá los sitios a scrapear. Cada uno necesita su parser propio.
EMPTY_LEG_SOURCES = [
    # {
    #     "name": "Flapper",
    #     "url": "https://www.flapper.aero/en/empty-legs",
    #     "row_selector": ".empty-leg-card",
    #     "from_selector": ".route-origin",
    #     "to_selector": ".route-dest",
    #     "price_selector": ".price",
    #     "date_selector": ".date",
    # },
]

# Filtrá por aeropuertos relevantes (los mismos del config principal + ciudades)
RELEVANT_AIRPORTS = {"COR", "EZE", "AEP", "SCL", "Cordoba", "Buenos Aires", "Santiago"}


def scrape():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[!] Playwright no instalado. Corré: pip install playwright && playwright install chromium")
        return []

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ))
        for src in EMPTY_LEG_SOURCES:
            try:
                page.goto(src["url"], timeout=45000, wait_until="networkidle")
                cards = page.query_selector_all(src["row_selector"])
                for c in cards:
                    def txt(sel):
                        el = c.query_selector(sel)
                        return el.inner_text().strip() if el else ""
                    leg = {
                        "source": src["name"],
                        "from": txt(src["from_selector"]),
                        "to": txt(src["to_selector"]),
                        "price": txt(src["price_selector"]),
                        "date": txt(src["date_selector"]),
                    }
                    if _is_relevant(leg):
                        results.append(leg)
            except Exception as e:
                print(f"  [!] Error scrapeando {src['name']}: {e}")
        browser.close()
    return results


def _is_relevant(leg):
    blob = f"{leg['from']} {leg['to']}".lower()
    return any(a.lower() in blob for a in RELEVANT_AIRPORTS)


def run():
    legs = scrape()
    for leg in legs:
        notifier.send(
            f"🛩️ <b>EMPTY LEG</b> ({leg['source']})\n\n"
            f"<b>{leg['from']} → {leg['to']}</b>\n"
            f"💵 {leg['price']}\n📅 {leg['date']}"
        )
    print(f"[ok] Empty legs relevantes: {len(legs)}")


if __name__ == "__main__":
    run()

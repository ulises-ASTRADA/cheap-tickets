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

INSTALAR:  pip install "playwright>=1.64.1" && playwright install chromium

SEGURIDAD (nov 2026): Playwright 1.64.1 trae Chromium 156.0.8078.4, anterior al
parche de Chrome del 27/10/2026 (156.0.8078.73, 4 CVE críticos). Hasta que salga
una versión de Playwright con Chromium parcheado, apuntá PLAYWRIGHT_CHROMIUM_EXECUTABLE
a un Chrome for Testing >= 156.0.8078.80. El navegador corre sin sesiones ni cookies
guardadas y solo puede navegar a los dominios de EMPTY_LEG_SOURCES.

Este módulo es opcional y artesanal: arranca con la API comercial (main.py),
y sumá esto cuando quieras cazar empty legs.
"""
import os
from urllib.parse import urlparse

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
    allowed_hosts = {urlparse(src["url"]).hostname for src in EMPTY_LEG_SOURCES}
    launch_kwargs = {"headless": True}
    # Chromium parcheado opcional (ver SEGURIDAD arriba).
    chromium_exe = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
    if chromium_exe:
        launch_kwargs["executable_path"] = chromium_exe
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        # Contexto efímero: sin storage_state, sin perfil persistente, sin descargas.
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
            accept_downloads=False,
            service_workers="block",
        )
        context.route("**/*", lambda route: _guard_navigation(route, allowed_hosts))
        page = context.new_page()
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
        context.close()
        browser.close()
    return results


def _guard_navigation(route, allowed_hosts):
    """Bloquea navegaciones de página principal fuera de los sitios configurados."""
    req = route.request
    if (
        req.is_navigation_request()
        and req.frame.parent_frame is None
        and urlparse(req.url).hostname not in allowed_hosts
    ):
        return route.abort()
    return route.continue_()


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

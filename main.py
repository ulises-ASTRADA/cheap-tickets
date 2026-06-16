"""
Flight deals scraper — punto de entrada.

Flujo:
  1. Por cada origen (COR, EZE, AEP, SCL) trae precios cacheados de Travelpayouts.
  2. Guarda cada precio en el histórico (SQLite).
  3. Compara contra la mediana histórica de esa ruta.
  4. Si el precio cae >= DROP_THRESHOLD bajo la mediana -> es un DEAL -> alerta Telegram.

Correlo cada 3-6 horas con cron/APScheduler. Las primeras corridas NO van a
alertar nada: primero necesita juntar histórico para que la mediana tenga sentido.

Uso:
    export TP_TOKEN="..."
    export TELEGRAM_TOKEN="..."
    export TELEGRAM_CHAT_ID="..."
    python -m scraper.main            # corrida única
    python -m scraper.main --loop     # loop interno cada N horas
"""
import argparse
import time

from . import config, db, notifier, travelpayouts as tp


def _fingerprint(d):
    """Identificador único de una oferta puntual para no repetir alertas."""
    return f"{d['origin']}-{d['destination']}-{d['depart_date']}-{int(d['price'])}"


def evaluate_route(deal):
    """Devuelve (es_deal, mediana, descuento) para una tarifa."""
    price = deal["price"]
    if price is None or price < config.ABSOLUTE_FLOOR_USD:
        return False, None, 0.0

    median = db.median_price(deal["origin"], deal["destination"])
    if median is None or median <= 0:
        return False, median, 0.0  # todavía no hay histórico suficiente

    discount = 1 - (price / median)
    return discount >= config.DROP_THRESHOLD, median, discount


def format_alert(deal, median, discount):
    link = tp.search_link(deal["origin"], deal["destination"],
                          deal["depart_date"], deal["return_date"])
    trip = "ida" if deal["one_way"] else "ida y vuelta"
    return (
        f"✈️ <b>GANGA detectada</b>\n\n"
        f"<b>{deal['origin']} → {deal['destination']}</b> ({trip})\n"
        f"💵 <b>{deal['price']:.0f} {config.CURRENCY.upper()}</b>  "
        f"(mediana histórica: {median:.0f} → <b>-{discount*100:.0f}%</b>)\n"
        f"📅 Salida: {deal['depart_date']}"
        + (f" · Vuelta: {deal['return_date']}" if deal['return_date'] else "")
        + (f"\n🛫 Aerolínea: {deal['airline']}" if deal['airline'] else "")
        + f"\n\n🔗 {link}\n"
        f"<i>Validá el precio en el link antes de comprar (la data es de cache).</i>"
    )


def run_once():
    db.init_db()
    targets = config.DESTINATIONS or [None]  # None = todos los destinos
    found = 0
    scanned = 0

    for origin in config.ORIGINS:
        for dest in targets:
            rows = tp.get_latest_prices(origin, dest)
            for deal in rows:
                if not deal["destination"] or deal["price"] is None:
                    continue
                scanned += 1
                # 1) guardar histórico SIEMPRE (así la mediana mejora con el tiempo)
                db.record_price(
                    deal["origin"], deal["destination"], deal["price"],
                    deal["airline"], deal["depart_date"], deal["return_date"],
                    deal["one_way"],
                )
                # 2) evaluar si es ganga
                is_deal, median, discount = evaluate_route(deal)
                if not is_deal:
                    continue
                fp = _fingerprint(deal)
                if db.already_sent(fp):
                    continue
                notifier.send(format_alert(deal, median, discount))
                db.mark_sent(fp)
                found += 1
            time.sleep(1)  # cortesía con la API

    print(f"[ok] Escaneadas {scanned} tarifas. Gangas nuevas alertadas: {found}.")
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", action="store_true", help="correr en loop")
    parser.add_argument("--interval", type=int, default=4, help="horas entre corridas (loop)")
    args = parser.parse_args()

    if not config.TP_TOKEN:
        print("[!] Falta TP_TOKEN. Exportá la variable de entorno antes de correr.")
        return

    if args.loop:
        while True:
            run_once()
            print(f"[zzz] Durmiendo {args.interval}h...")
            time.sleep(args.interval * 3600)
    else:
        run_once()


if __name__ == "__main__":
    main()

# CLAUDE.md

Guía para trabajar en este repo con Claude Code. Leé esto antes de tocar código.

## Qué es

Detector de tarifas aéreas baratas y gangas desde **Córdoba (COR)**, **Buenos Aires (EZE/AEP)** y **Santiago de Chile (SCL)** hacia cualquier destino. Corre periódicamente, mantiene histórico de precios por ruta y alerta por Telegram cuando una tarifa cae muy por debajo de su mediana histórica.

Es un MVP en Python puro (sin frameworks). Prioriza simplicidad y correr en cron sin infraestructura.

## Cómo está estructurado

```
flight-deals/
├── CLAUDE.md              # este archivo
├── README.md             # guía de uso para el usuario final (setup tokens, correr)
├── requirements.txt       # requests (obligatorio), playwright (opcional)
└── scraper/
    ├── __init__.py        # paquete vacío
    ├── config.py          # TODA la configuración: orígenes, destinos, umbrales, credenciales
    ├── travelpayouts.py   # cliente de la API de Travelpayouts (fuente de datos principal)
    ├── db.py              # capa SQLite: histórico de precios + dedupe de alertas
    ├── notifier.py        # envío de alertas a Telegram (degrada a consola)
    ├── main.py            # orquestador + lógica de detección de gangas (entry point)
    └── empty_legs.py      # módulo OPCIONAL: scraping de empty legs con Playwright
```

## Flujo de datos (importante para entender el sistema)

```
main.run_once()
  └─ por cada ORIGIN × DESTINATION:
       1. travelpayouts.get_latest_prices()  → tarifas cacheadas
       2. db.record_price()                   → guarda SIEMPRE (alimenta el histórico)
       3. main.evaluate_route()               → compara precio vs db.median_price()
       4. si descuento ≥ DROP_THRESHOLD:
            - chequea db.already_sent() (dedupe por fingerprint)
            - notifier.send() + db.mark_sent()
```

**Punto clave:** el sistema guarda todos los precios SIEMPRE, sin importar si son ganga o no. Esa es la materia prima de la mediana. Por eso las primeras corridas no alertan: no hay histórico suficiente (`MIN_SAMPLES`).

## Decisiones de diseño que hay que respetar

- **Travelpayouts es la fuente principal**, no scraping de Google Flights/Skyscanner. Esos bloquean agresivamente (Cloudflare, fingerprinting). La API es gratis, estable y fuerte en LATAM. No la cambies por scraping de aerolíneas sin una razón muy buena.
- **La data de Travelpayouts es de CACHE**, no shopping en vivo: viene de búsquedas reales de usuarios de Aviasales de los últimos días. Implicancias:
  - No están todos los vuelos posibles, solo lo que se buscó.
  - Los precios pueden estar desactualizados → SIEMPRE se incluye el link real en la alerta para validar antes de comprar. No remover ese disclaimer.
- **Moneda en USD por default** (`config.CURRENCY`). Es deliberado: comparar histórico en ARS se distorsiona por inflación. No cambiar a ARS salvo pedido explícito.
- **Detección por mediana, no por promedio.** La mediana resiste outliers (un precio absurdo no rompe el umbral). Mantener `statistics.median`.
- **Dedupe por fingerprint** (`origin-dest-fecha-precio`) para no spamear la misma oferta. Si cambiás el criterio de fingerprint, vas a re-alertar ofertas viejas.
- **Endpoint vigente:** `http://api.travelpayouts.com/aviasales/v3/get_latest_prices`. Hubo versiones anteriores (`v1/prices/cheap`, `v2/prices/month-matrix`); si algo falla, verificar contra la doc oficial antes de asumir.

## Configuración (scraper/config.py)

Todo se ajusta acá. Credenciales por variables de entorno, nunca hardcodeadas:

- `TP_TOKEN` — token de Travelpayouts (obligatorio)
- `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` — para alertas (opcionales; sin ellos imprime en consola)
- `ORIGINS` — `["COR", "EZE", "AEP", "SCL"]`
- `DESTINATIONS` — `[]` significa "a donde sea"; listar IATA para más señal en rutas puntuales
- `DROP_THRESHOLD` — 0.40 (40% bajo la mediana = ganga)
- `MIN_SAMPLES` — 4 (mínimo histórico para evaluar una ruta)
- `ABSOLUTE_FLOOR_USD` — 30 (ignora ruidos absurdamente baratos)
- `DB_PATH` — ruta del SQLite

## Cómo correr

```bash
pip install -r requirements.txt
export TP_TOKEN="..." TELEGRAM_TOKEN="..." TELEGRAM_CHAT_ID="..."
python -m scraper.main            # corrida única
python -m scraper.main --loop --interval 4   # loop cada 4h
```

Para producción se usa cron (ver README). El `--loop` es para pruebas o procesos persistentes.

## Cómo probar cambios

No hay suite de tests formal todavía. Para validar la lógica de detección sin token real:

```python
from scraper import db, config
config.DB_PATH = "/tmp/test.db"
db.init_db()
for p in [800, 850, 820, 780, 900]:
    db.record_price("EZE", "MAD", p, "IB", "2026-08-10", "2026-08-25", False)
from scraper.main import evaluate_route
deal = {"origin":"EZE","destination":"MAD","price":420,"depart_date":"2026-08-10","return_date":"2026-08-25","one_way":False,"airline":"IB"}
print(evaluate_route(deal))  # → (True, 820.0, ~0.49)
```

Sin `TP_TOKEN`, `main.py` sale limpio con un aviso. Sin credenciales de Telegram, `notifier` imprime en consola. Ambos degradan sin romper — útil para probar.

## El módulo empty_legs (estado actual)

`empty_legs.py` es un **esqueleto incompleto a propósito**. Los empty legs (tramos vacíos de jets privados) no están en ninguna API comercial; cada operador tiene su sitio con su propio HTML. El módulo:
- Usa Playwright (maneja JS/Cloudflare mejor que requests).
- Tiene `EMPTY_LEG_SOURCES = []` vacío: hay que cargar cada operador con sus selectores CSS.
- Filtra por `RELEVANT_AIRPORTS`.

Si te piden trabajar acá: elegir operadores con empty legs públicos (Flapper es buena opción para Sudamérica), inspeccionar el HTML real y completar los selectores. No asumir que los selectores de ejemplo en los comentarios funcionan.

## Mejoras pendientes / ideas (si surgen)

- Reenvío automático desde canales de Telegram de error fares (Secret Flying, etc.) al mismo bot.
- Tests formales con pytest.
- Filtro por temporada / rango de fechas en la detección.
- Soporte multi-moneda con normalización a USD para el histórico.

## Convenciones

- Comentarios y mensajes al usuario en **español rioplatense** (es el contexto del proyecto).
- Sin dependencias pesadas innecesarias: requests para HTTP, sqlite3 de stdlib, Playwright solo para el módulo opcional.
- Credenciales NUNCA hardcodeadas: siempre `os.environ`.

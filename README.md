# Flight Deals Scraper 🛫

Detector de tarifas baratas y gangas desde **Córdoba (COR)**, **Buenos Aires (EZE/AEP)** y **Santiago de Chile (SCL)** hacia cualquier destino. Alertas por Telegram.

## Cómo funciona

1. Consulta la **Data API de Travelpayouts (Aviasales)** — gratis, basada en cache de búsquedas reales, fuerte en LATAM.
2. Guarda **histórico de precios** por ruta en SQLite.
3. Detecta **gangas**: cuando una tarifa cae ≥40% bajo la mediana histórica de esa ruta.
4. Te avisa por **Telegram** (sin repetir la misma oferta).

> ⚠️ Las primeras corridas no alertan nada: primero junta histórico para que la mediana sea confiable. Dejalo corriendo 1-2 días antes de esperar señales buenas.

## 1. Conseguir el token de Travelpayouts

1. Registrate gratis en https://www.travelpayouts.com (es una red de afiliados de viajes; el registro es libre).
2. Confirmá tu email e iniciá sesión.
3. Andá a **Tools → API** o directo a: https://www.travelpayouts.com/programs/100/tools/api
4. Copiá tu **API token** (también es tu "marker" de afiliado, así que si alguien compra desde tu link, cobrás comisión).

## 2. Conseguir el bot de Telegram

1. En Telegram, hablale a **@BotFather** → `/newbot` → seguí los pasos → te da un **TOKEN**.
2. Mandale cualquier mensaje a tu bot nuevo (buscalo por el username que elegiste).
3. Abrí en el navegador: `https://api.telegram.org/bot<TU_TOKEN>/getUpdates`
4. Copiá el número que aparece en `"chat":{"id": ...}` → ese es tu **CHAT_ID**.

## 3. Instalar y correr

```bash
pip install -r requirements.txt

export TP_TOKEN="tu_token_travelpayouts"
export TELEGRAM_TOKEN="tu_token_bot"
export TELEGRAM_CHAT_ID="tu_chat_id"

# Corrida única
python -m scraper.main

# Loop interno cada 4 horas
python -m scraper.main --loop --interval 4
```

Sin las variables de Telegram, las alertas se imprimen en consola (útil para probar).

## 4. Dejarlo corriendo (cron en Linux/Mac)

```bash
crontab -e
# cada 4 horas:
0 */4 * * * cd /ruta/flight-deals && TP_TOKEN=xxx TELEGRAM_TOKEN=xxx TELEGRAM_CHAT_ID=xxx /usr/bin/python3 -m scraper.main >> cron.log 2>&1
```

## 5. Ajustes (scraper/config.py)

| Parámetro | Qué hace |
|-----------|----------|
| `ORIGINS` | Aeropuertos de salida (ya configurado COR/EZE/AEP/SCL) |
| `DESTINATIONS` | `[]` = a donde sea. Listá IATA puntuales para más señal en rutas específicas |
| `DROP_THRESHOLD` | Cuánto bajo la mediana para considerar ganga (0.40 = 40%) |
| `MIN_SAMPLES` | Mínimo de precios históricos antes de evaluar una ruta |
| `CURRENCY` | `usd` recomendado (evita distorsión por inflación en ARS) |

## Empty legs (opcional, avanzado)

`scraper/empty_legs.py` es el esqueleto para cazar **tramos vacíos de jets privados** (no están en ninguna API comercial). Requiere Playwright y ajustar selectores CSS por cada operador:

```bash
pip install playwright && playwright install chromium
python -m scraper.empty_legs
```

## Límites honestos

- La data de Travelpayouts es de **cache** (búsquedas de otros usuarios), no shopping en vivo. **Siempre validá el precio en el link real antes de comprar.**
- Rutas populares (EZE→MAD, SCL→MIA) tienen mucha data; rutas raras, poca o nada.
- Los **error fares** verdaderos (errores de tarifa de aerolíneas) suelen durar horas y muchas veces ni aparecen en cache. Para esos, sumá seguir canales de Telegram tipo Secret Flying / Mejores Vuelos como complemento.
```

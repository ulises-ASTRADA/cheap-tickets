# Flight Deal Monitor

A Python automation project that watches cached flight prices from Córdoba, Buenos Aires, and Santiago, stores route history in SQLite, and sends Telegram alerts when a fare falls substantially below its historical median.

## How it works

```text
Travelpayouts / Aviasales cache → normalized fares → SQLite price history
                                                        ↓
                                            route median comparison
                                                        ↓
                                        deduplicated Telegram alerts
```

Default origins are `COR`, `EZE`, `AEP`, and `SCL`. A fare qualifies when it is at least 40% below its route median, the route has at least four observations, and the fare is at least USD 30. These values are configurable in `config.py`.

**Stack:** Python, Requests, SQLite, the standard-library statistics module, Travelpayouts/Aviasales, and the Telegram Bot API. An optional Playwright module provides a starting point for empty-leg scraping.

| Component | Responsibility |
| --- | --- |
| `main.py` | Orchestration, deal evaluation, alert formatting, and CLI loop |
| `travelpayouts.py` | API requests and fare normalization |
| `db.py` | Route history, median calculation, and alert fingerprints |
| `notifier.py` | Telegram delivery or console output |
| `config.py` | Environment configuration and detection thresholds |
| `empty_legs.py` | Optional scraper scaffold with no active sources configured |

## Run locally

The source uses relative imports. Clone into a valid Python package directory and run from its parent:

```bash
git clone https://github.com/ulises-ASTRADA/cheap-tickets.git cheap_tickets
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r cheap_tickets/requirements.txt

# Set TP_TOKEN in this shell using your own Travelpayouts credential.
python -m cheap_tickets.main
python -m cheap_tickets.main --loop --interval 4
```

| Environment variable | Purpose |
| --- | --- |
| `TP_TOKEN` | Required Travelpayouts API credential |
| `TELEGRAM_TOKEN` | Optional Telegram bot credential |
| `TELEGRAM_CHAT_ID` | Optional destination chat |
| `DB_PATH` | SQLite file location; defaults to `flights.db` in the working directory |

Without Telegram configuration, notifications are printed to the console. Keep credentials in the execution environment. Persist the database between scheduled runs so price history and deduplication survive restarts.

## Engineering considerations

The median provides a simple baseline without a model-training pipeline. SQLite keeps deployment small, and fingerprints avoid repeating the same route/date/integer-price alert. Runs can be scheduled externally or through the built-in loop.

This is a prototype using cached search data, not live airline inventory. Observations may repeat cached fares, and comparisons are grouped by route rather than travel season or cabin. New routes need a history warm-up. A detected discount is a heuristic; verify price and availability before booking.

There is no automated test suite in the repository. The empty-leg module requires optional Playwright installation, source configuration, and site-specific selectors before it can collect listings.

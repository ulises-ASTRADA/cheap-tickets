"""
Configuración del flight deals scraper.
Editá ORIGINS y DESTINATIONS a gusto. Todo en códigos IATA.
"""
import os

# --- Credenciales (poné estos valores en variables de entorno, no hardcodees) ---
TP_TOKEN = os.environ.get("TP_TOKEN", "")            # Travelpayouts API token
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")  # Bot token de @BotFather
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")  # Tu chat id

CURRENCY = "usd"   # usd, ars, etc. usd conviene para comparar histórico sin distorsión inflacionaria

# --- Aeropuertos de origen ---
# COR = Córdoba | EZE = Ezeiza | AEP = Aeroparque | SCL = Santiago de Chile
ORIGINS = ["COR", "EZE", "AEP", "SCL"]

# --- Destinos a vigilar. [] = todos los destinos que devuelva la cache ---
# Dejalo vacío para "a donde sea", o listá destinos puntuales para más señal.
DESTINATIONS = []   # ej: ["MAD", "MIA", "GRU", "MEX", "BCN", "CUN", "PUJ"]

# --- Lógica de detección de gangas ---
# Una tarifa se considera "deal" si está por debajo de la mediana histórica de esa ruta
# en al menos este porcentaje.
DROP_THRESHOLD = 0.40        # 40% bajo la mediana
MIN_SAMPLES = 4              # mínimo de precios históricos para que la mediana sea confiable
ABSOLUTE_FLOOR_USD = 30      # ignorar ruidos absurdamente baratos (tramos cortos, errores de cache)

# --- Operación ---
DB_PATH = os.environ.get("DB_PATH", "flights.db")
REQUEST_TIMEOUT = 20

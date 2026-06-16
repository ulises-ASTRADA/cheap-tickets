"""
Alertas por Telegram.
Setup rápido:
  1. Hablale a @BotFather en Telegram -> /newbot -> te da un TOKEN.
  2. Mandale un mensaje cualquiera a tu bot nuevo.
  3. Abrí https://api.telegram.org/bot<TOKEN>/getUpdates en el navegador
     y copiá el "id" que aparece en "chat". Ese es tu TELEGRAM_CHAT_ID.
"""
import requests

from . import config


def send(text):
    if not config.TELEGRAM_TOKEN or not config.TELEGRAM_CHAT_ID:
        print("  [!] Telegram no configurado, imprimo en consola:\n")
        print(text)
        return False

    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": config.TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }, timeout=config.REQUEST_TIMEOUT)
        r.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"  [!] Error enviando a Telegram: {e}")
        return False

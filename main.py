import time
import requests
from binance.client import Client
from datetime import datetime

# ── CONFIG ──────────────────────────────────────────────
BOT_TOKEN = "8731021434:AAEpdZJ-BTiEeY2fdPFn3XshyX0bKi0SI-g"
CHAT_ID   = "590265015"

WATCH_LIST = [
    "MOVEUSDT",
    "HUSDT",
    "LAYERUSDT",
    "ALLOTUSDT",
]

ALERT_THRESHOLD = 1.0   # Alert when price moves 1% or more in 1 minute
CHECK_INTERVAL  = 60    # Check every 60 seconds
COOLDOWN        = 300   # Don't repeat alert for same token within 5 mins
# ────────────────────────────────────────────────────────

client = Client()
price_cache  = {}
last_alerted = {}

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram error: {e}")

def get_futures_prices():
    tickers = client.futures_mark_price()
    return {t['symbol']: float(t['markPrice']) for t in tickers}

def check_movements():
    current_prices = get_futures_prices()
    now_str  = datetime.now().strftime("%H:%M:%S")
    now_ts   = time.time()

    for symbol in WATCH_LIST:
        if symbol not in current_prices:
            print(f"[WARNING] {symbol} not found on Binance Futures — check the ticker name!")
            continue

        current = current_prices[symbol]

        if symbol in price_cache:
            prev       = price_cache[symbol]
            change_pct = ((current - prev) / prev) * 100

            # Check cooldown — avoid spamming same token
            last_alert_time = last_alerted.get(symbol, 0)
            cooldown_ok     = (now_ts - last_alert_time) > COOLDOWN

            if abs(change_pct) >= ALERT_THRESHOLD and cooldown_ok:
                direction = "🚀 PUMP" if change_pct > 0 else "🔴 DUMP"
                emoji     = "📈" if change_pct > 0 else "📉"

                msg = (
                    f"{direction} <b>{symbol}</b> {emoji}\n"
                    f"━━━━━━━━━━━━━━━━\n"
                    f"Change : <b>{change_pct:+.2f}%</b> in 1 min\n"
                    f"Price  : <b>${current:,.6f}</b>\n"
                    f"Prev   : ${prev:,.6f}\n"
                    f"Time   : {now_str} SGT"
                )
                print(msg)
                send_telegram(msg)
                last_alerted[symbol] = now_ts

        price_cache[symbol] = current

    print(f"[{now_str}] ✅ Checked {len(WATCH_LIST)} pairs. Next check in {CHECK_INTERVAL}s...")

# ── STARTUP ──────────────────────────────────────────────
print("🤖 Kenny Price Alert Bot started!")
send_telegram(
    "🤖 <b>Price Alert Bot LIVE!</b>\n\n"
    "📋 Watching:\n"
    + "\n".join([f"• {s}" for s in WATCH_LIST])
    + f"\n\n⚡ Alert threshold: {ALERT_THRESHOLD}%/min"
)

while True:
    try:
        check_movements()
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(10)
    time.sleep(CHECK_INTERVAL)
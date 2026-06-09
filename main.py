import time
import requests
from datetime import datetime

# ── CONFIG ──────────────────────────────────────────────
BOT_TOKEN = "8731021434:AAEpdZJ-BTiEeY2fdPFn3XshyX0bKi0SI-g"   # Replace this
CHAT_ID   = "590265015"  

WATCH_LIST = [
    "MOVEUSDT",
    "HUSDT",
    "LAYERUSDT",
    "ALLOUSDT",
]

ALERT_THRESHOLD = 1.0   # Alert at 1% move within 1 minute
CHECK_INTERVAL  = 60    # Check every 60 seconds
COOLDOWN        = 300   # 5 min cooldown per token to avoid spam
# ────────────────────────────────────────────────────────

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
    prices = {}
    for symbol in WATCH_LIST:
        try:
            url = f"https://api.bybit.com/v5/market/tickers?category=linear&symbol={symbol}"
            response = requests.get(url, timeout=10)
            print(f"[DEBUG] {symbol} raw response: {response.text[:200]}")
            data = response.json()
            if data['retCode'] == 0 and data['result']['list']:
                price = float(data['result']['list'][0]['lastPrice'])
                prices[symbol] = price
            else:
                print(f"[WARNING] {symbol} not found on Bybit!")
        except Exception as e:
            print(f"[ERROR] fetching {symbol}: {e}")
    return prices

def check_movements():
    current_prices = get_futures_prices()
    now_str = datetime.now().strftime("%H:%M:%S")
    now_ts  = time.time()

    for symbol in WATCH_LIST:
        if symbol not in current_prices:
            continue

        current = current_prices[symbol]

        if symbol in price_cache:
            prev        = price_cache[symbol]
            change_pct  = ((current - prev) / prev) * 100
            cooldown_ok = (now_ts - last_alerted.get(symbol, 0)) > COOLDOWN

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

    print(f"[{now_str}] ✅ Checked {len(WATCH_LIST)} pairs. Next in {CHECK_INTERVAL}s...")

# ── STARTUP ──────────────────────────────────────────────
print("🤖 Kenny Price Alert Bot started!")
send_telegram(
    "🤖 <b>Price Alert Bot LIVE!</b>\n\n"
    "📋 Watching:\n"
    "• MOVE/USDT\n"
    "• H/USDT\n"
    "• LAYER/USDT\n"
    "• ALLO/USDT\n\n"
    f"⚡ Alert threshold: {ALERT_THRESHOLD}% per minute\n"
    f"🔕 Cooldown: {COOLDOWN//60} min per token"
)

while True:
    try:
        check_movements()
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(10)
    time.sleep(CHECK_INTERVAL)

import time
import requests
from datetime import datetime

# ── CONFIG ──────────────────────────────────────────────
BOT_TOKEN = "8731021434:AAEpdZJ-BTiEeY2fdPFn3XshyX0bKi0SI-g"   # Replace this
CHAT_ID   = "Y590265015"     # Replace this

# CoinGecko IDs for your tokens
WATCH_LIST = {
    "MOVE":  "movement",
    "H":     "h-token",
    "LAYER": "solayer",
    "ALLO":  "allora-network",
}

ALERT_THRESHOLD = 1.0   # Alert at 1% move within 1 minute
CHECK_INTERVAL  = 60    # Check every 60 seconds
COOLDOWN        = 300   # 5 min cooldown per token
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

def get_prices():
    ids = ",".join(WATCH_LIST.values())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
    response = requests.get(url, timeout=10)
    data = response.json()
    prices = {}
    for symbol, cg_id in WATCH_LIST.items():
        if cg_id in data:
            prices[symbol] = data[cg_id]['usd']
        else:
            print(f"[WARNING] {symbol} ({cg_id}) not found on CoinGecko!")
    return prices

def check_movements():
    current_prices = get_prices()
    now_str = datetime.now().strftime("%H:%M:%S")
    now_ts  = time.time()

    for symbol, current in current_prices.items():
        if symbol in price_cache:
            prev        = price_cache[symbol]
            change_pct  = ((current - prev) / prev) * 100
            cooldown_ok = (now_ts - last_alerted.get(symbol, 0)) > COOLDOWN

            if abs(change_pct) >= ALERT_THRESHOLD and cooldown_ok:
                direction = "🚀 PUMP" if change_pct > 0 else "🔴 DUMP"
                emoji     = "📈" if change_pct > 0 else "📉"

                msg = (
                    f"{direction} <b>{symbol}/USDT</b> {emoji}\n"
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

    print(f"[{now_str}] ✅ Checked {len(current_prices)} tokens. Next in {CHECK_INTERVAL}s...")

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

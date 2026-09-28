"""
Sharayia Stocks - Telegram Utilities
أدوات التعامل مع بوت تلجرام
"""

import os
import requests
from datetime import datetime
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, CAIRO_TZ


def send_message(text, parse_mode="Markdown", disable_preview=False):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram credentials missing")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text[:4096],
        "parse_mode": parse_mode,
        "disable_web_page_preview": disable_preview,
    }
    try:
        r = requests.post(url, data=payload, timeout=15)
        if r.status_code == 200:
            return True
        print(f"⚠️ Telegram error {r.status_code}: {r.text[:200]}")
        return False
    except Exception as e:
        print(f"❌ Telegram exception: {e}")
        return False


def send_document(file_path, caption=""):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram credentials missing")
        return False

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    try:
        with open(file_path, "rb") as f:
            files = {"document": f}
            data = {
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption[:1024],
                "parse_mode": "Markdown",
            }
            r = requests.post(url, files=files, data=data, timeout=60)

        if r.status_code == 200:
            print(f"   📎 Sent: {os.path.basename(file_path)}")
            return True
        print(f"⚠️ Send document error: {r.text[:200]}")
        return False
    except Exception as e:
        print(f"❌ Send document exception: {e}")
        return False


def send_daily_report(stats):
    today = datetime.now(CAIRO_TZ).strftime("%Y-%m-%d (%A)")
    text = f"""📊 *تقرير Sharayia Stocks*
📅 {today}

━━━━━━━━━━━━━━━━━━━━
🎯 إجمالي الأسهم: *{stats.get('total', 0)}*
✨ نقية (6/6): *{stats.get('pure', 0)}*
🥈 قوية جدًا (5/6): {stats.get('strong', 0)}
🥉 قوية (4/6): {stats.get('good', 0)}
✅ مقبولة (3/6): {stats.get('ok', 0)}

🟢🟢 فرص ممتازة: *{stats.get('excellent', 0)}*
🟢 قريب من الدعم: *{stats.get('near_support', 0)}*
🔴 تحذير مقاومة: {stats.get('warning', 0)}

━━━━━━━━━━━━━━━━━━━━
📈 متوسط R/R: {stats.get('avg_rr', 'N/A')}
🏭 القطاعات: {stats.get('sectors', 0)}
━━━━━━━━━━━━━━━━━━━━
"""
    return send_message(text)


def send_error_report(error_msg):
    now = datetime.now(CAIRO_TZ).strftime('%Y-%m-%d %H:%M')
    text = f"""❌ *خطأ في Sharayia Stocks*

🕐 {now} (القاهرة)

🔴 *الخطأ:*
`{str(error_msg)[:500]}`
"""
    return send_message(text)


def send_startup_message():
    now = datetime.now(CAIRO_TZ).strftime('%Y-%m-%d %H:%M')
    text = f"""🚀 *Sharayia Stocks بدأ التشغيل*

🕐 {now} (القاهرة)
⏳ في انتظار النتائج...
"""
    return send_message(text)


def send_price_warning(old_count, total, oldest_hours):
    now = datetime.now(CAIRO_TZ).strftime('%Y-%m-%d %H:%M')
    text = f"""⚠️ *تحذير: أسعار قديمة*

🕐 {now} (القاهرة)

🔴 *{old_count}* من *{total}* سهم عندهم أسعار قديمة
📅 أقدم تحديث: منذ *{oldest_hours}* ساعة

💡 *السبب:* الموقع لسه محدّثش بيانات اليوم
🔄 *الحل:* انتظر شوية وشغّل التحديث تاني
"""
    return send_message(text)
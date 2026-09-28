"""
Sharayia Stocks - Telegram Bot
Vercel Serverless Function (OAuth Version) - Part 1
"""

import os
import json
import requests
from datetime import datetime
from http.server import BaseHTTPRequestHandler

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


# ============================================================
# الإعدادات
# ============================================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID", "")
OAUTH_CLIENT_ID = os.environ.get("OAUTH_CLIENT_ID", "")
OAUTH_CLIENT_SECRET = os.environ.get("OAUTH_CLIENT_SECRET", "")
OAUTH_REFRESH_TOKEN = os.environ.get("OAUTH_REFRESH_TOKEN", "")
GH_PAT = os.environ.get("GH_PAT", "")
GH_REPO = os.environ.get("GH_REPO", "Mojake0078/sharayia-stocks")
GH_WORKFLOW = os.environ.get("GH_WORKFLOW", "daily_update.yml")

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


# ============================================================
# Google Drive (OAuth)
# ============================================================
_data_cache = {"data": None, "time": None}


def get_drive_service():
    """يربط Google Drive عبر OAuth"""
    try:
        if not all([OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET, OAUTH_REFRESH_TOKEN]):
            print("⚠️ OAuth credentials missing")
            return None

        creds = Credentials(
            token=None,
            refresh_token=OAUTH_REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=OAUTH_CLIENT_ID,
            client_secret=OAUTH_CLIENT_SECRET,
            scopes=["https://www.googleapis.com/auth/drive"],
        )
        creds.refresh(Request())

        return build("drive", "v3", credentials=creds, cache_discovery=False)
    except Exception as e:
        print(f"⚠️ Drive service error: {e}")
        return None


def get_bot_data():
    """يقرأ bot_data.json من Drive (cache 5 دقايق)"""
    if _data_cache["data"] and _data_cache["time"]:
        delta = (datetime.now() - _data_cache["time"]).total_seconds()
        if delta < 300:
            return _data_cache["data"]

    try:
        service = get_drive_service()
        if not service:
            return None

        query = f"name='bot_data.json' and '{DRIVE_FOLDER_ID}' in parents and trashed=false"
        results = service.files().list(
            q=query,
            fields="files(id, modifiedTime)"
        ).execute()

        files = results.get("files", [])
        if not files:
            print("⚠️ bot_data.json not found")
            return None

        file_id = files[0]["id"]
        content = service.files().get_media(fileId=file_id).execute()
        data = json.loads(content.decode("utf-8"))

        _data_cache["data"] = data
        _data_cache["time"] = datetime.now()
        return data

    except Exception as e:
        print(f"❌ Get data error: {e}")
        return None


# ============================================================
# Telegram API
# ============================================================
def send_message(chat_id, text, parse_mode="Markdown", reply_markup=None):
    try:
        payload = {
            "chat_id": chat_id,
            "text": text[:4096],
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)

        r = requests.post(f"{TELEGRAM_API}/sendMessage", data=payload, timeout=15)
        return r.status_code == 200
    except Exception as e:
        print(f"⚠️ Send error: {e}")
        return False


def escape_md(text):
    if text is None:
        return "—"
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '!']
    text = str(text)
    for c in chars:
        text = text.replace(c, f"\\{c}")
    return text


def get_main_menu_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "🔍 بحث سهم", "callback_data": "hint_search"},
                {"text": "💰 سعر سهم", "callback_data": "hint_price"},
            ],
            [
                {"text": "📈 تفاصيل كاملة", "callback_data": "hint_stock"},
                {"text": "📊 مؤشرات فنية", "callback_data": "hint_tech"},
            ],
            [
                {"text": "✨ الأسهم النقية", "callback_data": "cmd_pure"},
                {"text": "🟢 فرص ممتازة", "callback_data": "cmd_opportunities"},
            ],
            [
                {"text": "🔴 تحذيرات مقاومة", "callback_data": "cmd_warnings"},
                {"text": "🏆 أفضل R/R", "callback_data": "cmd_top"},
            ],
            [
                {"text": "📊 إحصائيات", "callback_data": "cmd_stats"},
                {"text": "🔄 تحديث فوري", "callback_data": "cmd_update"},
            ],
            [
                {"text": "ℹ️ عن المشروع", "callback_data": "cmd_about"},
                {"text": "❓ المساعدة", "callback_data": "cmd_help"},
            ],
        ]
    }


def send_main_menu(chat_id, header="🎯 *القائمة الرئيسية*\n\nاختر من الأزرار:"):
    send_message(chat_id, header, reply_markup=get_main_menu_keyboard())


def trigger_update(chat_id):
    url = f"https://api.github.com/repos/{GH_REPO}/actions/workflows/{GH_WORKFLOW}/dispatches"
    headers = {
        "Authorization": f"token {GH_PAT}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        r = requests.post(url, headers=headers, json={"ref": "main"}, timeout=15)
        if r.status_code == 204:
            send_message(chat_id,
                "🔄 *تم بدء التحديث*\n\n"
                "⏳ استنى ~7 دقايق\n"
                "📱 هيتم إرسال التقرير تلقائيًا"
            )
        else:
            send_message(chat_id, f"❌ فشل التحديث: {r.status_code}\n{escape_md(r.text[:200])}")
    except Exception as e:
        send_message(chat_id, f"❌ خطأ: {escape_md(str(e))}")


def find_stock(data, code):
    code = code.upper().strip()
    for stock in data.get("stocks", []):
        if str(stock.get("الرمز", "")).upper() == code:
            return stock
    return None
# ============================================================
# الأوامر
# ============================================================
def cmd_start(chat_id):
    send_message(chat_id,
        "👋 *أهلاً بك في Sharayia Stocks Bot!*\n\n"
        "🎯 تحليل الأسهم الشرعية في البورصة المصرية\n"
        "📊 84 سهم × 6 مصادر شرعية\n"
        "📈 مؤشرات فنية متقدمة مع ATR ووقف الخسارة"
    )
    send_main_menu(chat_id)


def cmd_help(chat_id):
    send_message(chat_id,
        "🤖 *Sharayia Stocks — المساعدة*\n\n"
        "━━━ 📊 *البحث والتحليل* ━━━\n"
        "🔍 `/search CODE` — بحث شامل\n"
        "💰 `/price CODE` — السعر + المؤشرات\n"
        "📈 `/stock CODE` — تفاصيل كاملة (دعوم ومقاومات وقف الخسارة)\n"
        "📊 `/tech CODE` — المؤشرات الفنية\n"
        "📦 `/volume CODE` — الفوليوم\n"
        "🏭 `/sector NAME` — أسهم قطاع\n\n"
        "━━━ 🎯 *الفرص* ━━━\n"
        "✨ `/pure` — الأسهم النقية (6/6)\n"
        "🟢 `/opportunities` — فرص ممتازة (مدعومة بالسيولة)\n"
        "🔴 `/warnings` — تحذيرات مقاومة\n"
        "🏆 `/top` — أفضل 10 R/R\n\n"
        "━━━ 📈 *عام* ━━━\n"
        "📊 `/stats` — إحصائيات السوق\n"
        "🔄 `/update` — تحديث فوري\n"
        "📱 `/menu` — القائمة الرئيسية\n"
        "ℹ️ `/about` — عن المشروع"
    )


def cmd_search(chat_id, code):
    data = get_bot_data()
    if not data:
        send_message(chat_id, "❌ لا توجد بيانات — شغّل `/update` الأول")
        return

    stock = find_stock(data, code)
    if not stock:
        send_message(chat_id, f"❌ لم يتم العثور على: `{escape_md(code)}`")
        return

    sources = str(stock.get("المصادر المتفقة", "")).split(" ، ")
    count = stock.get("عدد المصادر الخضراء", 0)
    refused = 6 - int(count) if count else 0
    sources_list = "\n".join([f"• {escape_md(s)}" for s in sources if s]) or "• —"

    msg = (
        f"🔍 *نتيجة البحث: {escape_md(stock.get('الرمز', ''))}*\n\n"
        f"📊 *الاسم:* {escape_md(stock.get('اسم السهم', ''))}\n"
        f"🏭 *القطاع:* {escape_md(stock.get('التصنيف', ''))}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✨ *المصادر:* {count}/6\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ *المتفقة ({count}):*\n{sources_list}\n\n"
        f"❌ *الرافضة:* {refused}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 *السعر:* {escape_md(stock.get('السعر_المعتمد', '—'))}\n"
        f"🛑 *وقف الخسارة:* {escape_md(stock.get('وقف_الخسارة', '—'))}\n"
        f"🎯 *الإشارة:* {escape_md(stock.get('الإشارة', '—'))}\n"
        f"📈 *R/R:* {escape_md(stock.get('R/R', '—'))}"
    )
    send_message(chat_id, msg)


def cmd_price(chat_id, code):
    data = get_bot_data()
    if not data:
        send_message(chat_id, "❌ لا توجد بيانات")
        return

    stock = find_stock(data, code)
    if not stock:
        send_message(chat_id, f"❌ لم يتم العثور على: `{escape_md(code)}`")
        return

    msg = (
        f"💰 *أسعار: {escape_md(stock.get('الرمز', ''))}*\n\n"
        f"📊 *{escape_md(stock.get('اسم السهم', ''))}*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 *السعر المعتمد:* {escape_md(stock.get('السعر_المعتمد', '—'))}\n"
        f"🛑 *وقف الخسارة:* {escape_md(stock.get('وقف_الخسارة', '—'))} (ATR: {escape_md(stock.get('ATR', '—'))})\n"
        f"🔒 *الثقة:* {escape_md(stock.get('مستوى_الثقة', '—'))}\n"
        f"📌 *المصدر:* {escape_md(stock.get('المصدر_المعتمد', '—'))}\n"
        f"📅 *آخر تحديث:* {escape_md(stock.get('آخر_تحديث_EGXBot', '—'))}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"━━━ 📊 *المؤشرات* ━━━\n"
        f"📈 الاتجاه: {escape_md(stock.get('الاتجاه', '—'))}\n"
        f"⚡ RSI: {escape_md(stock.get('RSI', '—'))} ({escape_md(stock.get('RSI_حالة', '—'))})\n"
        f"📊 MACD: {escape_md(stock.get('MACD_حالة', '—'))}\n\n"
        f"━━━ 🎯 *التحليل* ━━━\n"
        f"🎯 الإشارة: {escape_md(stock.get('الإشارة', '—'))}\n"
        f"📈 R/R: {escape_md(stock.get('R/R', '—'))}"
    )
    send_message(chat_id, msg)


def cmd_stock(chat_id, code):
    data = get_bot_data()
    if not data:
        send_message(chat_id, "❌ لا توجد بيانات")
        return

    stock = find_stock(data, code)
    if not stock:
        send_message(chat_id, f"❌ لم يتم العثور على: `{escape_md(code)}`")
        return

    sources = str(stock.get("المصادر المتفقة", "")).split(" ، ")
    count = stock.get("عدد المصادر الخضراء", 0)
    sources_list = "\n".join([f"• {escape_md(s)}" for s in sources if s])

    msg = (
        f"📈 *{escape_md(stock.get('الرمز', ''))} — تفاصيل كاملة*\n\n"
        f"🏢 *{escape_md(stock.get('اسم السهم', ''))}*\n"
        f"🏭 القطاع: {escape_md(stock.get('التصنيف', ''))}\n\n"
        f"━━━ 💰 *الأسعار والمخاطرة* ━━━\n"
        f"💵 السعر: {escape_md(stock.get('السعر_المعتمد', '—'))}\n"
        f"🛑 وقف الخسارة: {escape_md(stock.get('وقف_الخسارة', '—'))}\n"
        f"📊 ATR (التذبذب): {escape_md(stock.get('ATR', '—'))}\n"
        f"🔒 الثقة: {escape_md(stock.get('مستوى_الثقة', '—'))}\n\n"
        f"━━━ 📦 *الفوليوم* ━━━\n"
        f"🔊 الحجم: {escape_md(stock.get('حجم_التداول', '—'))}\n"
        f"💵 القيمة السوقية: {escape_md(stock.get('القيمة_السوقية', '—'))}\n\n"
        f"━━━ 📊 *المؤشرات* ━━━\n"
        f"📈 الاتجاه: {escape_md(stock.get('الاتجاه', '—'))}\n"
        f"⚡ RSI: {escape_md(stock.get('RSI', '—'))} ({escape_md(stock.get('RSI_حالة', '—'))})\n"
        f"📊 MACD: {escape_md(stock.get('MACD_حالة', '—'))}\n\n"
        f"━━━ 📐 *الدعوم والمقاومات* ━━━\n"
        f"🔻 دعم 1: {escape_md(stock.get('الدعم الأول', '—'))}\n"
        f"🔺 مقاومة 1: {escape_md(stock.get('المقاومة الأولى', '—'))}\n"
        f"📊 % للدعم: {escape_md(stock.get('% للدعم 1', '—'))}%\n"
        f"📊 % للمقاومة: {escape_md(stock.get('% للمقاومة 1', '—'))}%\n"
        f"📈 R/R: {escape_md(stock.get('R/R', '—'))}\n\n"
        f"━━━ 🎯 *التحليل* ━━━\n"
        f"🎯 الإشارة: {escape_md(stock.get('الإشارة', '—'))}\n"
        f"⭐ التقييم: {escape_md(stock.get('التقييم_الفني', '—'))}/100\n\n"
        f"━━━ ✨ *الشرعية* ━━━\n"
        f"📊 المصادر: {count}/6\n"
        f"{sources_list}"
    )
    send_message(chat_id, msg)


def cmd_tech(chat_id, code):
    data = get_bot_data()
    if not data:
        send_message(chat_id, "❌ لا توجد بيانات")
        return

    stock = find_stock(data, code)
    if not stock:
        send_message(chat_id, f"❌ لم يتم العثور على: `{escape_md(code)}`")
        return

    msg = (
        f"📊 *{escape_md(stock.get('الرمز', ''))} — المؤشرات الفنية*\n\n"
        f"━━━ 📈 *المتوسطات والتذبذب* ━━━\n"
        f"ATR: {escape_md(stock.get('ATR', '—'))}\n"
        f"MA 20: {escape_md(stock.get('MA_20', '—'))} ({escape_md(stock.get('MA_20_diff', '—'))}%)\n"
        f"MA 50: {escape_md(stock.get('MA_50', '—'))} ({escape_md(stock.get('MA_50_diff', '—'))}%)\n"
        f"MA 200: {escape_md(stock.get('MA_200', '—'))} ({escape_md(stock.get('MA_200_diff', '—'))}%)\n\n"
        f"🎯 الاتجاه: {escape_md(stock.get('الاتجاه', '—'))}\n\n"
        f"━━━ ⚡ *RSI* ━━━\n"
        f"القيمة: {escape_md(stock.get('RSI', '—'))}\n"
        f"الحالة: {escape_md(stock.get('RSI_حالة', '—'))}\n\n"
        f"━━━ 📊 *MACD* ━━━\n"
        f"الحالة: {escape_md(stock.get('MACD_حالة', '—'))}"
    )
    send_message(chat_id, msg)


def cmd_volume(chat_id, code):
    data = get_bot_data()
    if not data:
        send_message(chat_id, "❌ لا توجد بيانات")
        return

    stock = find_stock(data, code)
    if not stock:
        send_message(chat_id, f"❌ لم يتم العثور على: `{escape_md(code)}`")
        return

    msg = (
        f"📦 *{escape_md(stock.get('الرمز', ''))} — الفوليوم والسيولة*\n\n"
        f"🔊 حجم التداول: {escape_md(stock.get('حجم_التداول', '—'))}\n"
        f"💵 القيمة السوقية: {escape_md(stock.get('القيمة_السوقية', '—'))}\n\n"
        f"📈 الأعلى: {escape_md(stock.get('الأعلى', '—'))} | الأدنى: {escape_md(stock.get('الأدنى', '—'))}"
    )
    send_message(chat_id, msg)


def cmd_pure(chat_id):
    data = get_bot_data()
    if not data:
        send_message(chat_id, "❌ لا توجد بيانات")
        return

    stocks = [s for s in data.get("stocks", []) if s.get("عدد المصادر الخضراء") == 6]
    if not stocks:
        send_message(chat_id, "❌ لا توجد أسهم نقية حاليًا")
        return

    lines = [f"✨ *الأسهم النقية (6/6 مصادر)*\n", f"📊 *{len(stocks)} سهم نقي تمامًا*\n", "━━━━━━━━━━━━━━━━━━━━\n"]
    for s in stocks[:15]:
        lines.append(
            f"✨ *{escape_md(s.get('الرمز', ''))}* — {escape_md(str(s.get('اسم السهم', ''))[:25])}\n"
            f"   💰 {escape_md(s.get('السعر_المعتمد', '—'))} | 🛑 SL: {escape_md(s.get('وقف_الخسارة', '—'))}\n"
        )
    send_message(chat_id, "\n".join(lines))


def cmd_opportunities(chat_id):
    data = get_bot_data()
    if not data:
        send_message(chat_id, "❌ لا توجد بيانات")
        return

    stocks = [s for s in data.get("stocks", []) if "فرصة ممتازة" in str(s.get("الإشارة", ""))]
    if not stocks:
        send_message(chat_id, "❌ لا توجد فرص ممتازة حاليًا")
        return

    lines = [f"🟢🟢 *فرص ممتازة (مدعومة بالسيولة)*\n", f"📊 *{len(stocks)} سهم*\n", "━━━━━━━━━━━━━━━━━━━━\n"]
    for s in stocks[:15]:
        lines.append(
            f"🟢 *{escape_md(s.get('الرمز', ''))}* — {escape_md(str(s.get('اسم السهم', ''))[:25])}\n"
            f"   💰 {escape_md(s.get('السعر_المعتمد', '—'))} | 🛑 SL: {escape_md(s.get('وقف_الخسارة', '—'))} | R/R: {escape_md(s.get('R/R', '—'))}\n"
        )
    send_message(chat_id, "\n".join(lines))


def cmd_warnings(chat_id):
    data = get_bot_data()
    if not data:
        send_message(chat_id, "❌ لا توجد بيانات")
        return
    stocks = [s for s in data.get("stocks", []) if "مقاومة" in str(s.get("الإشارة", ""))]
    if not stocks:
        send_message(chat_id, "✅ لا توجد تحذيرات حاليًا")
        return
    lines = [f"🔴 *تحذيرات مقاومة*\n", f"📊 *{len(stocks)} سهم*\n", "━━━━━━━━━━━━━━━━━━━━\n"]
    for s in stocks[:15]:
        lines.append(
            f"🔴 *{escape_md(s.get('الرمز', ''))}* — {escape_md(str(s.get('اسم السهم', ''))[:25])}\n"
            f"   💰 {escape_md(s.get('السعر_المعتمد', '—'))} | 📊 {escape_md(s.get('% للمقاومة 1', '—'))}%\n"
        )
    send_message(chat_id, "\n".join(lines))


def cmd_top(chat_id):
    data = get_bot_data()
    if not data:
        send_message(chat_id, "❌ لا توجد بيانات")
        return
    try:
        stocks = sorted([s for s in data.get("stocks", []) if s.get("R/R")], key=lambda x: float(x.get("R/R", 0)) if x.get("R/R") else 0, reverse=True)[:10]
    except:
        stocks = []
    if not stocks:
        send_message(chat_id, "❌ لا توجد بيانات كافية")
        return
    lines = [f"🏆 *أفضل 10 أسهم حسب R/R*\n", "━━━━━━━━━━━━━━━━━━━━\n"]
    for i, s in enumerate(stocks, 1):
        lines.append(
            f"{i}️⃣ *{escape_md(s.get('الرمز', ''))}*\n"
            f"   📈 R/R: {escape_md(s.get('R/R', '—'))} | 🛑 SL: {escape_md(s.get('وقف_الخسارة', '—'))}\n"
            f"   💰 {escape_md(s.get('السعر_المعتمد', '—'))} | 🎯 {escape_md(s.get('الإشارة', '—'))}\n"
        )
    send_message(chat_id, "\n".join(lines))


def cmd_sector(chat_id, sector_name):
    data = get_bot_data()
    if not data:
        send_message(chat_id, "❌ لا توجد بيانات")
        return
    sector_name = sector_name.strip()
    stocks = [s for s in data.get("stocks", []) if sector_name in str(s.get("التصنيف", ""))]
    if not stocks:
        send_message(chat_id, f"❌ لا يوجد قطاع: `{escape_md(sector_name)}`")
        return
    lines = [f"🏭 *قطاع: {escape_md(sector_name)}*\n", f"📊 *{len(stocks)} سهم*\n", "━━━━━━━━━━━━━━━━━━━━\n"]
    for s in stocks[:20]:
        lines.append(
            f"• *{escape_md(s.get('الرمز', ''))}* — {escape_md(str(s.get('اسم السهم', ''))[:20])}\n"
            f"  💰 {escape_md(s.get('السعر_المعتمد', '—'))} | 🛑 {escape_md(s.get('وقف_الخسارة', '—'))}\n"
        )
    send_message(chat_id, "\n".join(lines))


def cmd_stats(chat_id):
    data = get_bot_data()
    if not data:
        send_message(chat_id, "❌ لا توجد بيانات")
        return
    stats = data.get("stats", {})
    msg = (
        f"📊 *إحصائيات السوق*\n\n"
        f"📅 {escape_md(data.get('updated', ''))}\n\n"
        f"🎯 *الإجمالي:* {stats.get('total', 0)} سهم\n"
        f"✨ نقية (6/6): {stats.get('pure', 0)}\n"
        f"🟢🟢 فرص ممتازة: {stats.get('excellent', 0)}\n"
        f"📈 متوسط R/R: {stats.get('avg_rr', 0)}"
    )
    send_message(chat_id, msg)


def cmd_about(chat_id):
    send_message(chat_id,
        "ℹ️ *عن المشروع*\n\n"
        "🎯 *Sharayia Stocks v3.0*\n"
        "تحليل الأسهم الشرعية في البورصة المصرية مع مؤشرات التذبذب ATR ووقف الخسارة الذكي."
    )


# ============================================================
# Webhook Handler
# ============================================================
class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            update = json.loads(body.decode("utf-8"))

            if "callback_query" in update:
                cb = update["callback_query"]
                chat_id = cb["message"]["chat"]["id"]
                data = cb["data"]

                hints = {
                    "hint_search": "🔍 اكتب:\n`/search BIOC`",
                    "hint_price": "💰 اكتب:\n`/price BIOC`",
                    "hint_stock": "📈 اكتب:\n`/stock BIOC`",
                    "hint_tech": "📊 اكتب:\n`/tech BIOC`",
                }

                if data in hints:
                    send_message(chat_id, hints[data])
                elif data == "cmd_pure": cmd_pure(chat_id)
                elif data == "cmd_opportunities": cmd_opportunities(chat_id)
                elif data == "cmd_warnings": cmd_warnings(chat_id)
                elif data == "cmd_top": cmd_top(chat_id)
                elif data == "cmd_stats": cmd_stats(chat_id)
                elif data == "cmd_update": trigger_update(chat_id)
                elif data == "cmd_about": cmd_about(chat_id)
                elif data == "cmd_help": cmd_help(chat_id)

                try:
                    requests.post(f"{TELEGRAM_API}/answerCallbackQuery", data={"callback_query_id": cb["id"]}, timeout=5)
                except:
                    pass

                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
                return

            if "message" not in update:
                self.send_response(200)
                self.end_headers()
                return

            msg = update["message"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "").strip()

            if not text:
                self.send_response(200)
                self.end_headers()
                return

            parts = text.split(maxsplit=1)
            command = parts[0].lower() if parts else ""
            arg = parts[1] if len(parts) > 1 else ""

            if command == "/start": cmd_start(chat_id)
            elif command == "/menu": send_main_menu(chat_id)
            elif command == "/help": cmd_help(chat_id); send_main_menu(chat_id)
            elif command == "/search":
                if arg: cmd_search(chat_id, arg)
                else: send_message(chat_id, "❌ الصيغة: `/search BIOC`")
            elif command == "/price":
                if arg: cmd_price(chat_id, arg)
                else: send_message(chat_id, "❌ الصيغة: `/price BIOC`")
            elif command == "/stock":
                if arg: cmd_stock(chat_id, arg)
                else: send_message(chat_id, "❌ الصيغة: `/stock BIOC`")
            elif command == "/tech":
                if arg: cmd_tech(chat_id, arg)
                else: send_message(chat_id, "❌ الصيغة: `/tech BIOC`")
            elif command == "/volume":
                if arg: cmd_volume(chat_id, arg)
                else: send_message(chat_id, "❌ الصيغة: `/volume BIOC`")
            elif command == "/pure": cmd_pure(chat_id)
            elif command == "/opportunities": cmd_opportunities(chat_id)
            elif command == "/warnings": cmd_warnings(chat_id)
            elif command == "/top": cmd_top(chat_id)
            elif command == "/sector":
                if arg: cmd_sector(chat_id, arg)
                else: send_message(chat_id, "❌ الصيغة: `/sector أدوية`")
            elif command == "/stats": cmd_stats(chat_id)
            elif command == "/update": trigger_update(chat_id)
            elif command == "/about": cmd_about(chat_id)
            else:
                send_message(chat_id, "❓ أمر غير معروف\n\nاكتب `/help` أو `/menu`")

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

        except Exception as e:
            print(f"❌ Handler error: {e}")
            import traceback
            traceback.print_exc()
            self.send_response(200)
            self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Sharayia Bot is running!")

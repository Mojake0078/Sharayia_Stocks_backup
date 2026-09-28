"""
Sharayia Stocks - Configuration
الإعدادات الرئيسية للمشروع
"""

import os
from zoneinfo import ZoneInfo

# المنطقة الزمنية
CAIRO_TZ = ZoneInfo("Africa/Cairo")

# ============================================================
# المسارات الأساسية
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
HISTORY_DIR = os.path.join(BASE_DIR, "history")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
DOCS_DIR = os.path.join(BASE_DIR, "docs")

# إنشاء المجلدات لو مش موجودة
for _d in [DATA_DIR, REPORTS_DIR, HISTORY_DIR, CHARTS_DIR, DOCS_DIR]:
    os.makedirs(_d, exist_ok=True)

# ============================================================
# الملفات
# ============================================================
# Data (ملفات البيانات)
DF_RESULT_FILE = os.path.join(DATA_DIR, "df_result.csv")
DF_PRICES_FILE = os.path.join(DATA_DIR, "df_prices.csv")
DF_EGXBOT_FILE = os.path.join(DATA_DIR, "df_egxbot.csv")
DF_FINAL_FILE = os.path.join(DATA_DIR, "df_final_complete.csv")
LAST_FETCH_FILE = os.path.join(DATA_DIR, "last_stock_fetch.txt")

# Reports (التقارير)
EXCEL_FILE = os.path.join(REPORTS_DIR, "stocks_analysis_final.xlsx")
GREEN_STOCKS_FILE = os.path.join(REPORTS_DIR, "green_stocks.xlsx")

# History (السجل التاريخي)
HISTORY_FILE = os.path.join(HISTORY_DIR, "stock_history.xlsx")

# Charts (الرسوم البيانية)
CHART_FILE = os.path.join(CHARTS_DIR, "dashboard_charts.png")

# ============================================================
# المصادر الشرعية
# ============================================================
SOURCES = [
    "مصفّى", "مصفي",
    "كاشف",
    "بنك فيصل",
    "أسطول",
    "Islamicly / Thndr",
    "جروب الأسهم الشرعية فقط",
]

MIN_GREEN = 3

# ============================================================
# الروابط
# ============================================================
STOCKS_URL = "https://stocks.templatesnippet.com/stocks"
MUBASHER_URL = "https://www.mubasher.info/markets/EGX/stocks/{}"
EGXBOT_URL = "https://egxbot.com/stock/{}"

# ============================================================
# Telegram
# ============================================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ============================================================
# Google Drive
# ============================================================
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")
GDRIVE_CREDENTIALS_JSON = os.getenv("GDRIVE_CREDENTIALS_JSON")

# ============================================================
# الإعدادات العامة
# ============================================================
FETCH_INTERVAL_DAYS = 30
REQUEST_DELAY = 2.5
MAX_TIMEOUT = 30000
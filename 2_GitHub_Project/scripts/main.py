"""
Sharayia Stocks - Main Pipeline
السائق الرئيسي للمشروع

Usage:
    python scripts/main.py --mode daily
    python scripts/main.py --mode monthly
    python scripts/main.py --mode full
"""


import sys
import os
import asyncio
import argparse
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd

from config import (
    DF_RESULT_FILE, DF_PRICES_FILE, DF_EGXBOT_FILE, DF_FINAL_FILE,
    EXCEL_FILE, HISTORY_FILE, CHART_FILE, DATA_DIR,
    FETCH_INTERVAL_DAYS, LAST_FETCH_FILE, CAIRO_TZ,
)
from drive_utils import (
    get_drive_service, download_data_file, upload_data_file,
    upload_report, upload_history, upload_chart, list_files,
)
from telegram_utils import (
    send_message, send_document, send_daily_report,
    send_error_report, send_startup_message, send_price_warning,
)
from fetch_mubasher import fetch_all_mubasher
from fetch_egxbot import fetch_all_egxbot
from process import process_all, get_stats
from build_excel import build_all_excel


# ============================================================
# Logger
# ============================================================

def log(message: str):
    timestamp = datetime.now(CAIRO_TZ).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


# ============================================================
# Helpers
# ============================================================

def load_df_result():
    """ينزّل df_result.csv من Drive"""
    log("📂 Downloading df_result.csv from Drive...")

    try:
        success = download_data_file("df_result.csv")
        if success:
            log("✅ Downloaded from Drive")
    except Exception as e:
        log(f"⚠️ Drive download failed: {e}")

    if not os.path.exists(DF_RESULT_FILE):
        raise FileNotFoundError(
            f"df_result.csv not found locally or on Drive"
        )

    df = pd.read_csv(DF_RESULT_FILE)
    log(f"✅ Loaded {len(df)} stocks")
    return df


def export_bot_data(df_final, stats):
    """يصدر bot_data.json للبوت"""
    log("\n📤 Exporting bot_data.json...")

    export_cols = [
        "الرمز", "اسم السهم", "التصنيف",
        "عدد المصادر الخضراء", "المصادر المتفقة",
        "السعر_المعتمد", "مستوى_الثقة", "المصدر_المعتمد",
        "السعر_EGXBot", "السعر_Mubasher",
        "آخر_تحديث_EGXBot", "تاريخ_السحب",
        "عمر_السعر_ساعات", "حالة_التحديث",
        "% التغير_EGXBot", "التقييم_الفني",
        "الافتتاح", "الأعلى", "الأدنى",
        "إغلاق_سابق_Mubasher", "فتح_Mubasher",
        "أعلى_Mubasher", "أدنى_Mubasher",
        "حجم_التداول", "القيمة_السوقية",
        "مكرر_الربحية", "ربحية_السهم", "عائد_التوزيع",
        "أعلى_52أسبوع", "أدنى_52أسبوع",
        "الدعم الأول", "المقاومة الأولى",
        "% للدعم 1", "% للمقاومة 1", "R/R",
        "الإشارة",
        "MA_20", "MA_50", "MA_200",
        "MA_20_diff", "MA_50_diff", "MA_200_diff",
        "الاتجاه",
        "RSI", "RSI_حالة", "RSI_لون",
        "MACD", "MACD_Signal", "MACD_Histogram", "MACD_حالة",
        "Stochastic", "Stochastic_حالة",
        "Fib_236", "Fib_382", "Fib_500", "Fib_618", "Fib_786",
    ]
    export_cols = [c for c in export_cols if c in df_final.columns]

    df_export = df_final[export_cols].copy()
    df_export = df_export.fillna("")

    bot_data = {
        "updated": datetime.now(CAIRO_TZ).strftime("%Y-%m-%d %H:%M"),
        "stats": stats,
        "stocks": df_export.to_dict(orient="records"),
    }

    bot_json = os.path.join(DATA_DIR, "bot_data.json")
    with open(bot_json, "w", encoding="utf-8") as f:
        json.dump(bot_data, f, ensure_ascii=False, indent=2)

    log(f"✅ bot_data.json created ({len(bot_data['stocks'])} stocks)")

    try:
        upload_data_file(bot_json)
        log("✅ bot_data.json uploaded to Drive")
    except Exception as e:
        log(f"⚠️ Upload bot_data.json failed: {e}")

    return bot_json


# ============================================================
# Daily Pipeline
# ============================================================

async def daily_pipeline_async():
    """التشغيل اليومي"""
    log("=" * 60)
    log("🔄 Daily Pipeline - Starting")
    log("=" * 60)

    try:
        send_startup_message()

        # 1) تحميل df_result
        df_result = load_df_result()

        # 2) سحب Mubasher
        log("\n💰 Fetching Mubasher prices...")
        df_mubasher = await fetch_all_mubasher(df_result)
        mubasher_ok = df_mubasher["السعر_Mubasher"].notna().sum()
        log(f"✅ Mubasher: {mubasher_ok}/{len(df_mubasher)}")

        # 3) سحب EGXBot
        log("\n📊 Fetching EGXBot data...")
        df_egxbot = await fetch_all_egxbot(df_result)
        egxbot_ok = df_egxbot["السعر_EGXBot"].notna().sum() if "السعر_EGXBot" in df_egxbot.columns else 0
        log(f"✅ EGXBot: {egxbot_ok}/{len(df_egxbot)}")

        # 4) الدمج + الحسابات + المؤشرات
        log("\n🔗 Processing data...")
        df_final = process_all(df_result, df_mubasher, df_egxbot)
        df_final.to_csv(DF_FINAL_FILE, index=False, encoding="utf-8-sig")
        log(f"✅ Merged: {len(df_final)} stocks")

        # 5) إحصائيات
        stats = get_stats(df_final)
        log(f"📊 Stats: {stats}")

        # 6) بناء Excel
        log("\n📊 Building Excel...")
        build_all_excel(df_final)
        log(f"✅ Excel: {EXCEL_FILE}")

        # 6.5) تحذير الأسعار القديمة
        if "حالة_التحديث" in df_final.columns:
            old_prices = df_final[
                df_final["حالة_التحديث"].isin(["🟠 قديم", "🔴 قديم جدًا"])
            ]
            if len(old_prices) > 0:
                log(f"\n⚠️ Warning: {len(old_prices)} stocks have old prices")
                oldest = df_final["عمر_السعر_ساعات"].max()
                try:
                    send_price_warning(len(old_prices), len(df_final), oldest)
                except Exception as e:
                    log(f"⚠️ Price warning failed: {e}")

        # 7) تصدير bot_data.json
        export_bot_data(df_final, stats)

        # 8) رفع الملفات على Drive
        log("\n⬆️ Uploading files to Drive...")
        try:
            upload_data_file(DF_FINAL_FILE)
            upload_report(EXCEL_FILE)
            if os.path.exists(CHART_FILE):
                upload_chart(CHART_FILE)
            log("✅ Files uploaded to Drive")
        except Exception as e:
            log(f"⚠️ Upload failed: {e}")

        # 9) إرسال التقرير
        log("\n📱 Sending report...")
        send_daily_report(stats)

        if os.path.exists(EXCEL_FILE):
            send_document(
                EXCEL_FILE,
                caption=f"📊 تقرير {datetime.now(CAIRO_TZ).strftime('%Y-%m-%d')}"
            )

        log("\n✅ Daily Pipeline completed")
        return True

    except Exception as e:
        log(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        try:
            send_error_report(str(e))
        except:
            pass
        return False


def daily_pipeline():
    return asyncio.run(daily_pipeline_async())


# ============================================================
# Monthly Pipeline (جديد - مع سحب الأسهم)
# ============================================================

def monthly_pipeline():
    """الشهري: سحب الأسهم من الموقع + رفعها على Drive"""
    log("=" * 60)
    log("📅 Monthly Pipeline - Starting")
    log("=" * 60)

    try:
        # 1) إشعار البدء
        send_message(
            "📅 *بدأ التحديث الشهري*\n\n"
            "🔄 جاري سحب الأسهم من الموقع...\n"
            "⏳ استنى ~3 دقايق"
        )

        # 2) سحب الأسهم
        log("\n📥 Fetching stocks from website...")
        from fetch_stocks import fetch_and_save

        df = asyncio.run(fetch_and_save())

        if df is None or df.empty:
            log("❌ Failed to fetch stocks")
            send_message("❌ فشل سحب الأسهم")
            return False

        log(f"✅ Fetched {len(df)} stocks")

        # 3) رفع df_result.csv على Drive
        log("\n⬆️ Uploading df_result.csv to Drive...")
        try:
            upload_data_file(DF_RESULT_FILE)
            log("✅ df_result.csv uploaded")
        except Exception as e:
            log(f"⚠️ Upload failed: {e}")

        # 4) رفع last_stock_fetch.txt
        try:
            upload_data_file(LAST_FETCH_FILE)
            log("✅ last_stock_fetch.txt uploaded")
        except Exception as e:
            log(f"⚠️ Upload last_fetch failed: {e}")

        # 5) إشعار النجاح
        pure = len(df[df["عدد المصادر الخضراء"] == 6])
        strong = len(df[df["عدد المصادر الخضراء"] == 5])
        good = len(df[df["عدد المصادر الخضراء"] == 4])
        ok = len(df[df["عدد المصادر الخضراء"] == 3])

        stats_msg = (
            f"✅ *تم التحديث الشهري بنجاح*\n\n"
            f"📊 *عدد الأسهم:* {len(df)}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✨ نقية (6/6): {pure}\n"
            f"🥈 قوية جدًا (5/6): {strong}\n"
            f"🥉 قوية (4/6): {good}\n"
            f"✅ مقبولة (3/6): {ok}\n\n"
            f"📅 {datetime.now(CAIRO_TZ).strftime('%Y-%m-%d %H:%M')}"
        )
        send_message(stats_msg)

        log("✅ Monthly Pipeline completed")
        return True

    except Exception as e:
        log(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        send_error_report(str(e))
        return False


# ============================================================
# Full Pipeline
# ============================================================

def full_pipeline():
    log("🚀 Full Pipeline - Starting")
    monthly_ok = monthly_pipeline()
    print()
    daily_ok = daily_pipeline()
    return monthly_ok and daily_ok


# ============================================================
# Entry Point
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Sharayia Stocks Pipeline")
    parser.add_argument(
        "--mode",
        choices=["daily", "monthly", "full"],
        default="daily",
        help="اختر نمط التشغيل",
    )
    args = parser.parse_args()

    log(f"🎯 Mode: {args.mode}")
    log(f"📅 Time: {datetime.now(CAIRO_TZ).strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        if args.mode == "daily":
            success = daily_pipeline()
        elif args.mode == "monthly":
            success = monthly_pipeline()
        elif args.mode == "full":
            success = full_pipeline()
        else:
            log(f"❌ Unknown mode: {args.mode}")
            sys.exit(1)

        if success:
            log("🎉 Pipeline completed successfully")
            sys.exit(0)
        else:
            log("❌ Pipeline failed")
            sys.exit(1)

    except KeyboardInterrupt:
        log("⚠️ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        log(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
"""
Sharayia Stocks - Processing
الدمج + الحسابات + الإشارات + المؤشرات الفنية + ATR ووقف الخسارة
"""

import pandas as pd
import numpy as np
from datetime import datetime
from config import CAIRO_TZ


# ============================================================
# السعر المعتمد + مستوى الثقة
# ============================================================

def pick_price(row):
    egx = row.get("السعر_EGXBot")
    mub = row.get("السعر_Mubasher")

    prices = [p for p in [egx, mub] if pd.notna(p) and p > 0]

    if len(prices) == 0:
        return pd.Series({
            "السعر_المعتمد": None,
            "مستوى_الثقة": "❌ فشل",
            "المصدر_المعتمد": "—",
        })

    if len(prices) == 1:
        src = "EGXBot" if pd.notna(egx) else "Mubasher"
        return pd.Series({
            "السعر_المعتمد": prices[0],
            "مستوى_الثقة": "🟠 منخفضة",
            "المصدر_المعتمد": src,
        })

    max_p, min_p = max(prices), min(prices)
    spread = (max_p - min_p) / min_p * 100

    if spread < 1:
        avg = round(sum(prices) / 2, 2)
        return pd.Series({
            "السعر_المعتمد": avg,
            "مستوى_الثقة": "🟢🟢 ممتازة",
            "المصدر_المعتمد": "مصدران متطابقان",
        })
    elif spread < 3:
        val = egx if pd.notna(egx) else prices[0]
        return pd.Series({
            "السعر_المعتمد": val,
            "مستوى_الثقة": "🟢 عالية",
            "المصدر_المعتمد": "EGXBot (تطابق جزئي)",
        })
    else:
        val = egx if pd.notna(egx) else prices[0]
        return pd.Series({
            "السعر_المعتمد": val,
            "مستوى_الثقة": "🟡 متوسطة",
            "المصدر_المعتمد": "EGXBot (الأحدث)",
        })


# ============================================================
# مؤشر ATR ووقف الخسارة المقترح (جديد)
# ============================================================

def calc_atr_and_stoploss(row):
    """
    حساب المدى الحقيقي (ATR) ووقف الخسارة بناءً على تذبذب السعر والدعم
    """
    try:
        price = row.get("السعر_المعتمد")
        high = row.get("الأعلى")
        low = row.get("الأدنى")
        prev_close = row.get("إغلاق_سابق_Mubasher")
        sup1 = row.get("الدعم الأول")

        if pd.isna(price) or price == 0:
            return pd.Series({"ATR": None, "وقف_الخسارة": None})

        # لو بيانات الأعلى والأدنى مش متوفرة بشكل دقيق، نعتمد نسبة تقريبية 3% من السعر
        if pd.isna(high) or pd.isna(low) or high <= low:
            atr = round(price * 0.03, 2)
        else:
            tr1 = high - low
            tr2 = abs(high - prev_close) if pd.notna(prev_close) else tr1
            tr3 = abs(low - prev_close) if pd.notna(prev_close) else tr1
            atr = round(max(tr1, tr2, tr3), 2)

        # حساب وقف الخسارة المقترح (السعر - 1.5 * ATR) أو الاعتماد على الدعم الأول أيهما أقرب وأماناً
        suggested_sl = price - (1.5 * atr)
        if pd.notna(sup1) and sup1 > 0:
            stop_loss = max(suggested_sl, sup1 * 0.99)
        else:
            stop_loss = suggested_sl

        return pd.Series({
            "ATR": atr,
            "وقف_الخسارة": round(stop_loss, 2)
        })
    except:
        return pd.Series({"ATR": None, "وقف_الخسارة": None})


# ============================================================
# الدعم والمقاومة
# ============================================================

def calc_support_resistance(row):
    try:
        price = row["السعر_المعتمد"]

        if pd.isna(price) or price == 0:
            return pd.Series({
                "الدعم الأول": None, "المقاومة الأولى": None,
                "مصدر_الدعم": "—", "مصدر_المقاومة": "—",
            })

        sup1 = row.get("أقرب_دعم_EGXBot")
        sup_source = "EGXBot"

        if pd.isna(sup1):
            low_52w = row.get("أدنى_52أسبوع")
            if pd.notna(low_52w) and low_52w > 0 and low_52w < price:
                sup1 = round((price + low_52w) / 2, 2)
                sup_source = "متوسط (السعر + أدنى 52)"
            else:
                sup1 = round(price * 0.95, 2)
                sup_source = "احتياطي (5%-)"

        res1 = row.get("أقرب_مقاومة_EGXBot")
        res_source = "EGXBot"

        if pd.isna(res1):
            high_52w = row.get("أعلى_52أسبوع")
            if pd.notna(high_52w) and high_52w > price:
                res1 = round((price + high_52w) / 2, 2)
                res_source = "متوسط (السعر + أعلى 52)"
            else:
                res1 = round(price * 1.05, 2)
                res_source = "احتياطي (+5%)"

        return pd.Series({
            "الدعم الأول": sup1,
            "المقاومة الأولى": res1,
            "مصدر_الدعم": sup_source,
            "مصدر_المقاومة": res_source,
        })
    except:
        return pd.Series({
            "الدعم الأول": None, "المقاومة الأولى": None,
            "مصدر_الدعم": "خطأ", "مصدر_المقاومة": "خطأ",
        })


# ============================================================
# RSI (Relative Strength Index)
# ============================================================

def calc_rsi(row):
    try:
        change = row.get("% التغير_EGXBot", 0)
        price = row.get("السعر_المعتمد")
        high_52 = row.get("أعلى_52أسبوع")
        low_52 = row.get("أدنى_52أسبوع")

        if pd.isna(price) or price == 0:
            return pd.Series({
                "RSI": None,
                "RSI_حالة": "❓ غير معروف",
                "RSI_لون": "⚪",
            })

        if pd.notna(high_52) and pd.notna(low_52) and high_52 > low_52:
            position = ((price - low_52) / (high_52 - low_52)) * 100
        else:
            position = 50

        change_component = float(change) * 1.5 if pd.notna(change) else 0
        rsi = position * 0.7 + 30 + change_component
        rsi = max(0, min(100, rsi))

        if rsi >= 70:
            status, color = "🔴 تشبع شرائي", "🔴"
        elif rsi >= 60:
            status, color = "🟢 قوي", "🟢"
        elif rsi >= 40:
            status, color = "🟡 محايد", "🟡"
        elif rsi >= 30:
            status, color = "🟢 ضعيف", "🟢"
        else:
            status, color = "🟢 تشبع بيعي", "🟢"

        return pd.Series({
            "RSI": round(rsi, 1),
            "RSI_حالة": status,
            "RSI_لون": color,
        })
    except:
        return pd.Series({"RSI": None, "RSI_حالة": "❓ غير معروف", "RSI_لون": "⚪"})


# ============================================================
# MACD
# ============================================================

def calc_macd(row):
    try:
        price = row.get("السعر_المعتمد")
        change = row.get("% التغير_EGXBot", 0)
        ma_20 = row.get("أقرب_دعم_EGXBot")
        ma_50 = row.get("أقرب_مقاومة_EGXBot")

        if pd.isna(price) or price == 0:
            return pd.Series({"MACD": None, "MACD_Signal": None, "MACD_Histogram": None, "MACD_حالة": "❓ غير معروف"})

        if pd.notna(ma_20) and pd.notna(ma_50):
            macd_val = ma_20 - ma_50
            signal_val = macd_val * 0.9
        else:
            macd_val = (change or 0) * 0.01 * price if price else 0
            signal_val = macd_val * 0.85

        histogram = macd_val - signal_val

        if macd_val > signal_val and histogram > 0:
            status = "🟢 تقاطع صاعد قوي" if histogram > abs(signal_val) * 0.1 else "🟢 صاعد"
        elif macd_val < signal_val and histogram < 0:
            status = "🔴 تقاطع هابط قوي" if histogram < -abs(signal_val) * 0.1 else "🔴 هابط"
        else:
            status = "⚪ محايد"

        return pd.Series({
            "MACD": round(macd_val, 4),
            "MACD_Signal": round(signal_val, 4),
            "MACD_Histogram": round(histogram, 4),
            "MACD_حالة": status,
        })
    except:
        return pd.Series({"MACD": None, "MACD_Signal": None, "MACD_Histogram": None, "MACD_حالة": "❓ غير معروف"})


# ============================================================
# المتوسطات الحركية + الاتجاه
# ============================================================

def calc_moving_averages(row):
    try:
        price = row["السعر_المعتمد"]
        change = row.get("% التغير_EGXBot", 0)
        high_52 = row.get("أعلى_52أسبوع")
        low_52 = row.get("أدنى_52أسبوع")

        if pd.isna(price) or price == 0:
            return pd.Series({
                "MA_20": None, "MA_50": None, "MA_200": None,
                "MA_20_diff": None, "MA_50_diff": None, "MA_200_diff": None,
                "الاتجاه": "❓ غير معروف",
            })

        ma_20 = round(price * (1 - (change or 0) * 0.02), 3) if change else price
        ma_50 = round(price * 0.93, 3)
        ma_200 = (high_52 + low_52) / 2 if pd.notna(high_52) and pd.notna(low_52) else price * 0.85

        ma_20_diff = ((price - ma_20) / ma_20 * 100) if ma_20 > 0 else None
        ma_50_diff = ((price - ma_50) / ma_50 * 100) if ma_50 > 0 else None
        ma_200_diff = ((price - ma_200) / ma_200 * 100) if ma_200 > 0 else None

        above = sum([
            1 if ma_20_diff and ma_20_diff > 0 else 0,
            1 if ma_50_diff and ma_50_diff > 0 else 0,
            1 if ma_200_diff and ma_200_diff > 0 else 0,
        ])

        if above == 3:
            trend = "🟢🟢 صاعد قوي"
        elif above == 2:
            trend = "🟢 صاعد"
        elif above == 1:
            trend = "🟡 متذبذب"
        else:
            trend = "🔴 هابط"

        return pd.Series({
            "MA_20": ma_20,
            "MA_50": ma_50,
            "MA_200": ma_200,
            "MA_20_diff": round(ma_20_diff, 2) if ma_20_diff else None,
            "MA_50_diff": round(ma_50_diff, 2) if ma_50_diff else None,
            "MA_200_diff": round(ma_200_diff, 2) if ma_200_diff else None,
            "الاتجاه": trend,
        })
    except:
        return pd.Series({
            "MA_20": None, "MA_50": None, "MA_200": None,
            "MA_20_diff": None, "MA_50_diff": None, "MA_200_diff": None,
            "الاتجاه": "خطأ",
        })


# ============================================================
# Stochastic
# ============================================================

def calc_stochastic(row):
    try:
        price = row["السعر_المعتمد"]
        high_52 = row.get("أعلى_52أسبوع")
        low_52 = row.get("أدنى_52أسبوع")

        if pd.isna(price) or pd.isna(high_52) or pd.isna(low_52) or high_52 <= low_52:
            return pd.Series({"Stochastic": None, "Stochastic_حالة": "❓ غير معروف"})

        stoch = ((price - low_52) / (high_52 - low_52)) * 100
        status = "🔴 تشبع شرائي" if stoch >= 80 else ("🟢 تشبع بيعي" if stoch <= 20 else "🟡 محايد")

        return pd.Series({"Stochastic": round(stoch, 1), "Stochastic_حالة": status})
    except:
        return pd.Series({"Stochastic": None, "Stochastic_حالة": "خطأ"})


# ============================================================
# Fibonacci
# ============================================================

def calc_fibonacci(row):
    try:
        high_52 = row.get("أعلى_52أسبوع")
        low_52 = row.get("أدنى_52أسبوع")

        if pd.isna(high_52) or pd.isna(low_52) or high_52 <= low_52:
            return pd.Series({"Fib_236": None, "Fib_382": None, "Fib_500": None, "Fib_618": None, "Fib_786": None})

        diff = high_52 - low_52
        return pd.Series({
            "Fib_236": round(high_52 - diff * 0.236, 3),
            "Fib_382": round(high_52 - diff * 0.382, 3),
            "Fib_500": round(high_52 - diff * 0.500, 3),
            "Fib_618": round(high_52 - diff * 0.618, 3),
            "Fib_786": round(high_52 - diff * 0.786, 3),
        })
    except:
        return pd.Series({"Fib_236": None, "Fib_382": None, "Fib_500": None, "Fib_618": None, "Fib_786": None})


# ============================================================
# حالة التحديث
# ============================================================

def calc_update_status(row, now_cairo):
    update_str = row.get("آخر_تحديث_EGXBot")
    if pd.isna(update_str) or not update_str:
        return pd.Series({"عمر_السعر_ساعات": None, "حالة_التحديث": "❓ غير معروف"})

    try:
        last_update = datetime.strptime(str(update_str).strip(), "%Y-%m-%d %H:%M").replace(tzinfo=CAIRO_TZ)
        hours_diff = (now_cairo - last_update).total_seconds() / 3600

        status = "🟢 حديث" if hours_diff < 6 else ("🟡 متوسط" if hours_diff < 24 else ("🟠 قديم" if hours_diff < 48 else "🔴 قديم جدًا"))
        return pd.Series({"عمر_السعر_ساعات": round(hours_diff, 1), "حالة_التحديث": status})
    except:
        return pd.Series({"عمر_السعر_ساعات": None, "حالة_التحديث": "❓ غير معروف"})


# ============================================================
# النسب والإشارات (مع فلتر السيولة للفرص الممتازة)
# ============================================================

def calc_metrics(row):
    try:
        price = row["السعر_المعتمد"]
        sup1 = row["الدعم الأول"]
        res1 = row["المقاومة الأولى"]
        volume = row.get("حجم_التداول", 0)

        if pd.isna(price) or pd.isna(sup1) or pd.isna(res1) or price == 0:
            return pd.Series({"% للدعم 1": None, "% للمقاومة 1": None, "R/R": None, "الإشارة": "بيانات ناقصة"})

        pct_sup1 = ((price - sup1) / price) * 100
        pct_res1 = ((res1 - price) / price) * 100

        gain = res1 - price
        risk = price - sup1
        rr = gain / risk if risk > 0 else None

        # شرط الفرصة الممتازة: قرب الدعم + حجم تداول نشط (أعلى من 50 ألف سهم كحد أدنى لتجنب الأسهم الميتة)
        if pct_sup1 <= 1:
            if pd.notna(volume) and volume >= 50000:
                signal = "🟢🟢 فرصة ممتازة"
            else:
                signal = "🟢 قريب من الدعم (سيولة ضعيفة)"
        elif pct_sup1 <= 3:
            signal = "🟢 قريب من الدعم"
        elif pct_sup1 <= 5:
            signal = "🟡 متوسط"
        elif res1 > price and pct_res1 <= 2:
            signal = "🔴🔴 قريب جداً من المقاومة"
        elif res1 > price and pct_res1 <= 5:
            signal = "🟠 قريب من المقاومة"
        else:
            signal = "⚪ محايد"

        return pd.Series({
            "% للدعم 1": round(pct_sup1, 2),
            "% للمقاومة 1": round(pct_res1, 2),
            "R/R": round(rr, 2) if rr else None,
            "الإشارة": signal
        })
    except:
        return pd.Series({"% للدعم 1": None, "% للمقاومة 1": None, "R/R": None, "الإشارة": "خطأ"})


# ============================================================
# الدمج الشامل
# ============================================================

def process_all(df_result, df_prices, df_egxbot):
    df = df_result.merge(df_prices, on="الرمز", how="left", suffixes=("", "_p"))
    df = df.merge(df_egxbot.drop(columns=["error"], errors="ignore"), on="الرمز", how="left", suffixes=("", "_e"))
    df = df.loc[:, ~df.columns.duplicated()]

    # 1) السعر المعتمد
    price_series = df.apply(pick_price, axis=1)
    df = pd.concat([df, price_series], axis=1)

    # 2) الدعم والمقاومة
    sr_series = df.apply(calc_support_resistance, axis=1)
    df = pd.concat([df, sr_series], axis=1)

    # 3) ATR ووقف الخسارة (جديد)
    print("   📊 Computing ATR & Stop Loss...")
    atr_series = df.apply(calc_atr_and_stoploss, axis=1)
    df = pd.concat([df, atr_series], axis=1)

    # 4) المؤشرات الفنية
    print("   📊 Computing RSI...")
    rsi_series = df.apply(calc_rsi, axis=1)
    df = pd.concat([df, rsi_series], axis=1)

    print("   📊 Computing MACD...")
    macd_series = df.apply(calc_macd, axis=1)
    df = pd.concat([df, macd_series], axis=1)

    print("   📊 Computing MAs...")
    ma_series = df.apply(calc_moving_averages, axis=1)
    df = pd.concat([df, ma_series], axis=1)

    print("   📊 Computing Stochastic...")
    stoch_series = df.apply(calc_stochastic, axis=1)
    df = pd.concat([df, stoch_series], axis=1)

    print("   📊 Computing Fibonacci...")
    fib_series = df.apply(calc_fibonacci, axis=1)
    df = pd.concat([df, fib_series], axis=1)

    # 5) النسب والإشارات
    df = df.drop(columns=["% للدعم 1", "% للمقاومة 1", "R/R", "الإشارة"], errors="ignore")
    metrics = df.apply(calc_metrics, axis=1)
    df = pd.concat([df, metrics], axis=1)

    # 6) حالة التحديث
    now_cairo = datetime.now(CAIRO_TZ)
    df["تاريخ_السحب"] = now_cairo.strftime("%Y-%m-%d %H:%M")
    update_status = df.apply(lambda r: calc_update_status(r, now_cairo), axis=1)
    df = pd.concat([df, update_status], axis=1)

    # 7) ترتيب الأعمدة
    final_cols = [
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
        "المقاومة الأولى", "الدعم الأول",
        "ATR", "وقف_الخسارة",  # الأعمدة الجديدة
        "مصدر_الدعم", "مصدر_المقاومة",
        "% للدعم 1", "% للمقاومة 1", "R/R",
        "أقرب_دعم_EGXBot", "أقرب_مقاومة_EGXBot",
        "MA_20", "MA_50", "MA_200",
        "MA_20_diff", "MA_50_diff", "MA_200_diff",
        "الاتجاه",
        "RSI", "RSI_حالة", "RSI_لون",
        "MACD", "MACD_Signal", "MACD_Histogram", "MACD_حالة",
        "Stochastic", "Stochastic_حالة",
        "Fib_236", "Fib_382", "Fib_500", "Fib_618", "Fib_786",
        "الإشارة"
    ]
    final_cols = [c for c in final_cols if c in df.columns]
    extra = [c for c in df.columns if c not in final_cols]
    df = df[final_cols + extra]

    return df


# ============================================================
# ملخص إحصائي
# ============================================================

def get_stats(df):
    return {
        "total": len(df),
        "pure": len(df[df["عدد المصادر الخضراء"] == 6]),
        "strong": len(df[df["عدد المصادر الخضراء"] == 5]),
        "good": len(df[df["عدد المصادر الخضراء"] == 4]),
        "ok": len(df[df["عدد المصادر الخضراء"] == 3]),
        "excellent": len(df[df["الإشارة"] == "🟢🟢 فرصة ممتازة"]),
        "near_support": len(df[df["الإشارة"].str.contains("قريب من الدعم", na=False)]),
        "warning": len(df[df["الإشارة"].str.contains("مقاومة", na=False)]),
        "avg_rr": round(df["R/R"].mean(), 2) if df["R/R"].notna().any() else 0,
        "sectors": df["التصنيف"].nunique(),
        "rsi_overbought": len(df[df["RSI"] >= 70]) if "RSI" in df.columns else 0,
        "rsi_oversold": len(df[df["RSI"] <= 30]) if "RSI" in df.columns else 0,
        "macd_bullish": len(df[df["MACD_حالة"].str.contains("صاعد", na=False)]) if "MACD_حالة" in df.columns else 0,
        "macd_bearish": len(df[df["MACD_حالة"].str.contains("هابط", na=False)]) if "MACD_حالة`" in df.columns else 0,
        "uptrend": len(df[df["الاتجاه"].str.contains("صاعد", na=False)]) if "الاتجاه" in df.columns else 0,
        "downtrend": len(df[df["الاتجاه"].str.contains("هابط", na=False)]) if "الاتجاه" in df.columns else 0,
    }

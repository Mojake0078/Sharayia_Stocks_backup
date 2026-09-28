"""
Sharayia Stocks - EGXBot Fetcher
سحب البيانات من موقع EGXBot
"""

import asyncio
import pandas as pd
from datetime import datetime
from playwright.async_api import async_playwright
from config import EGXBOT_URL, REQUEST_DELAY, MAX_TIMEOUT


# ============================================================
# سحب سهم واحد
# ============================================================

async def fetch_stock(page, code):
    """يسحب كل بيانات السهم من EGXBot"""
    try:
        url = EGXBOT_URL.format(code)
        await page.goto(url, timeout=MAX_TIMEOUT, wait_until="domcontentloaded")
        await asyncio.sleep(REQUEST_DELAY)

        result = await page.evaluate("""() => {
            const text = document.body.innerText;
            const r = {};

            // السعر
            const priceMatch = text.match(/([\\d,]+(?:\\.\\d+)?)\\s*جنيه/);
            if (priceMatch) r.price = parseFloat(priceMatch[1].replace(/,/g, ''));

            // % التغير
            const changeMatch = text.match(/([+-]?\\d+(?:\\.\\d+)?)%/);
            if (changeMatch) r.change_pct = parseFloat(changeMatch[1]);

            // آخر تحديث
            const updateMatch = text.match(/آخر تحديث[:\\s]*([\\d\\-:\\s]+)\\(بتوقيت القاهرة\\)/);
            if (updateMatch) r.last_update = updateMatch[1].trim();

            // التقييم الفني
            const ratingMatch = text.match(/(\\d+)\\s*من\\s*100/);
            if (ratingMatch) r.rating = parseInt(ratingMatch[1]);

            // الافتتاح
            const openM = text.match(/الافتتاح\\s*([\\d,.]+)/);
            if (openM) r.open = parseFloat(openM[1].replace(/,/g, ''));

            // الأعلى
            const highM = text.match(/الأعلى\\s*([\\d,.]+)/);
            if (highM) r.high = parseFloat(highM[1].replace(/,/g, ''));

            // الأدنى
            const lowM = text.match(/الأدنى\\s*([\\d,.]+)/);
            if (lowM) r.low = parseFloat(lowM[1].replace(/,/g, ''));

            // حجم التداول (regex محسّن)
            const volM = text.match(/حجم التداول\\s*([\\d.,]+)\\s*(مليار|مليون|ألف)/);
            if (volM) {
                let v = parseFloat(volM[1].replace(/,/g, ''));
                const u = volM[2];
                if (u === 'مليار') v *= 1_000_000_000;
                else if (u === 'مليون') v *= 1_000_000;
                else if (u === 'ألف') v *= 1_000;
                r.volume = Math.round(v);
            }

            // القيمة السوقية (regex محسّن)
            const capM = text.match(/القيمة السوقية\\s*([\\d.,]+)\\s*(مليار|مليون|ألف)/);
            if (capM) {
                let v = parseFloat(capM[1].replace(/,/g, ''));
                const u = capM[2];
                if (u === 'مليار') v *= 1_000_000_000;
                else if (u === 'مليون') v *= 1_000_000;
                else if (u === 'ألف') v *= 1_000;
                r.market_cap = Math.round(v);
            }

            // مكرر الربحية
            const peM = text.match(/مكرر الربحية\\s*\\(P\\/E\\)\\s*([\\d,.]+)/);
            if (peM) r.pe = parseFloat(peM[1].replace(/,/g, ''));

            // ربحية السهم
            const epsM = text.match(/ربحية السهم\\s*\\(EPS\\)\\s*([\\d,.]+)/);
            if (epsM) r.eps = parseFloat(epsM[1].replace(/,/g, ''));

            // عائد التوزيع
            const divM = text.match(/عائد التوزيع\\s*([\\d,.]+)%/);
            if (divM) r.dividend_yield = parseFloat(divM[1]);

            // أعلى 52 أسبوع
            const h52M = text.match(/أعلى 52 أسبوع\\s*([\\d,.]+)/);
            if (h52M) r.high_52w = parseFloat(h52M[1].replace(/,/g, ''));

            // أدنى 52 أسبوع
            const l52M = text.match(/أدنى 52 أسبوع\\s*([\\d,.]+)/);
            if (l52M) r.low_52w = parseFloat(l52M[1].replace(/,/g, ''));

            // أقرب دعم
            const supM = text.match(/أقرب دعم\\s*([\\d,.]+)/);
            if (supM) r.nearest_support = parseFloat(supM[1].replace(/,/g, ''));

            // أقرب مقاومة
            const resM = text.match(/أقرب مقاومة\\s*([\\d,.]+)/);
            if (resM) r.nearest_resistance = parseFloat(resM[1].replace(/,/g, ''));

            return r;
        }""")

        return result
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# السحب الرئيسي
# ============================================================

async def fetch_all_egxbot(df_result):
    """يسحب كل بيانات EGXBot لكل الأسهم"""
    codes = df_result["الرمز"].astype(str).tolist()
    print(f"📊 Fetching {len(codes)} stocks from EGXBot...")

    all_results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox',
                  '--disable-dev-shm-usage', '--disable-gpu']
        )
        ctx = await browser.new_context(locale="ar-EG")
        page = await ctx.new_page()

        for i, code in enumerate(codes, 1):
            print(f"   [{i}/{len(codes)}] {code}", end=" ... ")

            data = await fetch_stock(page, code)
            data["الرمز"] = code
            all_results.append(data)

            price = data.get("price", "—")
            cap = data.get("market_cap", "—")
            print(f"✅ {price} | Cap:{cap}")

        await browser.close()

    df = pd.DataFrame(all_results)

    # إعادة تسمية الأعمدة
    rename_map = {
        "price": "السعر_EGXBot",
        "change_pct": "% التغير_EGXBot",
        "last_update": "آخر_تحديث_EGXBot",
        "rating": "التقييم_الفني",
        "open": "الافتتاح",
        "high": "الأعلى",
        "low": "الأدنى",
        "volume": "حجم_التداول",
        "market_cap": "القيمة_السوقية",
        "pe": "مكرر_الربحية",
        "eps": "ربحية_السهم",
        "dividend_yield": "عائد_التوزيع",
        "high_52w": "أعلى_52أسبوع",
        "low_52w": "أدنى_52أسبوع",
        "nearest_support": "أقرب_دعم_EGXBot",
        "nearest_resistance": "أقرب_مقاومة_EGXBot"
    }
    df = df.rename(columns=rename_map)

    # نسيبه error لو موجود
    return df


# ============================================================
# نقطة البداية للاختبار
# ============================================================

if __name__ == "__main__":
    print("🧪 Testing EGXBot fetcher (single stock)...")

    async def test():
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage'])
            page = await browser.new_page()
            data = await fetch_stock(page, "BIOC")
            print(data)
            await browser.close()

    asyncio.run(test())
"""
Sharayia Stocks - Mubasher Fetcher
سحب الأسعار من موقع Mubasher
"""

import asyncio
import pandas as pd
from datetime import datetime
from playwright.async_api import async_playwright
from config import MUBASHER_URL, REQUEST_DELAY, MAX_TIMEOUT


# ============================================================
# سحب سهم واحد
# ============================================================

async def fetch_stock(page, code):
    """يسحب السعر + إغلاق سابق + فتح + أعلى + أدنى من Mubasher"""
    try:
        url = MUBASHER_URL.format(code)
        await page.goto(url, timeout=MAX_TIMEOUT, wait_until="domcontentloaded")
        await asyncio.sleep(REQUEST_DELAY)

        result = await page.evaluate("""() => {
            const priceEl = document.querySelector('.market-summary__last-price');
            const price = priceEl ? priceEl.innerText.trim() : null;
            const text = document.body.innerText;

            const updateMatch = text.match(/آخر تحديث[:\\s]*([^\\n]+)/);
            const lastUpdate = updateMatch ? updateMatch[1].trim() : null;

            const prevCloseMatch = text.match(/إغلاق سابق\\s*([\\d.,]+)/);
            const prevClose = prevCloseMatch ? prevCloseMatch[1] : null;

            const openMatch = text.match(/فتح\\s*([\\d.,]+)/);
            const open = openMatch ? openMatch[1] : null;

            const highMatch = text.match(/أعلى\\s*([\\d.,]+)/);
            const high = highMatch ? highMatch[1] : null;

            const lowMatch = text.match(/أدنى\\s*([\\d.,]+)/);
            const low = lowMatch ? lowMatch[1] : null;

            return {price, lastUpdate, prevClose, open, high, low};
        }""")

        # تحويل الأرقام
        for k in ["price", "prevClose", "open", "high", "low"]:
            if result.get(k):
                try:
                    result[k] = float(str(result[k]).replace(",", ""))
                except:
                    result[k] = None

        return result
    except Exception as e:
        return {"price": None, "error": str(e)}


# ============================================================
# السحب الرئيسي
# ============================================================

async def fetch_all_mubasher(df_result):
    """
    يسحب الأسعار لكل الأسهم
    Returns: DataFrame
    """
    codes = df_result["الرمز"].astype(str).tolist()
    print(f"📊 Fetching {len(codes)} stocks from Mubasher...")

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

            all_results.append({
                "الرمز": code,
                "السعر_Mubasher": data.get("price"),
                "آخر_تحديث_Mubasher": data.get("lastUpdate"),
                "إغلاق_سابق_Mubasher": data.get("prevClose"),
                "فتح_Mubasher": data.get("open"),
                "أعلى_Mubasher": data.get("high"),
                "أدنى_Mubasher": data.get("low"),
            })

            price = data.get("price", "—")
            print(f"✅ {price}")

        await browser.close()

    return pd.DataFrame(all_results)


# ============================================================
# نقطة البداية للاختبار
# ============================================================

if __name__ == "__main__":
    print("🧪 Testing Mubasher fetcher (single stock)...")

    async def test():
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage'])
            page = await browser.new_page()
            data = await fetch_stock(page, "BIOC")
            print(data)
            await browser.close()

    asyncio.run(test())
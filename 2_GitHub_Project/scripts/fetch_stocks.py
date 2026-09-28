"""
Sharayia Stocks - Fetch Stocks from Website
سحب قائمة الأسهم الـشرعية+ من الموقع (شهري)
"""

import os
import asyncio
import pandas as pd
from datetime import datetime
from playwright.async_api import async_playwright

from config import (
    STOCKS_URL, DATA_DIR, DF_RESULT_FILE,
    LAST_FETCH_FILE, SOURCES, MIN_GREEN, REQUEST_DELAY, CAIRO_TZ,
)


async def fetch_stocks_from_website():
    """يسحب كل الأسهم من stocks.templatesnippet.com"""

    print("=" * 70)
    print("📥 Fetching stocks from website...")
    print("=" * 70)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox',
                  '--disable-dev-shm-usage', '--disable-gpu']
        )
        ctx = await browser.new_context(
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0 Safari/537.36"),
            viewport={"width": 1366, "height": 900},
            locale="ar-EG",
        )
        page = await ctx.new_page()

        try:
            await page.goto(STOCKS_URL, timeout=60000, wait_until="networkidle")
            await asyncio.sleep(3)

            # إغلاق النافذة المنبثقة
            try:
                await page.click("text=فهمت، متابعة", timeout=3000)
                await asyncio.sleep(1)
                print("   ✅ Closed popup")
            except Exception:
                pass

            # تحميل كل الأسهم
            print("📜 Loading all stocks...")
            last_count = 0
            same_streak = 0

            for i in range(60):
                clicked = await page.evaluate("""() => {
                    const btns = Array.from(document.querySelectorAll('button, a'));
                    const btn = btns.find(b => (b.innerText || '').includes('تحميل المزيد'));
                    if (!btn) return 'DONE';
                    btn.scrollIntoView({block: 'center'});
                    btn.click();
                    return 'CLICKED';
                }""")

                if clicked == 'DONE':
                    break

                await asyncio.sleep(1.8)

                count = await page.evaluate(
                    "() => document.querySelectorAll('div.group.rounded-2xl.border').length"
                )
                print(f"   ↳ {count} cards")

                if count == last_count:
                    same_streak += 1
                    if same_streak >= 3:
                        break
                else:
                    same_streak = 0
                last_count = count

            final_count = await page.evaluate(
                "() => document.querySelectorAll('div.group.rounded-2xl.border').length"
            )
            print(f"\n📦 Total cards: {final_count}\n")

            # استخراج البيانات
            js_code = """
            (sources) => {
                const MIN = 3;
                const results = [];
                const cards = document.querySelectorAll('div.group.rounded-2xl.border');

                cards.forEach(card => {
                    const greenBadges = card.querySelectorAll(
                        'span[class*="bg-green-"], span[class*="text-green-"]'
                    );
                    const green = new Set();

                    greenBadges.forEach(b => {
                        const t = (b.innerText || "").trim();
                        if (sources.includes(t)) green.add(t);
                    });

                    if (green.size < MIN) return;

                    const rawLines = (card.innerText || "")
                        .split(/\\r?\\n/)
                        .map(l => l.trim())
                        .filter(l => l.length > 0);

                    let name = "غير معروف";
                    let code = "";
                    let category = "";

                    for (const ln of rawLines) {
                        if (sources.includes(ln)) continue;
                        if (ln.includes("جروب الأسهم")) continue;
                        if (ln === "التوزيعات" || ln === "قارن" || ln === "التفاصيل") continue;
                        if (/^[A-Z]{2,6}$/.test(ln) && !code) { code = ln; continue; }
                        if (!category && (ln.includes("و") || ln.includes("خدمات") ||
                                          ln.includes("صناعة") || ln.includes("مالية") ||
                                          ln.includes("تعليم") || ln.includes("عقار") ||
                                          ln.includes("طاقة") || ln.includes("بنوك") ||
                                          ln.includes("منسوجات") || ln.includes("أغذية") ||
                                          ln.includes("أدوية") || ln.includes("سياحة") ||
                                          ln.includes("بتروكيماويات") || ln.includes("كيماويات") ||
                                          ln.includes("مواد") || ln.includes("مرافق") ||
                                          ln.includes("تكنولوجيا") || ln.includes("اتصالات") ||
                                          ln.includes("نقل") || ln.includes("رعاية"))) {
                            category = ln; continue;
                        }
                        if (name === "غير معروف" && ln.length > 2) name = ln;
                    }

                    results.push({
                        code: code || "-",
                        name: name,
                        category: category || "-",
                        green_count: green.size,
                        green_sources: Array.from(green).join(" ، ")
                    });
                });

                return results;
            }
            """

            data = await page.evaluate(js_code, SOURCES)

            if not data:
                print("⚠️ No stocks found")
                return pd.DataFrame()

            df = pd.DataFrame(data)
            df = df.sort_values("green_count", ascending=False).reset_index(drop=True)
            df.index += 1

            df = df.rename(columns={
                "code": "الرمز",
                "name": "اسم السهم",
                "category": "التصنيف",
                "green_count": "عدد المصادر الخضراء",
                "green_sources": "المصادر المتفقة"
            })

            return df

        finally:
            await browser.close()
            print("🔒 Browser closed")


async def fetch_and_save():
    """السحب + الحفظ + الرفع"""

    # 1) السحب
    df = await fetch_stocks_from_website()

    if df.empty:
        print("❌ No stocks fetched")
        return None

    print(f"✅ Fetched {len(df)} stocks")
    print(f"\n📊 Distribution:")
    print(df["عدد المصادر الخضراء"].value_counts().sort_index(ascending=False).to_string())

    # 2) الحفظ
    os.makedirs(DATA_DIR, exist_ok=True)

    # CSV
    df.to_csv(DF_RESULT_FILE, index=False, encoding="utf-8-sig")
    print(f"\n💾 Saved: {DF_RESULT_FILE}")

    # 3) تحديث تاريخ آخر سحب
    with open(LAST_FETCH_FILE, "w") as f:
        f.write(datetime.now(CAIRO_TZ).strftime("%Y-%m-%d %H:%M:%S"))
    print(f"📅 Updated: {LAST_FETCH_FILE}")

    return df


if __name__ == "__main__":
    asyncio.run(fetch_and_save())
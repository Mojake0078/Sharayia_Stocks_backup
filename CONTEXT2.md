# 🎯 Sharayia Stocks — Context File 2

## 🎯 الإضافات المقترحة

### 1. وصف تفصيلي لكل ملف Python

مش بس اسم الملف، بل:
- وظيفته الأساسية
- أهم الدوال جواه
- المدخلات والمخرجات

**مثال:**

### `scripts/process.py`
**الوظيفة:** دمج البيانات + حساب كل المؤشرات الفنية

**الدوال الرئيسية:**
- `pick_price()` - اختيار السعر المعتمد من المصادر
- `calc_rsi()` - حساب RSI
- `calc_macd()` - حساب MACD
- `calc_moving_averages()` - MA 20/50/200
- `calc_fibonacci()` - مستويات Fibonacci
- `process_all()` - الدالة الرئيسية

**المدخل:** df_result + df_prices + df_egxbot
**المخرج:** df_final_complete (DataFrame)

---

### 2. هيكل الـ Excel (10 أوراق)

اللي الشات لازم يعرفه:

1. Dashboard - إحصائيات + 4 رسوم
2. البيانات الكاملة - 84 سهم × 44 عمود
3. فرص الشراء - أفضل 40 سهم قريبين من الدعم
4. تحذير مقاومة - أفضل 40 سهم قريبين من المقاومة
5. أفضل R-R - أفضل 40 سهم حسب R/R
6. الأسهم النقية - 18 سهم (6/6)
7. حسب القطاع - 28 قطاع
8. حسب الفئة - 4 فئات
9. السجل التاريخي - سجل يومي
10. دليل الاستخدام - شرح كامل

---

### 3. المكتبات المستخدمة (requirements)

    playwright==1.48.0
    pandas==2.2.3
    openpyxl==3.1.5
    xlsxwriter==3.2.0
    nest-asyncio==1.6.0
    matplotlib==3.9.2
    numpy==2.1.3
    requests==2.32.3
    google-auth==2.35.0
    google-auth-oauthlib==1.2.1
    google-api-python-client==2.149.0
    pyarrow==17.0.0

---

### 4. خطوات الحصول على OAuth Refresh Token

عشان لو احتاج يجدده:

1. Google Cloud Console
2. OAuth Consent Screen (External)
3. إضافة Test Users
4. إنشاء OAuth Client (Desktop)
5. الحصول على Client ID + Secret
6. تشغيل Script للحصول على Refresh Token
7. حفظه في GitHub Secrets + Vercel

---

### 5. محتوى ملفات الـ Workflows

    # daily_update.yml
    - Cron: 0 14 * * * (5 مساءً القاهرة)
    - يشغل: python scripts/main.py --mode daily

    # monthly_update.yml
    - Cron: 0 3 1 * * (أول كل شهر 5 صباحاً)
    - يشغل: python scripts/main.py --mode monthly

---

### 6. هيكل Google Drive الكامل

    📁 MyDrive/
    ├── 📁 Sharayia_stocks-github/     ← ملفات GitHub Actions اليومية
    │   ├── bot_data.json
    │   ├── df_result.csv
    │   ├── df_final_complete.csv
    │   ├── stocks_analysis_final.xlsx
    │   ├── dashboard_charts.png
    │   └── last_stock_fetch.txt
    │
    └── 📁 Sharayia_Stocks_backup/     ← ملفات النقل والتوثيق
        ├── CONTEXT.md
        ├── CONTEXT2.md
        ├── CONTEXT3.md
        ├── 📁 1_Colab_Project/
        ├── 📁 2_GitHub_Project/
        └── 📁 3_Telegram_Project/

---

### 7. مشاكل معروفة والحلول (FAQ)

**❓ ليه CSV مش pkl؟**
→ pkl بيتأثر بإصدار pandas، CSV ثابت

**❓ ليه OAuth مش Service Account؟**
→ Google منعت Service Account من رفع ملفات على Drive شخصي

**❓ ليه xlsxwriter مش openpyxl؟**
→ openpyxl فيه مشاكل توافق مع pandas

**❓ الوقت في الرسائل مش مضبوط؟**
→ تأكد إن CAIRO_TZ = ZoneInfo("Africa/Cairo")

**❓ البوت بيقول "لا توجد بيانات"؟**
→ شغّل /update أو استنى GitHub Actions

---

### 8. ملاحظات عن الفريم الزمني (مهم للخطوة القادمة)

**قرار الفريم**

**السوق المصري:** 4.5 ساعات فقط
- 1 ساعة = 4 شمعات (غير عملي)
- يومي = ✅ الأنسب
- أسبوعي = ✅ للتأكيد

**القرار:** يومي + أسبوعي
**السبب:** متاح للمستخدم العادي، دقة عالية

---

### 9. خطة كشف الاختراقات (اللي هنشتغل عليه)

**المرحلة القادمة: Breakout Detection**

**5 أنواع إشارات مقترحة:**
1. 🚀 Breakout - اختراق مؤكد
2. ⚡ Pre-Breakout - على وشك
3. 🔄 Retest - إعادة اختبار
4. ⏳ Compression - انضغاط
5. 📉 Breakdown - اختراق هابط

**الشروط:**
- السعر يكسر المقاومة
- RVOL > 1.5
- RSI > 60
- شمعة قوية

**الأهداف:** 2-3 أهداف لكل إشارة
**الستوب:** 1.5 × ATR أو تحت آخر قاع

---

### 10. ملاحظات أمنية

**🔐 بيانات حساسة (لا تشاركها):**
- GitHub PAT: ghp_...
- OAuth Client Secret
- OAuth Refresh Token
- Telegram Bot Token

**✅ آمن للمشاركة:**
- Drive Folder ID
- Chat ID
- Repository URL

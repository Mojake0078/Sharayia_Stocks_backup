# 🎯 Sharayia Stocks — Context File

## 📌 نظرة عامة

مشروع تحليل الأسهم الشرعية في البورصة المصرية.

- **84 سهم** × **6 مصادر شرعية**
- يعمل **تلقائيًا** يوميًا 5 مساءً (القاهرة)
- يبعت تقارير على **تلجرام**
- يحفظ الملفات على **Google Drive**

---

## 🔗 الروابط المهمة

### GitHub
- المشروع الرئيسي: https://github.com/Mojake0078/sharayia-stocks
- بوت تلجرام: https://github.com/Mojake0078/sharayia-telegram-bot

### Vercel
- Dashboard: https://vercel.com/mojake0078s-projects/sharayia-telegram-bot
- URL: https://sharayia-telegram-bot.vercel.app

### Telegram
- Bot: @Sharayia_Stocks_bot
- Chat ID: 14563001

### Google Drive
- Folder: Sharayia_stocks-github
- Folder ID: 1OJme9_eySTiV4SR0P12_6jpZeR4ZIeLY

---

## 🏗️ البنية التحتية

| المكوّن | الوظيفة |
|---------|---------|
| GitHub Actions | Cron يومي 5 مساءً |
| Vercel | استضافة البوت |
| Google Drive | تخزين (OAuth) |
| Telegram Bot | 14 أمر + 12 زر |

---

## 📁 ملفات المشروع الرئيسي
sharayia-stocks/
├── scripts/
│ ├── config.py
│ ├── drive_utils.py
│ ├── telegram_utils.py
│ ├── fetch_mubasher.py
│ ├── fetch_egxbot.py
│ ├── process.py
│ ├── build_excel.py
│ ├── main.py
│ └── fetch_stocks.py
└── .github/workflows/
├── daily_update.yml
└── monthly_update.yml

text

---

## 📁 ملفات البوت
sharayia-telegram-bot/
├── api/webhook.py
├── requirements.txt
├── vercel.json
└── pyproject.toml

text

---

## 🔑 GitHub Secrets (8)

- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID
- GDRIVE_CREDENTIALS_JSON
- DRIVE_FOLDER_ID
- GH_PAT
- OAUTH_CLIENT_ID
- OAUTH_CLIENT_SECRET
- OAUTH_REFRESH_TOKEN

---

## 🔑 Vercel Env Variables (9)

- OAUTH_CLIENT_ID
- OAUTH_CLIENT_SECRET
- OAUTH_REFRESH_TOKEN
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID
- DRIVE_FOLDER_ID
- GH_PAT
- GH_REPO = Mojake0078/sharayia-stocks
- GH_WORKFLOW = daily_update.yml

---

## 📱 أوامر البوت (16)

| الأمر | الوظيفة |
|-------|---------|
| /start | ترحيب + القائمة |
| /menu | القائمة الرئيسية |
| /help | كل الأوامر |
| /search CODE | بحث شامل |
| /price CODE | السعر + المؤشرات |
| /stock CODE | تفاصيل كاملة |
| /tech CODE | المؤشرات الفنية |
| /volume CODE | الفوليوم |
| /sector NAME | أسهم قطاع |
| /pure | الأسهم النقية |
| /opportunities | فرص ممتازة |
| /warnings | تحذيرات |
| /top | أفضل 10 R/R |
| /stats | إحصائيات |
| /update | تحديث فوري |
| /about | عن المشروع |

---

## 📊 البيانات

### المصادر الشرعية (6)
1. مصفّى
2. كاشف
3. بنك فيصل
4. أسطول
5. Islamicly / Thndr
6. جروب الأسهم الشرعية فقط

### توزيع الأسهم
- نقية (6/6): 18
- قوية جدًا (5/6): 21
- قوية (4/6): 31
- مقبولة (3/6): 14

### المؤشرات الفنية
- RSI, MACD, MA (20/50/200), Stochastic, Fibonacci, RVOL

---

## 🔄 آلية العمل

### يوميًا الساعة 5 مساءً:
1. GitHub Actions يشتغل
2. يسحب الأسعار من Mubasher + EGXBot
3. يحسب المؤشرات
4. يبني Excel (10 أوراق)
5. يصدر bot_data.json
6. يرفع على Drive
7. يبعت تلجرام

### يدويًا:
- /update في تلجرام

---

## 📂 ملفات Drive
Sharayia_stocks-github/
├── bot_data.json
├── df_result.csv
├── df_final_complete.csv
├── stocks_analysis_final.xlsx
├── dashboard_charts.png
└── last_stock_fetch.txt

text

---

## ⚠️ المشاكل التي اتحلت

| # | المشكلة | الحل |
|:-:|---------|------|
| 1 | Service Account 403 | OAuth |
| 2 | pandas + openpyxl | xlsxwriter |
| 3 | pkl compatibility | CSV |
| 4 | Invalid Grant OAuth | code_verifier ثابت |
| 5 | --mode ناقص | إضافة daily |
| 6 | pyarrow missing | CSV |
| 7 | حرف غريب | إعادة كتابة |
| 8 | Indentation Error | تصحيح المسافات |

---

## 🎯 الخطوات القادمة

| # | الميزة | الأولوية |
|:-:|--------|:--------:|
| 1 | كشف الاختراقات | عالية |
| 2 | Pre-Breakout | عالية |
| 3 | Retest | عالية |
| 4 | Compression | متوسطة |
| 5 | SMC/ICT | عالية |
| 6 | Volume Profile | متوسطة |
| 7 | تنبيهات | عالية |
| 8 | إدارة المخاطر | متوسطة |

---

## 🎯 الفريم الزمني

**السوق المصري:** 10:00 - 14:30 (4.5 ساعة)

| الفريم | عملية؟ |
|:------:|:------:|
| 15 دقيقة | لا |
| 1 ساعة | ضعيف |
| يومي | ممتاز |
| أسبوعي | ممتاز |

**القرار:** يومي + أسبوعي

---

## 💡 تعليمات للشات الجديد

**عند بدء محادثة جديدة:**

1. الصق هذا الملف كامل
2. قل: اقرأ هذا الملف كله أولاً ثم استعد لأي أسئلة
3. اطرح سؤالك

---

## 📌 معلومات إضافية

- الحساب: Mojake0078
- الإيميل: mo7medezat16@gmail.com
- الإصدار: 1.0
- تاريخ الإنشاء: سبتمبر 2026

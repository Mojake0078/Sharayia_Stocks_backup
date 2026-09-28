# 🚀 دليل الإعداد - Sharayia Stocks

## 📋 المتطلبات

قبل البدء، تأكد إن عندك:

- ✅ حساب GitHub
- ✅ بوت تلجرام (من @BotFather)
- ✅ Google Service Account
- ✅ مجلد على Google Drive

---

## 🔐 GitHub Secrets المطلوبة

اذهب إلى:
`Repository → Settings → Secrets and variables → Actions → New repository secret`

| Secret Name | الوصف | كيف تجيبه |
|-------------|-------|-----------|
| `TELEGRAM_BOT_TOKEN` | توكن البوت | @BotFather → /newbot |
| `TELEGRAM_CHAT_ID` | Chat ID | @userinfobot |
| `GDRIVE_CREDENTIALS_JSON` | Service Account JSON | Google Cloud Console |
| `DRIVE_FOLDER_ID` | ID مجلد Drive | من رابط المجلد |

---

## 📱 إعداد بوت تلجرام

### 1. إنشاء البوت:
1. افتح تلجرام
2. ابحث عن `@BotFather`
3. اكتب: `/newbot`
4. اختار اسم للبوت
5. اختار username (ينتهي بـ `bot`)
6. **احفظ الـ Token** (هتحتاجه)

### 2. الحصول على Chat ID:
1. افتح محادثة مع البوت بتاعك
2. اكتب أي رسالة
3. افتح: `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. **احفظ الـ chat_id**

---

## 🔑 إعداد Google Service Account

### 1. إنشاء المشروع:
1. افتح [Google Cloud Console](https://console.cloud.google.com)
2. أنشئ مشروع جديد
3. فعّل **Google Drive API**

### 2. إنشاء Service Account:
1. اذهب إلى `IAM & Admin → Service Accounts`
2. اضغط `Create Service Account`
3. اختار اسم
4. اضغط `Create and Continue`
5. اضغط `Done`

### 3. تحميل الـ JSON Key:
1. اضغط على الـ Service Account
2. اذهب إلى `Keys` tab
3. اضغط `Add Key → Create new key`
4. اختار **JSON**
5. **هيتحمل تلقائيًا** — احفظه

### 4. مشاركة مجلد Drive:
1. افتح Google Drive
2. اختار مجلد المشروع
3. اضغط `Share`
4. الصق **email** الـ Service Account
5. اختار **Editor**
6. **احفظ الـ Folder ID** (من الرابط)

---

## ⏰ الجدولة

| Workflow | التوقيت | المدة |
|----------|---------|-------|
| **Daily Update** | 5:00 PM القاهرة | ~10 دقايق |
| **Monthly Refresh** | 1 من كل شهر، 5:00 ص | ~5 دقايق |

---

## 🎮 أوامر تلجرام

| الأمر | الوظيفة |
|-------|---------|
| `/start` | ترحيب |
| `/today` | تقرير اليوم |
| `/gold` | الأسهم النقية |
| `/opportunities` | فرص ممتازة |
| `/stock BIOC` | تفاصيل سهم |
| `/update` | تشغيل التحديث يدويًا |

---

## ✅ Checklist الإعداد

- [ ] إنشاء Repository على GitHub
- [ ] إضافة الملفات الأساسية
- [ ] إنشاء بوت تلجرام
- [ ] الحصول على Chat ID
- [ ] إنشاء Google Service Account
- [ ] تحميل JSON Key
- [ ] مشاركة مجلد Drive
- [ ] إضافة Secrets على GitHub
- [ ] اختبار Daily Update يدوي
- [ ] التأكد من الإشعار
- [ ] تفعيل الجدولة

---

**آخر تحديث:** 2026-09-13
**الإصدار:** 1.0
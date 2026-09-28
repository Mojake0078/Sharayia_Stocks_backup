"""
Sharayia Stocks - Google Drive Utilities (OAuth)
أدوات التعامل مع Google Drive عبر OAuth
"""

import os
import io
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from config import (
    DRIVE_FOLDER_ID,
    DATA_DIR, REPORTS_DIR, HISTORY_DIR, CHARTS_DIR,
)


# ============================================================
# إعدادات OAuth
# ============================================================
SCOPES = ["https://www.googleapis.com/auth/drive"]
TOKEN_URI = "https://oauth2.googleapis.com/token"


def get_drive_service():
    """يربط Google Drive باستخدام OAuth (حسابك الشخصي)"""
    client_id = os.getenv("OAUTH_CLIENT_ID")
    client_secret = os.getenv("OAUTH_CLIENT_SECRET")
    refresh_token = os.getenv("OAUTH_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        raise Exception("OAuth credentials missing (ID / SECRET / REFRESH_TOKEN)")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=TOKEN_URI,
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )

    # نجدّد الـ Access Token
    creds.refresh(Request())

    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    return service


# ============================================================
# البحث عن ملف
# ============================================================
def find_file(service, filename, folder_id=None):
    """يبحث عن ملف بالاسم"""
    if folder_id is None:
        folder_id = DRIVE_FOLDER_ID

    query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"

    try:
        results = service.files().list(
            q=query,
            fields="files(id, name, size, modifiedTime)",
            pageSize=10,
        ).execute()

        files = results.get("files", [])
        return files[0]["id"] if files else None
    except Exception as e:
        print(f"⚠️ find_file error: {e}")
        return None


# ============================================================
# رفع ملف
# ============================================================
def upload_file(service, local_path, filename=None, folder_id=None):
    """يرفع ملف على Drive (يستبدل لو موجود)"""
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"File not found: {local_path}")

    if filename is None:
        filename = os.path.basename(local_path)

    if folder_id is None:
        folder_id = DRIVE_FOLDER_ID

    existing_id = find_file(service, filename, folder_id)
    media = MediaFileUpload(local_path, resumable=True)

    try:
        if existing_id:
            file = service.files().update(
                fileId=existing_id,
                media_body=media,
            ).execute()
            print(f"   🔄 Updated: {filename}")
        else:
            file_metadata = {
                "name": filename,
                "parents": [folder_id],
            }
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id",
            ).execute()
            print(f"   ⬆️ Uploaded: {filename}")

        return file.get("id")
    except Exception as e:
        print(f"   ❌ Upload error: {e}")
        raise


# ============================================================
# تنزيل ملف
# ============================================================
def download_file(service, filename, local_path, folder_id=None):
    """ينزّل ملف من Drive"""
    if folder_id is None:
        folder_id = DRIVE_FOLDER_ID

    file_id = find_file(service, filename, folder_id)
    if not file_id:
        print(f"   ⚠️ File not found: {filename}")
        return False

    try:
        request = service.files().get_media(fileId=file_id)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        fh = io.FileIO(local_path, "wb")
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        print(f"   ⬇️ Downloaded: {filename}")
        return True
    except Exception as e:
        print(f"   ❌ Download error: {e}")
        return False


# ============================================================
# دوال مساعدة
# ============================================================
def download_data_file(filename):
    """ينزّل ملف من Drive → DATA_DIR"""
    service = get_drive_service()
    local_path = os.path.join(DATA_DIR, filename)
    return download_file(service, filename, local_path)


def upload_data_file(local_path):
    """يرفع ملف على Drive"""
    service = get_drive_service()
    return upload_file(service, local_path)


def upload_report(local_path):
    """يرفع تقرير Excel"""
    service = get_drive_service()
    return upload_file(service, local_path)


def upload_history(local_path):
    """يرفع السجل التاريخي"""
    service = get_drive_service()
    return upload_file(service, local_path)


def upload_chart(local_path):
    """يرفع رسم بياني"""
    service = get_drive_service()
    return upload_file(service, local_path)


def list_files():
    """يعرض كل الملفات في المجلد"""
    service = get_drive_service()
    query = f"'{DRIVE_FOLDER_ID}' in parents and trashed=false"

    try:
        results = service.files().list(
            q=query,
            fields="files(id, name, size, modifiedTime)",
            pageSize=100,
        ).execute()

        files = results.get("files", [])
        print(f"\n📁 Files in Drive ({len(files)}):")
        for f in files:
            size_kb = int(f.get("size", 0)) / 1024 if f.get("size") else 0
            print(f"   📄 {f['name']} ({size_kb:.1f} KB)")
        return files
    except Exception as e:
        print(f"❌ List error: {e}")
        return []
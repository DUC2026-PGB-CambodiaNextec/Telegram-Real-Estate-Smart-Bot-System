# -*- coding: utf-8 -*-
"""
Telegram Real Estate Smart Bot System - Khmer / English
Full Updated Version

Features:
- Beautiful Khmer menu design
- User property browsing flow
- Lead collection + SQLite storage
- Admin / Staff roles
- Admin Login button with password
- Admin dashboard auto display after login
- Lead list / lead detail
- PDF lead report generation for download / print
- Auto notify Admin + Staff when new lead arrives
- Fast user support buttons: contact staff, quality, warranty, modification, services, promotions
- Smart FAQ auto-reply for construction quality, discounts, services, and house improvement

Install:
  pip install -r requirements.txt

.env example:
  TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
  ADMIN_PHONE=0714174813
  ADMIN_PASSWORD=1234
  ADMIN_IDS=8399608471
  STAFF_IDS=
  DB_PATH=real_estate_leads.db
  PDF_DIR=lead_pdfs
  BOT_NAME=Real Estate Smart Bot
  COMPANY_NAME=Cheatzdevelopment Real Estate

Run:
  python src/app.py
"""

from __future__ import annotations

import os
import re
import html
import sqlite3
import datetime
import logging
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# PDF support
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False


# ============================================================
# Config
# ============================================================
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ADMIN_PHONE = os.getenv(
    "ADMIN_PHONE",
    "077252759 / 088345678"
).strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1234").strip()
DB_PATH = Path(os.getenv("DB_PATH", "real_estate_leads.db")).resolve()
PDF_DIR = Path(os.getenv("PDF_DIR", "lead_pdfs")).resolve()

BOT_NAME = os.getenv("BOT_NAME", "Real Estate Smart Bot")
COMPANY_NAME = os.getenv("COMPANY_NAME", "Cheatzdevelopment Real Estate")
DIV = "━━━━━━━━━━━━━━━━━━━━"

ADMIN_IDS = {
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}
STAFF_IDS = {
    int(x.strip()) for x in os.getenv("STAFF_IDS", "").split(",")
    if x.strip().isdigit()
}

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Conversation states
NAME, PHONE, ADDRESS, VISIT_DATE, ADMIN_LOGIN = range(5)


# ============================================================
# Data
# ============================================================
PROPERTIES = {
    "borey": {
        "title": "🏘️ បុរី",
        "desc": "ផ្ទះបុរីសម្រាប់គ្រួសារ មានទីតាំងល្អ សុវត្ថិភាព និងងាយស្រួលរស់នៅ។",
        "items": [
            {"name": "ផ្ទះល្វែង LA", "price": "$58,000", "size": "4m × 16m", "bed": "2 បន្ទប់គេង", "area": "64㎡", "image_url": "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=1200"},
            {"name": "ផ្ទះអាជីវកម្ម SH", "price": "$98,000", "size": "4.2m × 18m", "bed": "3 បន្ទប់គេង", "area": "75.6㎡", "image_url": "https://images.unsplash.com/photo-1605276374104-dee2a0ed3cd6?w=1200"},
            {"name": "Twin Villa", "price": "$168,000", "size": "8m × 20m", "bed": "4 បន្ទប់គេង", "area": "160㎡", "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1200"},
        ],
    },
    "villa": {
        "title": "🏡 វីឡា",
        "desc": "វីឡាទំនើប ស្អាត ប្រណិត សាកសមសម្រាប់គ្រួសារធំ និងការរស់នៅបែបឯកជន។",
        "items": [
            {"name": "វីឡាកូនកាត់", "price": "$145,000", "size": "7m × 20m", "bed": "4 បន្ទប់គេង", "area": "140㎡", "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1200"},
            {"name": "Queen Villa", "price": "$280,000", "size": "12m × 25m", "bed": "5 បន្ទប់គេង", "area": "300㎡", "image_url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1200"},
            {"name": "King Villa", "price": "$450,000", "size": "15m × 30m", "bed": "6 បន្ទប់គេង", "area": "450㎡", "image_url": "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=1200"},
        ],
    },
    "rent": {
        "title": "🏠 ផ្ទះជួល",
        "desc": "ផ្ទះជួលតម្លៃសមរម្យ សម្រាប់ស្នាក់នៅ ឬធ្វើអាជីវកម្ម។",
        "items": [
            {"name": "បន្ទប់ជួល", "price": "$80 / ខែ", "size": "4m × 5m", "bed": "1 បន្ទប់", "area": "20㎡", "image_url": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=1200"},
            {"name": "ផ្ទះជួលគ្រួសារ", "price": "$250 / ខែ", "size": "4m × 16m", "bed": "2 បន្ទប់គេង", "area": "64㎡", "image_url": "https://images.unsplash.com/photo-1560184897-ae75f418493e?w=1200"},
            {"name": "ផ្ទះជួលអាជីវកម្ម", "price": "$500 / ខែ", "size": "5m × 20m", "bed": "3 បន្ទប់", "area": "100㎡", "image_url": "https://images.unsplash.com/photo-1494526585095-c41746248156?w=1200"},
        ],
    },
}

PAYMENTS = {
    "full": "💵 បង់ប្រាក់ពេញ",
    "installment": "🏦 បង់រំលោះ",
}


FAQ_DATA = {
    "quality": {
        "title": "🏗️ គុណភាពសំណង់",
        "body": (
            "🏗️ *គុណភាពសំណង់*\n"
            f"{DIV}\n"
            "✅ គម្រោងផ្ទះត្រូវបានសាងសង់តាមស្តង់ដារសំណង់\n"
            "✅ មានគ្រឹះរឹងមាំ សមស្របតាមប្រភេទផ្ទះ\n"
            "✅ ប្រើសម្ភារៈសំណង់ដែលបានជ្រើសរើសត្រឹមត្រូវ\n"
            "✅ មានការត្រួតពិនិត្យគុណភាពក្នុងដំណាក់កាលសាងសង់\n\n"
            "📌 បើចង់បានព័ត៌មានបច្ចេកទេសលម្អិត សូមចុច *💬 ទាក់ទង Staff*។"
        ),
    },
    "warranty": {
        "title": "🛠️ ធានា/ជួសជុល",
        "body": (
            "🛠️ *ការធានា និងជួសជុល*\n"
            f"{DIV}\n"
            "✅ មានសេវាកម្មជំនួយក្រោយពេលទិញ\n"
            "✅ អាចសួរព័ត៌មានអំពីរយៈពេលធានា និងលក្ខខណ្ឌជួសជុល\n"
            "✅ Staff នឹងជួយពិនិត្យ និងបញ្ជាក់តាមប្រភេទផ្ទះ/គម្រោង\n\n"
            "📞 សម្រាប់ព័ត៌មានធានាពិតប្រាកដ សូមទាក់ទង Staff ដើម្បីបញ្ជាក់លើកិច្ចសន្យា។"
        ),
    },
    "modify": {
        "title": "🏡 កែលម្អផ្ទះ",
        "body": (
            "🏡 *ការកែលម្អផ្ទះ*\n"
            f"{DIV}\n"
            "✅ អ្នកប្រើប្រាស់អាចសួរពីការកែខាងក្នុងផ្ទះ\n"
            "✅ អាចសួរពីការបន្ថែមបន្ទប់ ផ្ទះបាយ ឬការតុបតែង\n"
            "✅ ការកែលម្អខ្លះអាចត្រូវការការអនុញ្ញាតពីគម្រោង/បុរី\n\n"
            "📌 Staff អាចពន្យល់លក្ខខណ្ឌមុនធ្វើការកែលម្អ។"
        ),
    },
    "services": {
        "title": "📋 សេវាកម្ម",
        "body": (
            "📋 *សេវាកម្មដែលមាន*\n"
            f"{DIV}\n"
            "✅ ណែនាំគម្រោងផ្ទះ\n"
            "✅ ពិគ្រោះតម្លៃ និងបង់រំលោះ\n"
            "✅ កំណត់ថ្ងៃមកមើលផ្ទះ\n"
            "✅ ជំនួយឯកសារ និងការទំនាក់ទំនង Staff\n"
            "✅ PDF Lead Report សម្រាប់ Admin/Staff\n\n"
            "☎️ ចុច *💬 ទាក់ទង Staff* ដើម្បីទទួលជំនួយរហ័ស។"
        ),
    },
    "promo": {
        "title": "🎁 Promotion / Discount",
        "body": (
            "🎁 *Promotion / Discount*\n"
            f"{DIV}\n"
            "✅ អាចមានការបញ្ចុះតម្លៃតាមគម្រោង\n"
            "✅ អាចមានការថែមជូន ឬលក្ខខណ្ឌពិសេស\n"
            "✅ Promotion អាចផ្លាស់ប្តូរតាមពេលវេលា និងប្រភេទផ្ទះ\n\n"
            "📞 សូមទាក់ទង Staff ដើម្បីទទួលតម្លៃ និងការថែមជូនចុងក្រោយ។"
        ),
    },
}


# ============================================================
# Helpers
# ============================================================
def now_text() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def is_admin(user_id: int | None) -> bool:
    return bool(user_id and user_id in ADMIN_IDS)


def is_staff(user_id: int | None) -> bool:
    return bool(user_id and (user_id in STAFF_IDS or user_id in ADMIN_IDS))


def require_admin_text() -> str:
    return "⛔ អ្នកមិនមានសិទ្ធិ Admin ទេ។ សូម Login ឬដាក់ ADMIN_IDS ក្នុង .env។"


def require_staff_text() -> str:
    return "⛔ សម្រាប់ Staff/Admin ប៉ុណ្ណោះ។"


# ============================================================
# Database
# ============================================================
def db_connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def column_exists(con: sqlite3.Connection, table: str, column: str) -> bool:
    cols = {row[1] for row in con.execute(f"PRAGMA table_info({table})").fetchall()}
    return column in cols


def add_column_if_missing(con: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    if not column_exists(con, table, column):
        con.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_database() -> None:
    """Create/upgrade database tables."""
    with db_connect() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                telegram_name TEXT,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                address TEXT,
                role TEXT DEFAULT 'user',
                first_seen TEXT,
                last_seen TEXT,
                lead_count INTEGER DEFAULT 0,
                is_old_user INTEGER DEFAULT 0
            )
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                telegram_name TEXT,
                user_status TEXT,
                property_type TEXT,
                property_name TEXT,
                property_price TEXT,
                property_size TEXT,
                payment_type TEXT,
                customer_name TEXT,
                phone TEXT,
                address TEXT,
                visit_date TEXT,
                status TEXT DEFAULT 'new',
                assigned_to INTEGER,
                assigned_name TEXT,
                pdf_path TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )

        con.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                telegram_name TEXT,
                role TEXT,
                action TEXT,
                detail TEXT,
                created_at TEXT
            )
            """
        )

        add_column_if_missing(con, "users", "role", "TEXT DEFAULT 'user'")
        add_column_if_missing(con, "leads", "user_status", "TEXT DEFAULT 'old'")
        add_column_if_missing(con, "leads", "status", "TEXT DEFAULT 'new'")
        add_column_if_missing(con, "leads", "assigned_to", "INTEGER")
        add_column_if_missing(con, "leads", "assigned_name", "TEXT")
        add_column_if_missing(con, "leads", "pdf_path", "TEXT")
        add_column_if_missing(con, "leads", "updated_at", "TEXT")

        for admin_id in ADMIN_IDS:
            con.execute(
                """
                INSERT INTO users(telegram_id, telegram_name, role, first_seen, last_seen)
                VALUES (?, ?, 'admin', ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET role='admin', last_seen=excluded.last_seen
                """,
                (admin_id, "Admin", now_text(), now_text()),
            )
        for staff_id in STAFF_IDS:
            con.execute(
                """
                INSERT INTO users(telegram_id, telegram_name, role, first_seen, last_seen)
                VALUES (?, ?, 'staff', ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    role=CASE WHEN role='admin' THEN 'admin' ELSE 'staff' END,
                    last_seen=excluded.last_seen
                """,
                (staff_id, "Staff", now_text(), now_text()),
            )
        con.commit()


def set_user_role(telegram_id: int, role: str, name: str = "") -> None:
    with db_connect() as con:
        con.execute(
            """
            INSERT INTO users(telegram_id, telegram_name, role, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                role=?, telegram_name=COALESCE(NULLIF(?, ''), telegram_name), last_seen=?
            """,
            (telegram_id, name, role, now_text(), now_text(), role, name, now_text()),
        )
        con.commit()


def get_user_role(telegram_id: int) -> str:
    if telegram_id in ADMIN_IDS:
        return "admin"
    if telegram_id in STAFF_IDS:
        return "staff"
    with db_connect() as con:
        row = con.execute("SELECT role FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()
        return row[0] if row and row[0] else "user"


def upsert_user(user) -> str:
    """Save Telegram user and return 'new' or 'old'."""
    now = now_text()
    role = "admin" if user.id in ADMIN_IDS else ("staff" if user.id in STAFF_IDS else "user")
    with db_connect() as con:
        row = con.execute(
            "SELECT telegram_id, lead_count, role FROM users WHERE telegram_id=?",
            (user.id,),
        ).fetchone()
        if row:
            existing_role = row[2] or "user"
            final_role = "admin" if role == "admin" or existing_role == "admin" else ("staff" if role == "staff" or existing_role == "staff" else "user")
            con.execute(
                """
                UPDATE users
                SET telegram_name=?, username=?, first_name=?, last_name=?, last_seen=?, is_old_user=1, role=?
                WHERE telegram_id=?
                """,
                (
                    user.full_name,
                    user.username or "",
                    user.first_name or "",
                    user.last_name or "",
                    now,
                    final_role,
                    user.id,
                ),
            )
            con.commit()
            return "old"

        con.execute(
            """
            INSERT INTO users(
                telegram_id, telegram_name, username, first_name, last_name,
                phone, address, role, first_seen, last_seen, lead_count, is_old_user
            ) VALUES (?, ?, ?, ?, ?, '', '', ?, ?, ?, 0, 0)
            """,
            (
                user.id,
                user.full_name,
                user.username or "",
                user.first_name or "",
                user.last_name or "",
                role,
                now,
                now,
            ),
        )
        con.commit()
        return "new"


def update_user_contact(telegram_id: int, phone: str, address: str) -> None:
    with db_connect() as con:
        con.execute(
            """
            UPDATE users
            SET phone=?, address=?, last_seen=?, is_old_user=1
            WHERE telegram_id=?
            """,
            (phone, address, now_text(), telegram_id),
        )
        con.commit()


def get_user_profile(telegram_id: int) -> dict | None:
    with db_connect() as con:
        con.row_factory = sqlite3.Row
        row = con.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()
        return dict(row) if row else None


def get_last_lead(telegram_id: int) -> dict | None:
    with db_connect() as con:
        con.row_factory = sqlite3.Row
        row = con.execute(
            "SELECT * FROM leads WHERE telegram_id=? ORDER BY id DESC LIMIT 1",
            (telegram_id,),
        ).fetchone()
        return dict(row) if row else None


def save_lead(data: dict) -> int:
    now = now_text()
    with db_connect() as con:
        cur = con.execute(
            """
            INSERT INTO leads(
                telegram_id, telegram_name, user_status, property_type, property_name,
                property_price, property_size, payment_type, customer_name,
                phone, address, visit_date, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?, ?)
            """,
            (
                data.get("telegram_id"),
                data.get("telegram_name"),
                data.get("user_status", "old"),
                data.get("property_type"),
                data.get("property_name"),
                data.get("property_price"),
                data.get("property_size"),
                data.get("payment_type"),
                data.get("customer_name"),
                data.get("phone"),
                data.get("address"),
                data.get("visit_date"),
                now,
                now,
            ),
        )
        con.execute(
            """
            UPDATE users
            SET lead_count = COALESCE(lead_count, 0) + 1,
                phone=?, address=?, last_seen=?, is_old_user=1
            WHERE telegram_id=?
            """,
            (data.get("phone"), data.get("address"), now, data.get("telegram_id")),
        )
        con.commit()
        return int(cur.lastrowid)


def update_lead_pdf_path(lead_id: int, pdf_path: str) -> None:
    with db_connect() as con:
        con.execute("UPDATE leads SET pdf_path=?, updated_at=? WHERE id=?", (pdf_path, now_text(), lead_id))
        con.commit()


def update_lead_status(lead_id: int, status: str) -> bool:
    with db_connect() as con:
        cur = con.execute("UPDATE leads SET status=?, updated_at=? WHERE id=?", (status, now_text(), lead_id))
        con.commit()
        return cur.rowcount > 0


def assign_lead(lead_id: int, staff_id: int, staff_name: str = "") -> bool:
    with db_connect() as con:
        cur = con.execute(
            "UPDATE leads SET assigned_to=?, assigned_name=?, status='assigned', updated_at=? WHERE id=?",
            (staff_id, staff_name, now_text(), lead_id),
        )
        con.commit()
        return cur.rowcount > 0


def get_lead(lead_id: int) -> dict | None:
    with db_connect() as con:
        con.row_factory = sqlite3.Row
        row = con.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
        return dict(row) if row else None


def list_recent_leads(limit: int = 10) -> list[dict]:
    with db_connect() as con:
        con.row_factory = sqlite3.Row
        rows = con.execute("SELECT * FROM leads ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]


def get_dashboard_counts() -> dict[str, int]:
    with db_connect() as con:
        return {
            "total_users": con.execute("SELECT COUNT(*) FROM users").fetchone()[0],
            "new_users": con.execute("SELECT COUNT(*) FROM users WHERE COALESCE(lead_count,0)=0 AND COALESCE(is_old_user,0)=0").fetchone()[0],
            "old_users": con.execute("SELECT COUNT(*) FROM users WHERE COALESCE(is_old_user,0)=1 OR COALESCE(lead_count,0)>0").fetchone()[0],
            "total_leads": con.execute("SELECT COUNT(*) FROM leads").fetchone()[0],
            "new_leads": con.execute("SELECT COUNT(*) FROM leads WHERE COALESCE(status,'new')='new'").fetchone()[0],
            "assigned_leads": con.execute("SELECT COUNT(*) FROM leads WHERE status='assigned'").fetchone()[0],
            "closed_leads": con.execute("SELECT COUNT(*) FROM leads WHERE status='closed'").fetchone()[0],
            "admins": con.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0],
            "staff": con.execute("SELECT COUNT(*) FROM users WHERE role='staff'").fetchone()[0],
        }



def log_activity(user_id: int | None, name: str = "", action: str = "", detail: str = "") -> None:
    """Save user/admin/staff usage history for Admin Dashboard."""
    try:
        role = get_user_role(int(user_id)) if user_id else "guest"
        with db_connect() as con:
            con.execute(
                """
                INSERT INTO activity_logs(telegram_id, telegram_name, role, action, detail, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, name, role, action, detail[:500], now_text()),
            )
            con.commit()
    except Exception as e:
        logger.warning("Cannot log activity: %s", e)


def list_activity_logs(limit: int = 15) -> list[dict]:
    with db_connect() as con:
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT * FROM activity_logs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def activity_history_text(limit: int = 15) -> str:
    logs = list_activity_logs(limit)
    if not logs:
        return "🕘 មិនទាន់មានប្រវត្តិការប្រើប្រាស់ទេ។"
    lines = ["🕘 *Admin Usage History*", DIV]
    for row in logs:
        lines.append(
            f"#{row.get('id')} | `{row.get('role')}` | {row.get('telegram_name') or row.get('telegram_id')}\n"
            f"➡️ {row.get('action')} — {row.get('detail') or '-'}\n"
            f"🕒 {row.get('created_at')}"
        )
    return "\n\n".join(lines)


# ============================================================
# Keyboards
# ============================================================
def main_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🏠 ចាប់ផ្តើម"), KeyboardButton("🏘️ មើលគម្រោង")],
            [KeyboardButton("💬 ទាក់ទង Staff"), KeyboardButton("📋 សេវាកម្ម")],
            [KeyboardButton("🖼️ រូបផ្ទះគំរូ"), KeyboardButton("🕘 ប្រវត្តិ")],
            [KeyboardButton("🏗️ គុណភាពសំណង់"), KeyboardButton("🛠️ ធានា/ជួសជុល")],
            [KeyboardButton("🏡 កែលម្អផ្ទះ"), KeyboardButton("🎁 Promotion")],
            [KeyboardButton("🔐 Admin Login"), KeyboardButton("👨‍💼 Staff Panel")],
        ],
        resize_keyboard=True,
        input_field_placeholder="ជ្រើសរើស Menu...",
    )


def admin_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📊 Admin Data"), KeyboardButton("📋 Leads")],
            [KeyboardButton("📄 Download PDF"), KeyboardButton("🕘 History")],
            [KeyboardButton("👥 Staff")],
            [KeyboardButton("🏠 User Menu")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Admin Panel...",
    )


def staff_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📋 Leads"), KeyboardButton("📄 Download PDF")],
            [KeyboardButton("☎️ ទំនាក់ទំនង"), KeyboardButton("🏠 User Menu")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Staff Panel...",
    )


def property_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🏘️ បុរី", callback_data="type:borey")],
            [InlineKeyboardButton("🏡 វីឡា", callback_data="type:villa")],
            [InlineKeyboardButton("🏠 ផ្ទះជួល", callback_data="type:rent")],
            [InlineKeyboardButton("☎️ ទាក់ទងបុគ្គលិក", callback_data="contact")],
        ]
    )



def quick_info_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🏗️ គុណភាពសំណង់", callback_data="faq:quality")],
            [InlineKeyboardButton("🛠️ ធានា/ជួសជុល", callback_data="faq:warranty")],
            [InlineKeyboardButton("🏡 កែលម្អផ្ទះ", callback_data="faq:modify")],
            [InlineKeyboardButton("📋 សេវាកម្ម", callback_data="faq:services")],
            [InlineKeyboardButton("🎁 Promotion", callback_data="faq:promo")],
            [InlineKeyboardButton("💬 ទាក់ទង Staff", callback_data="staff:contact")],
        ]
    )



def gallery_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🏘️ រូប បុរី", callback_data="gallery:borey")],
            [InlineKeyboardButton("🏡 រូប វីឡា", callback_data="gallery:villa")],
            [InlineKeyboardButton("🏠 រូប ផ្ទះជួល", callback_data="gallery:rent")],
        ]
    )


def gallery_list_keyboard(property_type: str) -> InlineKeyboardMarkup:
    rows = []
    for index, item in enumerate(PROPERTIES[property_type]["items"]):
        rows.append([InlineKeyboardButton(f"🖼️ {item['name']} • {item['price']}", callback_data=f"gallery:{property_type}:{index}")])
    rows.append([InlineKeyboardButton("🔙 ត្រឡប់", callback_data="gallery:root")])
    return InlineKeyboardMarkup(rows)


def property_list_keyboard(property_type: str) -> InlineKeyboardMarkup:
    rows = []
    for index, item in enumerate(PROPERTIES[property_type]["items"]):
        rows.append([InlineKeyboardButton(f"{item['name']} • {item['price']}", callback_data=f"property:{property_type}:{index}")])
    rows.append([InlineKeyboardButton("🔙 ត្រឡប់ទៅជម្រើស", callback_data="back:types")])
    return InlineKeyboardMarkup(rows)


def payment_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(PAYMENTS["full"], callback_data="payment:full")],
            [InlineKeyboardButton(PAYMENTS["installment"], callback_data="payment:installment")],
            [InlineKeyboardButton("🔙 ជ្រើសផ្ទះវិញ", callback_data="back:property_list")],
        ]
    )


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ បញ្ចូលព័ត៌មានណាត់មើលផ្ទះ", callback_data="form:start")],
            [InlineKeyboardButton("🔙 ជ្រើសការបង់ប្រាក់វិញ", callback_data="back:payment")],
        ]
    )


def lead_action_keyboard(lead_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📄 PDF", callback_data=f"pdf:{lead_id}"),
                InlineKeyboardButton("✅ Close", callback_data=f"close:{lead_id}"),
            ],
            [InlineKeyboardButton("📋 Leads List", callback_data="admin:leads")],
        ]
    )


def admin_dashboard_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📋 View Leads", callback_data="admin:leads")],
            [InlineKeyboardButton("🕘 Usage History", callback_data="admin:history")],
            [InlineKeyboardButton("🔄 Refresh Dashboard", callback_data="admin:dashboard")],
        ]
    )


# ============================================================
# Text Builders
# ============================================================
def welcome_text(first_name: str) -> str:
    return (
        f"👋 សួស្តី {first_name}!\n{DIV}\n"
        f"🏡 *{BOT_NAME}*\n"
        "ប្រព័ន្ធ Bot ឆ្លាតវៃសម្រាប់អចលនទ្រព្យ\n\n"
        "✨ អ្នកអាចធ្វើការ៖\n"
        "✅ ជ្រើសរើស បុរី / វីឡា / ផ្ទះជួល\n"
        "✅ មើលតម្លៃ និងទំហំផ្ទះ\n"
        "✅ ជ្រើសបង់ប្រាក់ពេញ ឬបង់រំលោះ\n"
        "✅ បញ្ចូលឈ្មោះ លេខទូរស័ព្ទ អាសយដ្ឋាន\n"
        "✅ កំណត់ថ្ងៃមកមើលផ្ទះ\n"
        "✅ សួរពីគុណភាពសំណង់/ធានា/Promotion បានភ្លាមៗ\n"
        "✅ ទាក់ទង Staff បានលឿន\n\n"
        "👇 សូមជ្រើសរើសប្រភេទ ឬព័ត៌មានដែលអ្នកចង់បាន"
    )


def old_user_text(first_name: str, profile: dict | None, last_lead: dict | None) -> str:
    lead_count = profile.get("lead_count", 0) if profile else 0
    txt = (
        f"👋 សួស្តីម្ដងទៀត {first_name}!\n{DIV}\n"
        "✅ ប្រព័ន្ធបានស្គាល់អ្នកជា *Old User*\n"
        f"📌 ចំនួនសំណើចាស់: {lead_count}\n\n"
    )
    if last_lead:
        txt += (
            "🧾 សំណើចុងក្រោយរបស់អ្នក៖\n"
            f"🏡 {last_lead.get('property_name')}\n"
            f"💰 {last_lead.get('property_price')}\n"
            f"📞 {last_lead.get('phone')}\n"
            f"📅 {last_lead.get('visit_date')}\n\n"
        )
    txt += "👇 អ្នកអាចជ្រើសគម្រោងថ្មី ឬទាក់ទងបុគ្គលិកបាន"
    return txt


def admin_dashboard_text() -> str:
    counts = get_dashboard_counts()
    return (
        "👑 *ADMIN DASHBOARD*\n"
        f"{DIV}\n"
        f"👥 Total Users: `{counts['total_users']}`\n"
        f"🆕 New Users: `{counts['new_users']}`\n"
        f"🔁 Old Users: `{counts['old_users']}`\n\n"
        f"🧾 Total Leads: `{counts['total_leads']}`\n"
        f"🟢 New Leads: `{counts['new_leads']}`\n"
        f"🟡 Assigned Leads: `{counts['assigned_leads']}`\n"
        f"✅ Closed Leads: `{counts['closed_leads']}`\n\n"
        f"🛡️ Admins: `{counts['admins']}`\n"
        f"👨‍💼 Staff: `{counts['staff']}`\n\n"
        "⚡ *Quick Commands*\n"
        "`/leads` - មើល leads ចុងក្រោយ\n"
        "`/lead ID` - មើល detail\n"
        "`/pdf ID` - Download PDF\n"
        "`/close ID` - Close lead\n"
        "`/assign LEAD_ID STAFF_ID` - Assign staff"
    )


def property_type_text(property_type: str) -> str:
    data = PROPERTIES[property_type]
    return f"{data['title']}\n{DIV}\n{data['desc']}\n\n👇 សូមជ្រើសរើសគម្រោង/ម៉ូឌែលខាងក្រោម៖"


def property_detail_text(property_type: str, index: int) -> str:
    item = PROPERTIES[property_type]["items"][index]
    return (
        f"🏡 *{item['name']}*\n{DIV}\n"
        f"💰 តម្លៃ: `{item['price']}`\n"
        f"📐 ទំហំដី/ផ្ទះ: `{item['size']}`\n"
        f"📏 ផ្ទៃសរុប: `{item['area']}`\n"
        f"🛏️ {item['bed']}\n\n"
        "👇 សូមជ្រើសរើសរបៀបបង់ប្រាក់"
    )


def summary_text(data: dict) -> str:
    return (
        "📋 *សេចក្តីសង្ខេបការជ្រើសរើស*\n"
        f"{DIV}\n"
        f"🏷️ ប្រភេទ: {data.get('property_type_title')}\n"
        f"🏡 ផ្ទះ: {data.get('property_name')}\n"
        f"💰 តម្លៃ: {data.get('property_price')}\n"
        f"📐 ទំហំ: {data.get('property_size')}\n"
        f"💳 ការបង់ប្រាក់: {data.get('payment_type')}\n\n"
        "បន្ទាប់មក សូមបញ្ចូលព័ត៌មានរបស់អ្នក ដើម្បីឲ្យបុគ្គលិកទាក់ទង។"
    )


def final_text(data: dict, lead_id: int) -> str:
    return (
        "✅ *បានទទួលព័ត៌មានរបស់អ្នករួចហើយ!*\n"
        f"{DIV}\n"
        f"🧾 លេខសំណើ: `#{lead_id}`\n"
        f"👤 ឈ្មោះ: {data.get('customer_name')}\n"
        f"📞 ទូរស័ព្ទ: {data.get('phone')}\n"
        f"📍 ទីលំនៅបច្ចុប្បន្ន: {data.get('address')}\n"
        f"📅 ថ្ងៃមកមើលផ្ទះ: {data.get('visit_date')}\n\n"
        f"☎️ ព័ត៌មានបន្ថែម: `{ADMIN_PHONE}`\n\n"
        "អរគុណច្រើន សម្រាប់ការចាប់អារម្មណ៍លើគម្រោងរបស់យើង 🙏"
    )


def lead_detail_text(lead: dict) -> str:
    return (
        f"🧾 *Lead #{lead.get('id')}*\n"
        f"{DIV}\n"
        f"📌 Status: `{lead.get('status') or 'new'}`\n"
        f"👤 Customer: {lead.get('customer_name')}\n"
        f"📞 Phone: `{lead.get('phone')}`\n"
        f"📍 Address: {lead.get('address')}\n"
        f"📅 Visit Date: {lead.get('visit_date')}\n\n"
        f"🏷️ Type: {lead.get('property_type')}\n"
        f"🏡 Property: {lead.get('property_name')}\n"
        f"💰 Price: {lead.get('property_price')}\n"
        f"📐 Size: {lead.get('property_size')}\n"
        f"💳 Payment: {lead.get('payment_type')}\n\n"
        f"👨‍💼 Assigned: {lead.get('assigned_name') or lead.get('assigned_to') or 'None'}\n"
        f"🕒 Created: {lead.get('created_at')}"
    )


def leads_list_text(leads: list[dict]) -> str:
    if not leads:
        return "📭 មិនទាន់មាន Leads ទេ។"
    lines = ["📋 *Recent Leads*", DIV]
    for lead in leads:
        lines.append(
            f"#{lead.get('id')} | {lead.get('status') or 'new'} | "
            f"{lead.get('customer_name') or '-'} | {lead.get('phone') or '-'} | "
            f"{lead.get('property_name') or '-'}"
        )
    lines.append("\nប្រើ `/lead ID` ឬ `/pdf ID`")
    return "\n".join(lines)


# ============================================================
# PDF
# ============================================================
def generate_lead_pdf(lead: dict) -> Path:
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab not installed. Run: pip install reportlab")

    PDF_DIR.mkdir(parents=True, exist_ok=True)
    lead_id = lead.get("id")
    pdf_path = PDF_DIR / f"lead_{lead_id}.pdf"

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Title"],
        fontSize=18,
        leading=22,
        alignment=1,
        textColor=colors.HexColor("#0f172a"),
    )
    subtitle_style = ParagraphStyle(
        "SubtitleCustom",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=colors.HexColor("#475569"),
    )
    normal = styles["Normal"]

    def p(value: Any) -> Paragraph:
        return Paragraph(html.escape(str(value or "")), normal)

    story = [
        Paragraph(COMPANY_NAME, title_style),
        Paragraph("Telegram Real Estate Lead Report", subtitle_style),
        Spacer(1, 0.4 * cm),
    ]

    header_data = [
        ["Lead ID", f"#{lead_id}", "Status", lead.get("status") or "new"],
        ["Created At", lead.get("created_at") or "", "Updated At", lead.get("updated_at") or ""],
    ]

    header_table = Table(header_data, colWidths=[3 * cm, 5 * cm, 3 * cm, 6 * cm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0f2fe")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))
    story += [header_table, Spacer(1, 0.5 * cm)]

    rows = [
        ["Customer Name", p(lead.get("customer_name"))],
        ["Phone", p(lead.get("phone"))],
        ["Address", p(lead.get("address"))],
        ["Visit Date", p(lead.get("visit_date"))],
        ["Telegram Name", p(lead.get("telegram_name"))],
        ["Telegram ID", p(lead.get("telegram_id"))],
        ["Property Type", p(lead.get("property_type"))],
        ["Property Name", p(lead.get("property_name"))],
        ["Property Price", p(lead.get("property_price"))],
        ["Property Size", p(lead.get("property_size"))],
        ["Payment Type", p(lead.get("payment_type"))],
        ["Assigned To", p(lead.get("assigned_name") or lead.get("assigned_to") or "None")],
    ]

    table = Table(rows, colWidths=[4.2 * cm, 12.8 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#0f172a")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))

    story += [
        Paragraph("Customer & Property Information", styles["Heading2"]),
        table,
        Spacer(1, 0.6 * cm),
        Paragraph("Admin Note:", styles["Heading3"]),
        Paragraph("This PDF can be downloaded and printed for customer follow-up.", normal),
    ]

    doc.build(story)
    update_lead_pdf_path(int(lead_id), str(pdf_path))
    return pdf_path


async def send_lead_pdf(chat_id: int, context: ContextTypes.DEFAULT_TYPE, lead_id: int, caption: str = "") -> None:
    lead = get_lead(lead_id)
    if not lead:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ Lead #{lead_id} មិនមានទេ។")
        return

    try:
        pdf_path = generate_lead_pdf(lead)
        with open(pdf_path, "rb") as f:
            await context.bot.send_document(
                chat_id=chat_id,
                document=f,
                filename=f"lead_{lead_id}.pdf",
                caption=caption or f"📄 Lead #{lead_id} PDF Report\nអាច Download និង Print បាន។",
            )
    except Exception as e:
        logger.exception("PDF error")
        await context.bot.send_message(chat_id=chat_id, text=f"❌ PDF error: {e}\n\nសូម install: pip install reportlab")


# ============================================================
# Notification
# ============================================================
async def notify_team_new_lead(context: ContextTypes.DEFAULT_TYPE, lead_id: int) -> None:
    lead = get_lead(lead_id)
    if not lead:
        return

    targets = sorted(ADMIN_IDS | STAFF_IDS)
    if not targets:
        logger.info("No ADMIN_IDS/STAFF_IDS set. Skip notify.")
        return

    text = (
        "🚨 *New Customer Lead!*\n"
        f"{DIV}\n"
        f"🧾 Lead: `#{lead_id}`\n"
        f"👤 {lead.get('customer_name')}\n"
        f"📞 `{lead.get('phone')}`\n"
        f"🏡 {lead.get('property_name')}\n"
        f"📅 {lead.get('visit_date')}\n\n"
        f"Commands: `/lead {lead_id}` | `/pdf {lead_id}`"
    )

    for uid in targets:
        try:
            await context.bot.send_message(chat_id=uid, text=text, parse_mode=ParseMode.MARKDOWN, reply_markup=lead_action_keyboard(lead_id))
            await send_lead_pdf(uid, context, lead_id, caption=f"📄 Lead #{lead_id} PDF Report")
        except Exception as e:
            logger.warning("Cannot notify %s: %s", uid, e)


# ============================================================
# Handlers
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    log_activity(user.id, user.full_name, "start", "/start or user menu")
    context.user_data.clear()
    user_status = upsert_user(user)
    context.user_data["user_status"] = user_status

    role = get_user_role(user.id)
    if role == "admin":
        await update.message.reply_text("🛡️ Admin detected. Welcome back!", reply_markup=admin_reply_keyboard())
    elif role == "staff":
        await update.message.reply_text("👨‍💼 Staff detected. Welcome back!", reply_markup=staff_reply_keyboard())

    if user_status == "new":
        await update.message.reply_text("🆕 អ្នកជា New User — ព័ត៌មានរបស់អ្នកត្រូវបានរក្សាទុកហើយ។", reply_markup=main_reply_keyboard())
        await update.message.reply_text(welcome_text(user.first_name), parse_mode=ParseMode.MARKDOWN, reply_markup=main_reply_keyboard())
    else:
        profile = get_user_profile(user.id)
        last_lead = get_last_lead(user.id)
        await update.message.reply_text(old_user_text(user.first_name, profile, last_lead), parse_mode=ParseMode.MARKDOWN, reply_markup=main_reply_keyboard())

    await update.message.reply_text("📌 ជ្រើសរើសប្រភេទផ្ទះ៖", reply_markup=property_type_keyboard())


async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    role = get_user_role(user.id)
    await update.message.reply_text(f"🆔 Your Telegram ID: `{user.id}`\n👤 Name: {user.full_name}\n🔐 Role: `{role}`", parse_mode=ParseMode.MARKDOWN)


async def admin_login_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("🔐 សូមបញ្ចូល Admin Password:", reply_markup=main_reply_keyboard())
    return ADMIN_LOGIN


async def verify_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    password = clean_text(update.message.text)
    user = update.effective_user

    if password == ADMIN_PASSWORD:
        ADMIN_IDS.add(user.id)
        set_user_role(user.id, "admin", user.full_name)
        log_activity(user.id, user.full_name, "admin_login", "Admin logged in")
        await update.message.reply_text("✅ Admin Login Success\n\n👑 Welcome Admin!", reply_markup=admin_reply_keyboard())
        await update.message.reply_text(admin_dashboard_text(), parse_mode=ParseMode.MARKDOWN, reply_markup=admin_dashboard_keyboard())
    else:
        await update.message.reply_text("❌ Password មិនត្រឹមត្រូវ", reply_markup=main_reply_keyboard())

    return ConversationHandler.END


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(require_admin_text())
        return
    await update.message.reply_text(admin_dashboard_text(), parse_mode=ParseMode.MARKDOWN, reply_markup=admin_dashboard_keyboard())
    await update.message.reply_text("🛡️ Admin Menu", reply_markup=admin_reply_keyboard())


async def staff_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_staff(update.effective_user.id):
        await update.message.reply_text(require_staff_text())
        return
    await update.message.reply_text(
        "👨‍💼 *Staff Panel*\n"
        f"{DIV}\n"
        "📋 /leads - Recent leads\n"
        "🧾 /lead ID - Lead detail\n"
        "📄 /pdf ID - Download PDF\n"
        "✅ /close ID - Close lead",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=staff_reply_keyboard(),
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_staff(update.effective_user.id):
        await update.message.reply_text(require_staff_text())
        return
    await update.message.reply_text(admin_dashboard_text(), parse_mode=ParseMode.MARKDOWN, reply_markup=admin_dashboard_keyboard())


async def leads_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_staff(update.effective_user.id):
        await update.message.reply_text(require_staff_text())
        return
    await update.message.reply_text(leads_list_text(list_recent_leads(10)), parse_mode=ParseMode.MARKDOWN)



async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(require_admin_text())
        return
    log_activity(update.effective_user.id, update.effective_user.full_name, "view_history", "/history")
    await update.message.reply_text(activity_history_text(20), parse_mode=ParseMode.MARKDOWN, reply_markup=admin_dashboard_keyboard())


async def gallery_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    log_activity(user.id, user.full_name, "open_gallery", "User opened sample house gallery")
    await update.message.reply_text(
        "🖼️ *រូបផ្ទះគំរូ*\n"
        f"{DIV}\n"
        "សូមជ្រើសរើសប្រភេទផ្ទះ ដើម្បីមើលរូបគំរូ។",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=gallery_type_keyboard(),
    )


async def lead_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_staff(update.effective_user.id):
        await update.message.reply_text(require_staff_text())
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("ប្រើ: /lead ID\nឧទាហរណ៍: /lead 1")
        return
    lead_id = int(context.args[0])
    lead = get_lead(lead_id)
    if not lead:
        await update.message.reply_text(f"❌ Lead #{lead_id} មិនមានទេ។")
        return
    await update.message.reply_text(lead_detail_text(lead), parse_mode=ParseMode.MARKDOWN, reply_markup=lead_action_keyboard(lead_id))


async def pdf_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_staff(update.effective_user.id):
        await update.message.reply_text(require_staff_text())
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("ប្រើ: /pdf ID\nឧទាហរណ៍: /pdf 1")
        return
    await send_lead_pdf(update.effective_chat.id, context, int(context.args[0]))


async def close_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_staff(update.effective_user.id):
        await update.message.reply_text(require_staff_text())
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("ប្រើ: /close ID\nឧទាហរណ៍: /close 1")
        return
    lead_id = int(context.args[0])
    if update_lead_status(lead_id, "closed"):
        await update.message.reply_text(f"✅ Lead #{lead_id} closed.")
    else:
        await update.message.reply_text(f"❌ Lead #{lead_id} មិនមានទេ។")


async def assign_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(require_admin_text())
        return
    if len(context.args) < 2 or not context.args[0].isdigit() or not context.args[1].isdigit():
        await update.message.reply_text("ប្រើ: /assign LEAD_ID STAFF_ID\nឧទាហរណ៍: /assign 1 123456789")
        return
    lead_id = int(context.args[0])
    staff_id = int(context.args[1])
    if assign_lead(lead_id, staff_id, f"Staff {staff_id}"):
        STAFF_IDS.add(staff_id)
        set_user_role(staff_id, "staff", f"Staff {staff_id}")
        await update.message.reply_text(f"✅ Assigned Lead #{lead_id} to Staff `{staff_id}`", parse_mode=ParseMode.MARKDOWN)
        try:
            await context.bot.send_message(chat_id=staff_id, text=f"📌 អ្នកត្រូវបាន assign Lead #{lead_id}\nប្រើ /lead {lead_id} ឬ /pdf {lead_id}")
        except Exception:
            pass
    else:
        await update.message.reply_text(f"❌ Lead #{lead_id} មិនមានទេ។")


async def setstaff_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(require_admin_text())
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("ប្រើ: /setstaff TELEGRAM_ID")
        return
    staff_id = int(context.args[0])
    STAFF_IDS.add(staff_id)
    set_user_role(staff_id, "staff", f"Staff {staff_id}")
    await update.message.reply_text(f"✅ Staff added: `{staff_id}`", parse_mode=ParseMode.MARKDOWN)


async def setadmin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(require_admin_text())
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("ប្រើ: /setadmin TELEGRAM_ID")
        return
    admin_id = int(context.args[0])
    ADMIN_IDS.add(admin_id)
    set_user_role(admin_id, "admin", f"Admin {admin_id}")
    await update.message.reply_text(f"✅ Admin added: `{admin_id}`", parse_mode=ParseMode.MARKDOWN)


async def remove_role_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(require_admin_text())
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("ប្រើ: /remove_role TELEGRAM_ID")
        return
    uid = int(context.args[0])
    ADMIN_IDS.discard(uid)
    STAFF_IDS.discard(uid)
    set_user_role(uid, "user", f"User {uid}")
    await update.message.reply_text(f"✅ Role removed: `{uid}`", parse_mode=ParseMode.MARKDOWN)


async def faq_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str) -> None:
    item = FAQ_DATA.get(key)
    user = update.effective_user
    if user:
        log_activity(user.id, user.full_name, "faq", key)
    text = item["body"] if item else "សូមជ្រើសរើសព័ត៌មានពី menu ខាងក្រោម។"

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=quick_info_keyboard(),
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_reply_keyboard(),
        )


async def quick_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "⚡ *Quick Help Menu*\n"
        f"{DIV}\n"
        "ជ្រើសរើសព័ត៌មានដែលអ្នកចង់សួរ៖",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=quick_info_keyboard(),
    )


async def services_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await faq_reply(update, context, "services")


async def quality_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await faq_reply(update, context, "quality")


async def warranty_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await faq_reply(update, context, "warranty")


async def promo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await faq_reply(update, context, "promo")


async def staff_contact_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    log_activity(user.id, user.full_name, "request_staff", "User requested staff support")
    text_user = (
        "💬 *ទាក់ទង Staff រហ័ស*\n"
        f"{DIV}\n"
        "សូមរង់ចាំបន្តិច Staff/Admin នឹងទាក់ទងអ្នកវិញ។\n\n"
        f"📞 លេខទំនាក់ទំនង: `{ADMIN_PHONE}`\n"
        "អ្នកក៏អាចបំពេញព័ត៌មានណាត់មើលផ្ទះតាម menu ផងដែរ។"
    )

    alert = (
        "📣 *User requests Staff Support*\n"
        f"{DIV}\n"
        f"👤 Name: {user.full_name}\n"
        f"🆔 ID: `{user.id}`\n"
        f"🔗 Username: @{user.username if user.username else '-'}\n\n"
        "សូមទាក់ទង User នេះឲ្យបានរហ័ស។"
    )

    targets = sorted(ADMIN_IDS | STAFF_IDS)
    for uid in targets:
        try:
            await context.bot.send_message(chat_id=uid, text=alert, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.warning("Cannot send staff request to %s: %s", uid, e)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text_user,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=quick_info_keyboard(),
        )
    else:
        await update.message.reply_text(
            text_user,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_reply_keyboard(),
        )


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = (
        "☎️ *ព័ត៌មានទំនាក់ទំនង*\n"
        f"{DIV}\n"
        "📞 Smart: `077252759`\n"
        "📞 Cellcard: `088345678`\n"
        f"📞 Hotline: `{ADMIN_PHONE}`\n"
        "⏰ ម៉ោងធ្វើការ: 8:00 AM - 6:00 PM\n"
        "📍 អ្នកអាចណាត់មកមើលផ្ទះតាម Bot នេះបាន។"
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=property_type_keyboard())
    else:
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=main_reply_keyboard())


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "admin:dashboard":
        if not is_staff(user_id):
            await query.edit_message_text(require_staff_text())
            return ConversationHandler.END
        await query.edit_message_text(admin_dashboard_text(), parse_mode=ParseMode.MARKDOWN, reply_markup=admin_dashboard_keyboard())
        return ConversationHandler.END

    if data == "admin:history":
        if not is_admin(user_id):
            await query.edit_message_text(require_admin_text())
            return ConversationHandler.END
        log_activity(user_id, query.from_user.full_name, "view_history", "Inline admin history")
        await query.edit_message_text(activity_history_text(20), parse_mode=ParseMode.MARKDOWN, reply_markup=admin_dashboard_keyboard())
        return ConversationHandler.END

    if data == "admin:leads":
        if not is_staff(user_id):
            await query.edit_message_text(require_staff_text())
            return ConversationHandler.END
        await query.edit_message_text(leads_list_text(list_recent_leads()), parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END

    if data.startswith("pdf:"):
        if not is_staff(user_id):
            await query.edit_message_text(require_staff_text())
            return ConversationHandler.END
        await send_lead_pdf(query.message.chat_id, context, int(data.split(":", 1)[1]))
        return ConversationHandler.END

    if data.startswith("close:"):
        if not is_staff(user_id):
            await query.edit_message_text(require_staff_text())
            return ConversationHandler.END
        lead_id = int(data.split(":", 1)[1])
        update_lead_status(lead_id, "closed")
        await query.edit_message_text(f"✅ Lead #{lead_id} closed.")
        return ConversationHandler.END

    if data == "contact":
        await contact(update, context)
        return ConversationHandler.END

    if data.startswith("faq:"):
        await faq_reply(update, context, data.split(":", 1)[1])
        return ConversationHandler.END

    if data == "staff:contact":
        await staff_contact_request(update, context)
        return ConversationHandler.END

    if data == "gallery:root":
        await query.edit_message_text(
            "🖼️ សូមជ្រើសរើសប្រភេទផ្ទះ៖",
            reply_markup=gallery_type_keyboard(),
        )
        return ConversationHandler.END

    if data.startswith("gallery:"):
        parts = data.split(":")
        if len(parts) == 2:
            property_type = parts[1]
            await query.edit_message_text(
                f"🖼️ {PROPERTIES[property_type]['title']}\n{DIV}\nជ្រើសរើសម៉ូឌែលដើម្បីមើលរូប៖",
                reply_markup=gallery_list_keyboard(property_type),
            )
            return ConversationHandler.END
        if len(parts) == 3:
            property_type, index_s = parts[1], parts[2]
            index = int(index_s)
            item = PROPERTIES[property_type]["items"][index]
            log_activity(user_id, query.from_user.full_name, "view_sample_image", item.get("name", ""))
            caption = (
                f"🖼️ *{item['name']}*\n{DIV}\n"
                f"💰 តម្លៃ: `{item['price']}`\n"
                f"📐 ទំហំ: `{item['size']}`\n"
                f"📏 ផ្ទៃសរុប: `{item['area']}`\n"
                f"🛏️ {item['bed']}"
            )
            try:
                await query.message.reply_photo(
                    photo=item.get("image_url"),
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=gallery_list_keyboard(property_type),
                )
                await query.edit_message_text("✅ រូបផ្ទះគំរូបានផ្ញើរួច។")
            except Exception as e:
                await query.edit_message_text(f"❌ មិនអាចផ្ញើរូបបាន: {e}")
            return ConversationHandler.END

    if data == "back:types":
        await query.edit_message_text("📌 ជ្រើសរើសប្រភេទផ្ទះ៖", reply_markup=property_type_keyboard())
        return ConversationHandler.END

    if data == "back:property_list":
        property_type = context.user_data.get("property_type", "borey")
        await query.edit_message_text(property_type_text(property_type), reply_markup=property_list_keyboard(property_type))
        return ConversationHandler.END

    if data == "back:payment":
        property_type = context.user_data.get("property_type")
        index = context.user_data.get("property_index", 0)
        log_activity(user_id, query.from_user.full_name, "view_property", item.get("name", ""))
        await query.edit_message_text(property_detail_text(property_type, index), parse_mode=ParseMode.MARKDOWN, reply_markup=payment_keyboard())
        image_url = item.get("image_url")
        if image_url:
            try:
                await query.message.reply_photo(
                    photo=image_url,
                    caption=f"🖼️ រូបគំរូ: {item['name']}",
                    reply_markup=payment_keyboard(),
                )
            except Exception as e:
                logger.warning("Cannot send property image: %s", e)
        return ConversationHandler.END

    if data.startswith("type:"):
        property_type = data.split(":", 1)[1]
        context.user_data["property_type"] = property_type
        context.user_data["property_type_title"] = PROPERTIES[property_type]["title"]
        await query.edit_message_text(property_type_text(property_type), reply_markup=property_list_keyboard(property_type))
        return ConversationHandler.END

    if data.startswith("property:"):
        _, property_type, index_s = data.split(":")
        index = int(index_s)
        item = PROPERTIES[property_type]["items"][index]
        context.user_data.update(
            {
                "property_type": property_type,
                "property_type_title": PROPERTIES[property_type]["title"],
                "property_index": index,
                "property_name": item["name"],
                "property_price": item["price"],
                "property_size": item["size"],
            }
        )
        await query.edit_message_text(property_detail_text(property_type, index), parse_mode=ParseMode.MARKDOWN, reply_markup=payment_keyboard())
        return ConversationHandler.END

    if data.startswith("payment:"):
        payment_key = data.split(":", 1)[1]
        context.user_data["payment_type"] = PAYMENTS[payment_key]
        await query.edit_message_text(summary_text(context.user_data), parse_mode=ParseMode.MARKDOWN, reply_markup=confirm_keyboard())
        return ConversationHandler.END

    if data == "form:start":
        await query.edit_message_text("👤 សូមបញ្ចូលឈ្មោះពេញរបស់អ្នក៖")
        return NAME

    return ConversationHandler.END


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = clean_text(update.message.text)
    if len(name) < 2:
        await update.message.reply_text("⚠️ សូមបញ្ចូលឈ្មោះឲ្យបានត្រឹមត្រូវ។")
        return NAME
    context.user_data["customer_name"] = name
    await update.message.reply_text("📞 សូមបញ្ចូលលេខទូរស័ព្ទរបស់អ្នក៖")
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    phone = clean_text(update.message.text)
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 8:
        await update.message.reply_text("⚠️ លេខទូរស័ព្ទមិនត្រឹមត្រូវ។ សូមបញ្ចូលម្ដងទៀត។")
        return PHONE
    context.user_data["phone"] = phone
    await update.message.reply_text("📍 សូមបញ្ចូលទីលំនៅបច្ចុប្បន្នរបស់អ្នក៖")
    return ADDRESS


async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    address = clean_text(update.message.text)
    if len(address) < 5:
        await update.message.reply_text("⚠️ សូមបញ្ចូលអាសយដ្ឋានឲ្យបានច្បាស់។")
        return ADDRESS
    context.user_data["address"] = address
    await update.message.reply_text("📅 សូមបញ្ជាក់ថ្ងៃដែលចង់មកមើលផ្ទះដល់ទីតាំង\nឧទាហរណ៍: 25/05/2026 ម៉ោង 9:00 ព្រឹក")
    return VISIT_DATE


async def get_visit_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    visit_date = clean_text(update.message.text)
    if len(visit_date) < 4:
        await update.message.reply_text("⚠️ សូមបញ្ចូលថ្ងៃ/ម៉ោងឲ្យបានច្បាស់។")
        return VISIT_DATE

    user = update.effective_user
    context.user_data["visit_date"] = visit_date
    context.user_data["telegram_id"] = user.id
    context.user_data["telegram_name"] = user.full_name
    context.user_data.setdefault("user_status", "old")

    update_user_contact(user.id, context.user_data.get("phone", ""), context.user_data.get("address", ""))
    lead_id = save_lead(context.user_data)
    log_activity(user.id, user.full_name, "submit_lead", f"Lead #{lead_id}: {context.user_data.get('property_name', '')}")

    await update.message.reply_text(final_text(context.user_data, lead_id), parse_mode=ParseMode.MARKDOWN, reply_markup=main_reply_keyboard())
    await notify_team_new_lead(context, lead_id)
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("❌ បានបោះបង់។ ចុច /start ដើម្បីចាប់ផ្តើមម្ដងទៀត។", reply_markup=main_reply_keyboard())
    return ConversationHandler.END


async def text_shortcut(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    text = clean_text(update.message.text)
    user_id = update.effective_user.id

    if text in {"🏠 ចាប់ផ្តើម", "🏘️ មើលគម្រោង", "🏠 User Menu"}:
        await start(update, context)
    elif text == "☎️ ទំនាក់ទំនង":
        await contact(update, context)
    elif text == "💬 ទាក់ទង Staff":
        await staff_contact_request(update, context)
    elif text == "🏗️ គុណភាពសំណង់":
        await faq_reply(update, context, "quality")
    elif text == "🛠️ ធានា/ជួសជុល":
        await faq_reply(update, context, "warranty")
    elif text == "🏡 កែលម្អផ្ទះ":
        await faq_reply(update, context, "modify")
    elif text == "📋 សេវាកម្ម":
        await faq_reply(update, context, "services")
    elif text == "🖼️ រូបផ្ទះគំរូ":
        await gallery_command(update, context)
    elif text in {"🕘 History", "🕘 ប្រវត្តិ"}:
        await history_command(update, context)
    elif text == "🎁 Promotion":
        await faq_reply(update, context, "promo")
    elif text == "🔐 Admin Login":
        return await admin_login_start(update, context)
    elif text == "📊 Admin Data":
        await stats_command(update, context)
    elif text == "📋 Leads":
        await leads_command(update, context)
    elif text == "👨‍💼 Staff Panel":
        await staff_command(update, context)
    elif text == "📄 Download PDF":
        await update.message.reply_text("📄 ប្រើ command: /pdf ID\nឧទាហរណ៍: /pdf 1")
    elif text == "👥 Staff":
        if is_admin(user_id):
            await update.message.reply_text("👥 Staff Management\n/setstaff TELEGRAM_ID\n/remove_role TELEGRAM_ID")
        else:
            await update.message.reply_text(require_admin_text())
    else:
        await update.message.reply_text("សូមចុច /start ដើម្បីមើលជម្រើសផ្ទះ។", reply_markup=main_reply_keyboard())

    return None


def validate_env() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("❌ សូមដាក់ TELEGRAM_BOT_TOKEN ក្នុង file .env")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Telegram error: %s", context.error)


def main() -> None:
    validate_env()
    init_database()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(callback_handler),
            MessageHandler(filters.Regex("^🔐 Admin Login$"), admin_login_start),
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            VISIT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_visit_date)],
            ADMIN_LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_admin)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", myid_command))
    app.add_handler(CommandHandler("help", quick_info_command))
    app.add_handler(CommandHandler("services", services_command))
    app.add_handler(CommandHandler("quality", quality_command))
    app.add_handler(CommandHandler("warranty", warranty_command))
    app.add_handler(CommandHandler("promo", promo_command))
    app.add_handler(CommandHandler("staff_contact", staff_contact_request))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("staff", staff_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("leads", leads_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("gallery", gallery_command))
    app.add_handler(CommandHandler("lead", lead_command))
    app.add_handler(CommandHandler("pdf", pdf_command))
    app.add_handler(CommandHandler("close", close_command))
    app.add_handler(CommandHandler("assign", assign_command))
    app.add_handler(CommandHandler("setstaff", setstaff_command))
    app.add_handler(CommandHandler("setadmin", setadmin_command))
    app.add_handler(CommandHandler("remove_role", remove_role_command))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_shortcut))
    app.add_error_handler(error_handler)

    print(f"""
╔══════════════════════════════════════════════╗
  {BOT_NAME} — RUNNING ✅
  Database : {DB_PATH}
  PDF Dir  : {PDF_DIR}
  Contact  : {ADMIN_PHONE}
  Admins   : {len(ADMIN_IDS)}
  Staff    : {len(STAFF_IDS)}
  PDF      : {'ON' if REPORTLAB_AVAILABLE else 'OFF - install reportlab'}
╚══════════════════════════════════════════════╝
""")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

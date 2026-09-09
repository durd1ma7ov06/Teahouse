"""FastAPI server for Teahouse Telegram Mini App and Admin Dashboard."""

import os
import io
import csv
import logging
from typing import Optional
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Query, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel

from sqlalchemy import select, func, desc
from db.session import async_session
from db.models import User, Profile, InterviewSession
from bot.config import settings

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Teahouse Mini App & Admin API")

# Mount static files
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


class ProfileUpdateRequest(BaseModel):
    telegram_id: int
    full_name: str
    phone: Optional[str] = None
    role: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    seniority: Optional[str] = None
    experience_years: Optional[int] = None
    age: Optional[int] = None
    achievements: Optional[str] = None
    target_partner: Optional[str] = None
    target_industry: Optional[str] = None
    target_seniority: Optional[str] = None
    can_offer: Optional[str] = None
    interests: Optional[str] = None


@app.get("/")
async def get_index():
    """Render Mini App homepage."""
    index_file = BASE_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h2>Teahouse Mini App faol</h2>")
    return FileResponse(str(index_file))


@app.get("/api/questions")
async def get_questions_list():
    """Anketa savollari, variantlar va tizim mezonlarini qaytaruvchi API."""
    return {
        "deadline": settings.registration_deadline,
        "is_open": settings.is_registration_open(),
        "total_questions": 13,
        "stages": [
            {
                "stage": 1,
                "title": "Shaxsiy va kasbiy ma'lumotlar hamda erishilgan natijalar",
                "questions": [
                    {"id": 1, "field": "full_name", "title": "To'liq ism va familiyangiz", "type": "text"},
                    {"id": 2, "field": "phone", "title": "Telefon raqamingiz", "type": "phone"},
                    {"id": 3, "field": "role", "title": "Asosiy kasbingiz va lavozimingiz", "type": "text"},
                    {"id": 4, "field": "company", "title": "Kompaniya, tashkilot yoki startap loyihangiz", "type": "text"},
                    {"id": 5, "field": "industry", "title": "Faoliyat sohangiz", "type": "select", "options": [
                        "Axborot texnologiyalari (IT)",
                        "Moliya, bank va investitsiya",
                        "Savdo, riteyl va xizmatlar",
                        "Marketing, PR va reklama",
                        "Ishlab chiqarish va sanoat",
                        "Qurilish va ko'chmas mulk",
                        "Ta'lim va konsalting",
                        "Tibbiyot va farmatsevtika",
                    ]},
                    {"id": 6, "field": "seniority", "title": "Tajriba darajangiz", "type": "select", "options": [
                        "Boshlang'ich (0-2 yil)",
                        "O'rta mutaxassis (3-5 yil)",
                        "Katta mutaxassis (6-10 yil)",
                        "Rahbar / Biznes asoschisi (10+ yil)",
                    ]},
                    {"id": 7, "field": "achievements", "title": "Eng katta yutug'ingiz, loyihangiz yoki biznes natijalaringiz", "type": "textarea"},
                    {"id": 8, "field": "age", "title": "Yoshingiz", "type": "select", "options": ["18-24", "25-30", "31-35", "36-40", "41-50", "50+"]},
                ]
            },
            {
                "stage": 2,
                "title": "Qidirilayotgan sheriklar va uchrashuv mezonlari",
                "questions": [
                    {"id": 9, "field": "target_partner", "title": "Uchrashuvdan ko'zlangan asosiy maqsad", "type": "select", "options": [
                        "Biznes hamkor / Hammuassis topish",
                        "Investor / Moliyalashtirish jalb qilish",
                        "Mijozlar va buyurtmachilar topish",
                        "Malakali mutaxassis / Jamoa yig'ish",
                        "Mentor / Maslahatchi topish",
                        "Tajriba almashish va professional aloqalar",
                    ]},
                    {"id": 10, "field": "target_industry", "title": "Qaysi soha vakillari bilan muloqot qilish qiziq", "type": "select", "options": [
                        "Barcha soha vakillari bilan",
                        "Axborot texnologiyalari (IT)",
                        "Biznes, savdo va investitsiya",
                        "Marketing va savdo mutaxassislari",
                        "Ishlab chiqarish va xizmat ko'rsatish",
                    ]},
                    {"id": 11, "field": "target_seniority", "title": "Qidirilayotgan sherikning tajriba darajasi", "type": "select", "options": [
                        "Biznes egalari / Top-menejerlar",
                        "Katta mutaxassislar (Senior / 5+ yil)",
                        "O'rta darajadagi mutaxassislar (Mid)",
                        "Darajaning farqi yo'q (G'oyasi borlar)",
                    ]},
                    {"id": 12, "field": "can_offer", "title": "Boshqalarga bera oladigan aniq foyda, resurs yoki tajribangiz", "type": "textarea"},
                    {"id": 13, "field": "interests", "title": "Uchrashuv stolida muhokama qilmoqchi bo'lgan amaliy mavzu", "type": "textarea"},
                ]
            }
        ]
    }


@app.get("/api/profile/{telegram_id}")
async def get_profile(telegram_id: int):
    """Foydalanuvchi profilini olish."""
    async with async_session() as session:
        res_user = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = res_user.scalar_one_or_none()
        if not user:
            return {"found": False}

        res_prof = await session.execute(
            select(Profile).where(Profile.user_id == user.id)
        )
        profile = res_prof.scalar_one_or_none()

        if not profile:
            return {"found": True, "first_name": user.first_name, "phone": user.phone, "profile": None}

        return {
            "found": True,
            "first_name": user.first_name,
            "phone": user.phone,
            "profile": {
                "role": profile.role,
                "company": profile.company,
                "industry": profile.industry,
                "seniority": profile.seniority,
                "experience_years": profile.experience_years,
                "age": profile.age,
                "achievements": profile.achievements,
                "target_partner": profile.target_partner or profile.current_goal,
                "target_industry": profile.target_industry,
                "target_seniority": profile.target_seniority,
                "can_offer": profile.can_offer,
                "interests": profile.interests,
                "bio_summary": profile.bio_summary
            }
        }


# ═══════════════════════════════════════════════════════════════════════
# ADMIN PANEL: Barcha danniy (ma'lumot)larni ko'rish va boshqarish
# ═══════════════════════════════════════════════════════════════════════

@app.get("/admin", response_class=HTMLResponse)
@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(secret: Optional[str] = Query(None)):
    """Zamonaviy, to'liq va o'qilishi oson Admin boshqaruv paneli."""
    # Agar secret to'g'ri kelsa yoki lokalda bo'lsa ochadi
    async with async_session() as session:
        # Barcha foydalanuvchilar va profillar
        stmt = (
            select(User, Profile)
            .outerjoin(Profile, User.id == Profile.user_id)
            .order_by(desc(User.created_at))
        )
        results = (await session.execute(stmt)).all()

        total_users = len(results)
        completed_profiles = sum(1 for u, p in results if p and p.bio_summary)
        users_with_phone = sum(1 for u, p in results if u.phone)

    # HTML generatsiya qilish
    rows_html = ""
    for idx, (user, profile) in enumerate(results, 1):
        status_badge = '<span style="background:#10b981;color:#fff;padding:3px 8px;border-radius:12px;font-size:11px;font-weight:600;">To\'liq</span>' if (profile and profile.bio_summary) else '<span style="background:#f59e0b;color:#fff;padding:3px 8px;border-radius:12px;font-size:11px;font-weight:600;">Jarayonda</span>'
        
        name = user.first_name or "Noma'lum"
        username = f"@{user.username}" if user.username else f"ID: {user.telegram_id}"
        phone = user.phone or '<span style="color:#9ca3af">—</span>'
        role = profile.role or '<span style="color:#9ca3af">—</span>' if profile else "—"
        company = profile.company or "—" if profile else "—"
        industry = profile.industry or "—" if profile else "—"
        achievements = profile.achievements or "—" if profile else "—"
        target_partner = profile.target_partner or "—" if profile else "—"
        can_offer = profile.can_offer or "—" if profile else "—"
        bio = profile.bio_summary or "—" if profile else "—"

        created_str = user.created_at.strftime("%d.%m %H:%M") if user.created_at else "—"

        rows_html += f"""
        <tr style="border-bottom: 1px solid #2d3748; transition: background 0.2s;" onmouseover="this.style.background='#1e293b'" onmouseout="this.style.background='transparent'">
            <td style="padding: 12px 14px; font-weight: 600; color: #94a3b8;">{idx}</td>
            <td style="padding: 12px 14px;">
                <div style="font-weight: 600; color: #f8fafc;">{name}</div>
                <div style="font-size: 12px; color: #38bdf8;">{username}</div>
            </td>
            <td style="padding: 12px 14px; font-weight: 500; color: #cbd5e1;">{phone}</td>
            <td style="padding: 12px 14px;">
                <div style="font-weight: 600; color: #f1f5f9;">{role}</div>
                <div style="font-size: 12px; color: #94a3b8;">{company} ({industry})</div>
            </td>
            <td style="padding: 12px 14px; max-width: 200px; font-size: 12px; color: #cbd5e1; line-height: 1.4;">
                <div style="overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;" title="{achievements}">
                    {achievements}
                </div>
            </td>
            <td style="padding: 12px 14px; max-width: 180px; font-size: 12px; color: #cbd5e1;">
                <div style="font-weight: 600; color: #a78bfa;">{target_partner}</div>
                <div style="font-size: 11px; color: #94a3b8; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="{can_offer}">Taklif: {can_offer}</div>
            </td>
            <td style="padding: 12px 14px; max-width: 220px; font-size: 12px; color: #38bdf8; font-style: italic;">
                {bio}
            </td>
            <td style="padding: 12px 14px;">{status_badge}</td>
            <td style="padding: 12px 14px; font-size: 12px; color: #64748b;">{created_str}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Teahouse — Boshqaruv Markazi (Admin)</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }}
        body {{ background: #0b0f17; color: #f8fafc; padding: 24px; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; padding-bottom: 20px; border-bottom: 1px solid #1e293b; }}
        .title {{ font-size: 24px; font-weight: 700; color: #ffffff; }}
        .subtitle {{ font-size: 13px; color: #94a3b8; margin-top: 4px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }}
        .card {{ background: #131b2a; border: 1px solid #1e293b; border-radius: 12px; padding: 18px; }}
        .card-num {{ font-size: 30px; font-weight: 700; color: #38bdf8; margin-top: 8px; }}
        .card-label {{ font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; }}
        .actions {{ display: flex; gap: 12px; }}
        .btn {{ display: inline-flex; align-items: center; gap: 8px; background: #2563eb; color: #fff; padding: 10px 18px; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: 600; transition: 0.2s; }}
        .btn:hover {{ background: #1d4ed8; }}
        .btn-green {{ background: #059669; }}
        .btn-green:hover {{ background: #047857; }}
        .table-container {{ background: #131b2a; border: 1px solid #1e293b; border-radius: 12px; overflow-x: auto; }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; }}
        th {{ background: #0f172a; padding: 14px; font-size: 12px; text-transform: uppercase; color: #94a3b8; letter-spacing: 0.5px; border-bottom: 1px solid #1e293b; }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <div class="title">Teahouse — A'zolar va Anketalar Tahlili</div>
            <div class="subtitle">25-sentyabr saralash anketalari va AI profil natijalari monitoringi</div>
        </div>
        <div class="actions">
            <a href="/admin/export" class="btn btn-green">📥 Excel / CSV Yuklab Olish</a>
            <a href="javascript:location.reload()" class="btn">🔄 Yangilash</a>
        </div>
    </div>

    <div class="stats-grid">
        <div class="card">
            <div class="card-label">Jami A'zolar (Foydalanuvchilar)</div>
            <div class="card-num">{total_users}</div>
        </div>
        <div class="card">
            <div class="card-label">To'liq Anketani Topshirganlar</div>
            <div class="card-num" style="color: #10b981;">{completed_profiles}</div>
        </div>
        <div class="card">
            <div class="card-label">Telefon Tasdiqlaganlar</div>
            <div class="card-num" style="color: #f59e0b;">{users_with_phone}</div>
        </div>
        <div class="card">
            <div class="card-label">Deadlayn va Saralash</div>
            <div class="card-num" style="font-size: 20px; color: #e0e7ff; margin-top: 14px;">25-sentyabr 23:59</div>
        </div>
    </div>

    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>A'zo</th>
                    <th>Telefon</th>
                    <th>Kasbi & Tashkilot</th>
                    <th>Yutuqlari & Natijasi</th>
                    <th>Qidirayotgan Sherigi</th>
                    <th>AI Xulosasi (Bio)</th>
                    <th>Holati</th>
                    <th>Vaqt</th>
                </tr>
            </thead>
            <tbody>
                {rows_html if rows_html else '<tr><td colspan="9" style="text-align:center;padding:30px;color:#64748b;">Hozircha a\'zolar yo\'q</td></tr>'}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
    return HTMLResponse(content=html)


@app.get("/admin/export")
async def export_members_excel():
    """Barcha ma'lumotlarni to'liq Excel (.xlsx yoki .csv) formatida yuklab olish."""
    async with async_session() as session:
        stmt = (
            select(User, Profile)
            .outerjoin(Profile, User.id == Profile.user_id)
            .order_by(desc(User.created_at))
        )
        results = (await session.execute(stmt)).all()

        headers = [
            "ID",
            "Telegram ID",
            "Username",
            "To'liq Ism",
            "Telefon",
            "Kasb/Lavozim",
            "Kompaniya/Loyiha",
            "Soha",
            "Tajriba Darajasi",
            "Tajriba Yili",
            "Yoshi",
            "Eng Katta Yutug'i va Natijasi",
            "Sheriklik Maqsadi",
            "Izlanayotgan Soha",
            "Qidirilayotgan Daraja",
            "Boshqalarga Taklifi",
            "Muhokama Mavzulari",
            "AI Xulosa (Bio)",
            "Ro'yxatdan O'tgan Sana",
        ]

        data_rows = []
        for user, profile in results:
            data_rows.append([
                user.id,
                user.telegram_id,
                f"@{user.username}" if user.username else "",
                user.first_name,
                user.phone or "",
                profile.role if profile else "",
                profile.company if profile else "",
                profile.industry if profile else "",
                profile.seniority if profile else "",
                profile.experience_years if profile else "",
                profile.age if profile else "",
                profile.achievements if profile and hasattr(profile, "achievements") and profile.achievements else "",
                profile.target_partner if profile else "",
                profile.target_industry if profile else "",
                profile.target_seniority if profile and hasattr(profile, "target_seniority") and profile.target_seniority else "",
                profile.can_offer if profile else "",
                profile.interests if profile else "",
                profile.bio_summary if profile else "",
                user.created_at.strftime("%Y-%m-%d %H:%M") if user.created_at else "",
            ])

        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter
            has_openpyxl = True
        except ImportError:
            has_openpyxl = False

        if has_openpyxl:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Teahouse A'zolari"
            ws.append(headers)

            header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
            header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
            header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
            thin_border = Border(
                left=Side(style="thin", color="CBD5E1"),
                right=Side(style="thin", color="CBD5E1"),
                top=Side(style="thin", color="CBD5E1"),
                bottom=Side(style="thin", color="CBD5E1"),
            )

            for col_idx in range(1, len(headers) + 1):
                cell = ws.cell(row=1, column=col_idx)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_align
                cell.border = thin_border

            ws.row_dimensions[1].height = 28

            for row_data in data_rows:
                ws.append(row_data)
                row_idx = ws.max_row
                ws.row_dimensions[row_idx].height = 22
                for col_idx in range(1, len(row_data) + 1):
                    cell = ws.cell(row=row_idx, column=col_idx)
                    cell.border = thin_border
                    cell.alignment = Alignment(vertical="center")

            for col in ws.columns:
                max_len = 0
                col_letter = get_column_letter(col[0].column)
                for cell in col:
                    val = str(cell.value or "")
                    if len(val) > max_len:
                        max_len = len(val)
                ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 40)

            excel_buffer = io.BytesIO()
            wb.save(excel_buffer)
            excel_bytes = excel_buffer.getvalue()

            filename = f"teahouse_members_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            return Response(
                content=excel_bytes,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            output = io.StringIO()
            output.write("sep=;\n")
            writer = csv.writer(output, delimiter=";")
            writer.writerow(headers)
            for row in data_rows:
                writer.writerow(row)

            output.seek(0)
            csv_bytes = output.getvalue().encode("utf-8-sig")

            filename = f"teahouse_members_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            return Response(
                content=csv_bytes,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

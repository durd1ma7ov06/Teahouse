# 🍵 Teahouse Bot

Toshkentdagi professionallarni haftalik qahvaxona uchrashuvlariga matching qiluvchi Telegram bot.

## Tez boshlash

### 1. Kerakli narsalar
- Python 3.12+
- Docker (PostgreSQL va Redis uchun)
- Telegram Bot Token ([BotFather](https://t.me/BotFather))
- OpenAI API Key ([platform.openai.com](https://platform.openai.com))

### 2. O'rnatish

```bash
# Repo'ni clone qiling
cd teahouse

# Virtual environment yarating
python -m venv venv
venv\Scripts\activate  # Windows

# Dependencies o'rnating
pip install -r requirements.txt

# Docker xizmatlarni ishga tushiring
docker-compose up -d

# .env faylini yarating
copy .env.example .env
# .env faylini tahrirlang va tokenlarni kiriting
```

### 3. Ishga tushirish

```bash
python -m bot.main
```

## Loyiha strukturasi

```
teahouse/
├── bot/              # Telegram bot (aiogram 3.x)
│   ├── handlers/     # Message/callback handlers
│   ├── keyboards/    # Inline keyboards
│   ├── services/     # LLM, STT, matching, payment, scheduler
│   ├── states/       # FSM states
│   └── main.py       # Entry point
├── db/               # Database (SQLAlchemy + PostgreSQL)
│   ├── models/       # 19 database models
│   └── session.py    # Async session factory
└── admin/            # Admin panel (FastAPI) [coming soon]
```

## Haftalik jadval

| Vaqt | Voqea |
|------|-------|
| Dush 20:00 | Offer wave 1 |
| Dush 21:00 | Wave 1 yopiladi |
| Sesh 10:00 | Offer wave 2 |
| Sesh 11:00 | Wave 2 yopiladi |
| Sesh 20:00 | Roster lock + 24h reveal |
| Chor 09:00 | Ertalabki eslatma |
| Chor 18:00 | 2 soat qoldi |
| Chor 20:00 | **UCHRASHUV** |
| Pay 09:00 | Feedback poll |

## Texnologiyalar

- **Bot:** aiogram 3.x
- **DB:** PostgreSQL + SQLAlchemy 2.0
- **Cache/FSM:** Redis
- **LLM:** OpenAI GPT-4o (intervyu, savol generatsiya)
- **STT:** OpenAI Whisper (ovozli xabar)
- **Scheduler:** APScheduler
- **Admin:** FastAPI + HTMX

## Narx
99,000 UZS — faqat xizmat uchun (qahva kirmaydi).

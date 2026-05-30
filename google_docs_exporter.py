"""
NewsForge → Google Docs exporter.

Создаёт структурированный документ по всем 6 блокам ТЗ:
  Шапка / Блок 1. Инфоповоды / Блок 2. Углы / Блок 3. Заголовки /
  Блок 4. Рекомендации / Блок 5. Риски / Блок 6. Срочность /
  + Обратная связь по прошлому выпуску

Setup (одноразово):
  1. Google Drive → создай папку «NewsForge Reports»
  2. ПКМ → Share → добавь email сервисного аккаунта как Editor
  3. Скопируй ID папки из URL (drive.google.com/drive/folders/FOLDER_ID)
  4. Settings → Google Docs → вставь ID папки → Сохранить

Auth:
  GOOGLE_CREDENTIALS_B64 — base64-encoded service account JSON (приоритет)
  GOOGLE_SERVICE_ACCOUNT_PATH — путь к JSON-файлу (legacy)
"""
import os, base64, json
from datetime import datetime
from typing import Optional

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
]

# ── Локализация ────────────────────────────────────────────────────────────────

TRIGGER_RU   = {"money": "Деньги", "crisis": "Кризис", "opportunity": "Возможность",
                "fear": "Страх", "trust": "Доверие"}
CATEGORY_RU  = {"economy": "Экономика", "politics": "Политика", "social_media": "Соцсети",
                "celebrity": "Селеба", "scandal": "Скандал", "banks_taxes": "Банки/Налоги",
                "fears": "Страхи"}
SOURCE_RU    = {"top_media": "Топ СМИ", "local_tabloid": "Таблоид", "google_news": "Google News",
                "twitter_trend": "Twitter", "tiktok": "TikTok", "telegram": "Telegram", "forum": "Форум"}
CREATIVE_RU  = {"news": "Новостной", "emotional": "Эмоциональный",
                "investigation": "Разоблачение", "personal_story": "Личная история"}
RISK_RU      = {"high": "Высокий", "medium": "Средний", "low": "Низкий"}
FORMAT_RU    = {"question": "Вопрос", "shock": "Шок", "number": "Цифра",
                "quote": "Цитата", "intrigue": "Интрига"}
URGENCY_LABEL = {"urgent_48h": "СРОЧНО (48ч)", "week": "На неделе", "eternal": "Вечная тема"}


# ── UTF-16 helper (Google Docs API считает в code units) ──────────────────────

def _u16(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


# ── DocBuilder ────────────────────────────────────────────────────────────────

class DocBuilder:
    """Накапливает текстовые сегменты, строит пакет запросов Docs API."""

    def __init__(self):
        self._segs: list[dict] = []   # {"text", "style", "bold", "italic"}

    def _add(self, text: str, style: str = "NORMAL_TEXT",
             bold: bool = False, italic: bool = False):
        if text:
            self._segs.append({"text": text + "\n", "style": style,
                                "bold": bold, "italic": italic})

    # helpers
    def h1(self, t):      self._add(t, "HEADING_1")
    def h2(self, t):      self._add(t, "HEADING_2")
    def h3(self, t):      self._add(t, "HEADING_3")
    def bold(self, t):    self._add(t, bold=True)
    def italic(self, t):  self._add(t, italic=True)
    def text(self, t):    self._add(t)
    def sep(self):        self._add("─" * 55)
    def br(self):         self._add("")

    def build_requests(self) -> tuple[str, list[dict]]:
        """Возвращает (full_text, list_of_api_requests)."""
        full_text = "".join(s["text"] for s in self._segs)

        reqs: list[dict] = [{"insertText": {"location": {"index": 1}, "text": full_text}}]

        pos = 1
        for seg in self._segs:
            ln = _u16(seg["text"])
            end = pos + ln

            if seg["style"] != "NORMAL_TEXT":
                reqs.append({
                    "updateParagraphStyle": {
                        "range": {"startIndex": pos, "endIndex": end},
                        "paragraphStyle": {"namedStyleType": seg["style"]},
                        "fields": "namedStyleType",
                    }
                })

            content_end = end - 1   # exclude trailing \n from char styling
            if content_end > pos:
                style_fields = []
                ts: dict = {}
                if seg["bold"]:
                    ts["bold"] = True; style_fields.append("bold")
                if seg["italic"]:
                    ts["italic"] = True; style_fields.append("italic")
                if ts:
                    reqs.append({
                        "updateTextStyle": {
                            "range": {"startIndex": pos, "endIndex": content_end},
                            "textStyle": ts,
                            "fields": ",".join(style_fields),
                        }
                    })

            pos = end

        return full_text, reqs


# ── Credentials ───────────────────────────────────────────────────────────────

def _load_credentials():
    """
    Порядок приоритета:
      1. OAuth2 Refresh Token (личный аккаунт Google) — рекомендуется для личного Drive
      2. Service Account (base64 из env)
      3. Service Account (путь к JSON файлу)

    Внимание: сервисный аккаунт создаёт файлы в своём Drive (квота = 0).
    Используй OAuth Refresh Token чтобы файлы создавались от имени пользователя.
    Запусти setup_google_oauth.py один раз для получения токена.
    """
    try:
        from google.oauth2 import service_account
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
    except ImportError:
        print("[gdocs] Установи: pip install google-api-python-client google-auth")
        return None

    # ── Вариант 1: OAuth2 refresh token (личный аккаунт) ──────────────────────
    refresh_token  = os.getenv("GOOGLE_OAUTH_REFRESH_TOKEN", "").strip()
    client_id      = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip()
    client_secret  = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
    if refresh_token and client_id and client_secret:
        try:
            creds = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
                scopes=SCOPES,
            )
            creds.refresh(Request())   # получаем актуальный access token
            print("[gdocs] Авторизация через OAuth2 (личный аккаунт)")
            return creds
        except Exception as e:
            print(f"[gdocs] Ошибка OAuth2 credentials: {e}")

    # ── Вариант 2: Service Account из env (base64) ─────────────────────────────
    b64 = os.getenv("GOOGLE_CREDENTIALS_B64", "").strip()
    if b64:
        try:
            info = json.loads(base64.b64decode(b64).decode("utf-8"))
            creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
            print("[gdocs] Авторизация через Service Account (base64)")
            return creds
        except Exception as e:
            print(f"[gdocs] Ошибка credentials из env: {e}")

    # ── Вариант 3: Service Account из файла ────────────────────────────────────
    path = os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH", "").strip()
    if path and os.path.exists(path):
        try:
            creds = service_account.Credentials.from_service_account_file(path, scopes=SCOPES)
            print("[gdocs] Авторизация через Service Account (файл)")
            return creds
        except Exception as e:
            print(f"[gdocs] Ошибка credentials из файла: {e}")

    print("[gdocs] Credentials не настроены")
    return None


def _get_sa_email() -> str:
    try:
        b64 = os.getenv("GOOGLE_CREDENTIALS_B64", "")
        if b64:
            return json.loads(base64.b64decode(b64).decode("utf-8")).get("client_email", "")
    except Exception:
        pass
    return "сервисный аккаунт"


def get_service_account_email() -> str:
    return _get_sa_email()


def is_oauth_configured() -> bool:
    """True если настроены OAuth2-токены (личный аккаунт)."""
    return bool(
        os.getenv("GOOGLE_OAUTH_REFRESH_TOKEN", "").strip() and
        os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip() and
        os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
    )


# ── Главная функция ───────────────────────────────────────────────────────────

def create_report_doc(report_data: dict) -> Optional[str]:
    creds = _load_credentials()
    if not creds:
        return None

    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "").strip()
    if not folder_id:
        print("[gdocs] GOOGLE_DRIVE_FOLDER_ID не задан")
        return None

    try:
        from googleapiclient.discovery import build
        drive_svc = build("drive", "v3", credentials=creds)
        docs_svc  = build("docs",  "v1", credentials=creds)

        geo        = report_data.get("geo", "GEO")
        report_id  = report_data.get("report_id", "")
        date_str   = (report_data.get("created_at") or "")[:10]
        title_val  = report_data.get("title", "").strip()
        doc_title  = title_val or f"NewsForge — {geo} #{report_id} — {date_str}"

        # Создаём документ в папке пользователя
        doc = drive_svc.files().create(
            body={"name": doc_title,
                  "mimeType": "application/vnd.google-apps.document",
                  "parents": [folder_id]},
            fields="id,webViewLink",
        ).execute()
        doc_id   = doc["id"]
        doc_link = doc.get("webViewLink",
                           f"https://docs.google.com/document/d/{doc_id}/edit")

        # Строим контент
        _, reqs = _build_all_blocks(report_data)

        docs_svc.documents().batchUpdate(
            documentId=doc_id, body={"requests": reqs}
        ).execute()

        # Открываем чтение по ссылке (игнорируем ошибку если запрещено политикой)
        try:
            drive_svc.permissions().create(
                fileId=doc_id,
                body={"type": "anyone", "role": "reader"},
            ).execute()
        except Exception:
            pass

        print(f"[gdocs] Создан: {doc_link}")
        return doc_link

    except Exception as exc:
        err = str(exc)
        if "storageQuotaExceeded" in err:
            print(
                "[gdocs] Квота Drive сервисного аккаунта исчерпана (0 байт).\n"
                "  Решение: настрой OAuth2 токен личного Google-аккаунта.\n"
                "  Запусти: python setup_google_oauth.py"
            )
        elif "notFound" in err or "404" in err:
            print(f"[gdocs] Папка не найдена. Проверь GOOGLE_DRIVE_FOLDER_ID в .env")
        elif "403" in err:
            print(f"[gdocs] Нет доступа. Добавь {_get_sa_email()} как Editor в папку Drive")
        else:
            print(f"[gdocs] Ошибка: {exc}")
        return None


# ── Построение документа (6 блоков ТЗ) ───────────────────────────────────────

def _fmt_date(iso: str) -> str:
    if not iso:
        return ""
    try:
        d = datetime.fromisoformat(iso[:19])
        months = ["янв","фев","мар","апр","май","июн","июл","авг","сен","окт","ноя","дек"]
        return f"{d.day} {months[d.month-1]} {d.year}"
    except Exception:
        return iso[:10]


def _build_all_blocks(r: dict) -> tuple[str, list[dict]]:
    d   = DocBuilder()
    geo = r.get("geo", "")

    news  = r.get("news", [])
    angles = r.get("angles", [])
    recs  = r.get("recommendations", [])
    risks = r.get("risks", [])
    urg   = r.get("urgency", {})
    prev_liked = r.get("prev_liked", [])
    stats = r.get("stats", {})

    created_str = _fmt_date(r.get("created_at", ""))

    # ── Заголовок документа ───────────────────────────────────────────────────
    title_val = r.get("title", "").strip()
    d.h1(title_val or f"NewsForge — {geo} #{r.get('report_id','')} — {created_str}")
    d.br()

    # ── Шапка ─────────────────────────────────────────────────────────────────
    d.h2("Шапка")
    d.text(f"Страна / GEO:        {geo}")
    d.text(f"Дата генерации:      {created_str}")
    d.text(f"Период покрытия:     последние {r.get('coverage_days', 7)} дней")
    if r.get("team_lead"):
        d.text(f"Тимлид:              {r['team_lead']}")
    if r.get("prev_report_id"):
        d.text(f"Предыдущий выпуск:   #{r['prev_report_id']}")
    d.text(f"Инфоповодов: {stats.get('total_news',0)}  |  "
           f"Углов: {stats.get('total_angles',0)}  |  "
           f"Заголовков: {stats.get('total_headlines',0)}")
    d.sep()
    d.br()

    # ── Блок 1. Инфоповоды ────────────────────────────────────────────────────
    d.h2(f"Блок 1. Инфоповоды ({len(news)})")
    for i, n in enumerate(news, 1):
        urg_label = URGENCY_LABEL.get(n.get("urgency",""), "")
        prefix    = f"[{urg_label}] " if urg_label else ""
        d.bold(f"{i}. {prefix}{n.get('title','')}")

        src_parts = [n.get("source",""),
                     SOURCE_RU.get(n.get("source_type",""), n.get("source_type",""))]
        pub = _fmt_date(n.get("published_at",""))
        src_line = "   Источник: " + " · ".join(p for p in src_parts if p)
        if pub:
            src_line += f"  |  Дата: {pub}"
        d.text(src_line)

        if n.get("category"):
            d.text(f"   Категория: {CATEGORY_RU.get(n['category'], n['category'])}")
        if n.get("emotional_trigger"):
            d.text(f"   Триггер: {TRIGGER_RU.get(n['emotional_trigger'], n['emotional_trigger'])}")
        if n.get("description"):
            d.text(f"   {n['description'][:300]}")
        if n.get("original_url"):
            d.text(f"   Ссылка: {n['original_url']}")
        d.br()
    d.sep()
    d.br()

    # ── Блок 2. Углы и идеи ───────────────────────────────────────────────────
    d.h2(f"Блок 2. Маркетинговые углы и идеи ({len(angles)})")
    for i, a in enumerate(angles, 1):
        d.bold(f"{i}. [{a.get('priority','?')}] {a.get('angle_title','')}")
        if a.get("news_title"):
            d.text(f"   К инфоповоду: {a['news_title']}")
        if a.get("creative_type"):
            d.text(f"   Тип креатива: {CREATIVE_RU.get(a['creative_type'], a['creative_type'])}")
        if a.get("target_pain"):
            d.text(f"   Боль аудитории: {a['target_pain']}")
        if a.get("offer_connection"):
            d.text(f"   Связь с оффером: {a['offer_connection']}")
        d.br()
    d.sep()
    d.br()

    # ── Блок 3. Заголовки ─────────────────────────────────────────────────────
    total_hl = sum(len(a.get("headlines", [])) for a in angles)
    d.h2(f"Блок 3. Заголовки ({total_hl})")
    for i, a in enumerate(angles, 1):
        headlines = a.get("headlines", [])
        if not headlines:
            continue
        d.bold(f"[{a.get('priority','?')}] {a.get('angle_title','')}")
        for h in headlines:
            fmt_label = FORMAT_RU.get(h.get("format",""), h.get("format",""))
            char_cnt  = h.get("character_count", len(h.get("text","")))
            d.text(f"   • {h.get('text','')}  ({char_cnt} зн. · {fmt_label})")
        d.br()
    d.sep()
    d.br()

    # ── Блок 4. Рекомендации к тесту ─────────────────────────────────────────
    if recs:
        d.h2("Блок 4. Рекомендации к тесту (Топ-5)")
        for rec in recs[:5]:
            rank = rec.get("rank", "?")
            d.bold(f"{rank}. {rec.get('angle_title','')}")
            if rec.get("news_title"):
                d.text(f"   Инфоповод: {rec['news_title']}")
            if rec.get("reasoning"):
                d.text(f"   Обоснование: {rec['reasoning']}")
            scores = []
            if rec.get("freshness"):        scores.append(f"Свежесть: {rec['freshness']}")
            if rec.get("trigger_strength"): scores.append(f"Триггер: {rec['trigger_strength']}")
            if rec.get("offer_fit"):        scores.append(f"Оффер: {rec['offer_fit']}")
            if scores:
                d.text("   " + "  |  ".join(scores))
            d.br()
        d.sep()
        d.br()

    # ── Блок 5. Риски ─────────────────────────────────────────────────────────
    if risks:
        d.h2(f"Блок 5. Оценка рисков ({len(risks)})")
        for risk in risks:
            if risk.get("news_title"):
                d.bold(f"Инфоповод: {risk['news_title']}")
            legal = risk.get("legal_risks", [])
            if legal:
                d.text(f"   Юридические риски: {'; '.join(legal)}")
            d.text(f"   Риск бана платформой:   {RISK_RU.get(risk.get('platform_ban_risk',''), risk.get('platform_ban_risk',''))}")
            d.text(f"   Риск негатива:           {RISK_RU.get(risk.get('audience_negativity_risk',''), risk.get('audience_negativity_risk',''))}")
            d.text(f"   Репутационный риск:      {RISK_RU.get(risk.get('reputation_risk',''), risk.get('reputation_risk',''))}")
            if risk.get("expiry_date"):
                d.text(f"   Срок актуальности:       {risk['expiry_date']}")
            d.br()
        d.sep()
        d.br()

    # ── Блок 6. Срочность ─────────────────────────────────────────────────────
    d.h2("Блок 6. Срочность")
    urgent  = urg.get("urgent", [])
    week    = urg.get("week", [])
    eternal = urg.get("eternal", [])
    d.bold(f"СРОЧНО — тестить в течение 48 часов ({len(urgent)})")
    for t in urgent:
        d.text(f"   • {t}")
    d.br()
    d.bold(f"НА НЕДЕЛЕ ({len(week)})")
    for t in week:
        d.text(f"   • {t}")
    d.br()
    d.bold(f"ВЕЧНЫЕ ТЕМЫ ({len(eternal)})")
    for t in eternal:
        d.text(f"   • {t}")
    d.sep()
    d.br()

    # ── Обратная связь по прошлому выпуску ────────────────────────────────────
    if prev_liked:
        d.h2("Что зашло в прошлый раз")
        d.italic(f"Углы из предыдущего выпуска #{r.get('prev_report_id','')} с положительной оценкой:")
        for a in prev_liked:
            d.text(f"   [{a.get('priority','?')}] {a.get('angle_title','')}")
        d.br()

    return d.build_requests()

"""
NewsForge → Google Docs exporter — v2 (styled).

Создаёт структурированный, визуально оформленный документ:
  Обложка · Блок 1. Инфоповоды · Блок 2+3. Углы и заголовки ·
  Блок 4. Рекомендации · Блок 5. Риски · Блок 6. Срочность ·
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
import os, re, base64, json
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
                "twitter_trend": "Twitter", "tiktok": "TikTok", "telegram": "Telegram",
                "forum": "Форум"}
CREATIVE_RU  = {"news": "Новостной", "emotional": "Эмоциональный",
                "investigation": "Разоблачение", "personal_story": "Личная история"}
RISK_RU      = {"high": "Высокий", "medium": "Средний", "low": "Низкий"}
FORMAT_RU    = {"question": "Вопрос", "shock": "Шок", "number": "Число",
                "quote": "Цитата", "intrigue": "Интрига"}
URGENCY_LABEL = {"urgent_48h": "СРОЧНО (48ч)", "week": "На неделе", "eternal": "Вечная тема"}

# ── Цветовая палитра ──────────────────────────────────────────────────────────

def _rgb(r, g, b):
    return {"red": r / 255, "green": g / 255, "blue": b / 255}

C_NAVY   = _rgb(15,  52,  96)   # заголовки разделов
C_TEAL   = _rgb(8,  102, 107)   # мета-информация, теги
C_GREEN  = _rgb(21, 128,  61)   # приоритет A
C_AMBER  = _rgb(180, 130,   0)  # приоритет B
C_GRAY   = _rgb(100, 116, 139)  # приоритет C, второстепенный текст
C_RED    = _rgb(185,  28,  28)  # СРОЧНО, высокий риск
C_ORANGE = _rgb(194,  65,  12)  # на неделе, средний риск
C_BLUE   = _rgb(30,   64, 175)  # ссылки
C_GOLD   = _rgb(161,  98,   7)  # рекомендации
C_TEXT   = _rgb(30,   41,  59)  # основной текст
C_LIGHT  = _rgb(71,   85, 105)  # вторичный текст


# ── UTF-16 helper (Google Docs API считает в code units) ──────────────────────

def _u16(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


# ── Утилиты текста ────────────────────────────────────────────────────────────

def _clean(text: str) -> str:
    """Убирает HTML-сущности и лишние пробелы из RSS-текста."""
    if not text:
        return ""
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"&#\d+;", "", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _short_url(url: str, max_len: int = 72) -> str:
    """Обрезает очень длинные URL до читаемой длины."""
    if not url:
        return ""
    if len(url) <= max_len:
        return url
    # Для Google News redirect — оставляем только домен
    if "news.google.com" in url:
        return "https://news.google.com/…"
    return url[:max_len] + "…"


# ── DocBuilder ────────────────────────────────────────────────────────────────

class DocBuilder:
    """Накапливает текстовые сегменты, строит пакет запросов Docs API."""

    def __init__(self):
        self._segs: list[dict] = []

    def _add(self, text: str, *,
             named_style: str = "NORMAL_TEXT",
             bold: bool = False,
             italic: bool = False,
             size_pt: float = None,
             color: dict = None,
             align: str = None,        # "CENTER" | "LEFT" | "JUSTIFIED"
             space_above: float = None,
             space_below: float = None,
             indent: float = None):    # indentStart в PT
        if text is not None:
            self._segs.append(dict(
                text=text + "\n",
                named_style=named_style,
                bold=bold, italic=italic,
                size_pt=size_pt, color=color,
                align=align,
                space_above=space_above,
                space_below=space_below,
                indent=indent,
            ))

    # ── Структурные элементы ──────────────────────────────────────────────────

    def br(self):
        self._add("", space_above=0, space_below=0)

    def divider_thick(self):
        self._add("━" * 58, color=C_NAVY, align="CENTER",
                  size_pt=8, space_above=10, space_below=10)

    def divider(self):
        self._add("─" * 58, color=C_GRAY, align="CENTER",
                  size_pt=8, space_above=6, space_below=6)

    def section_header(self, label: str, count=None):
        tail = f"  ({count})" if count is not None else ""
        self._add(f"▌  {label.upper()}{tail}",
                  bold=True, size_pt=13, color=C_NAVY,
                  space_above=20, space_below=6)

    # ── Обложка ───────────────────────────────────────────────────────────────

    def cover_title(self, t: str):
        self._add(t, bold=True, size_pt=24, color=C_NAVY,
                  align="CENTER", space_above=14, space_below=4)

    def cover_sub(self, t: str):
        self._add(t, size_pt=11, color=C_LIGHT,
                  align="CENTER", space_above=2, space_below=2)

    def cover_stats(self, t: str):
        self._add(t, bold=True, size_pt=12, color=C_TEAL,
                  align="CENTER", space_above=8, space_below=8)

    # ── Новости ───────────────────────────────────────────────────────────────

    def news_title(self, number: int, text: str, urgency: str):
        color = {"urgent_48h": C_RED, "week": C_ORANGE, "eternal": C_GRAY}.get(urgency, C_GRAY)
        icon  = {"urgent_48h": "🔥", "week": "⏳", "eternal": "♾️"}.get(urgency, "•")
        label = URGENCY_LABEL.get(urgency, "")
        badge = f"[{label}]  " if label else ""
        self._add(f"{icon}  {number}.  {badge}{text}",
                  bold=True, size_pt=11, color=color,
                  space_above=10, space_below=2)

    def news_meta(self, t: str):
        self._add(t, size_pt=9.5, color=C_GRAY, indent=14, space_above=1, space_below=1)

    def news_tags(self, t: str):
        self._add(t, size_pt=9.5, color=C_TEAL, indent=14, space_above=1, space_below=1)

    def news_desc(self, t: str):
        self._add(t, size_pt=10, italic=True, color=C_LIGHT, indent=14,
                  space_above=1, space_below=1)

    def news_link(self, url: str):
        self._add(f"   🔗  {_short_url(url)}",
                  size_pt=9, color=C_BLUE, italic=True, indent=14,
                  space_above=1, space_below=1)

    # ── Углы ──────────────────────────────────────────────────────────────────

    def angle_header(self, priority: str, title: str):
        color = {"A": C_GREEN, "B": C_AMBER, "C": C_GRAY}.get(priority, C_GRAY)
        icon  = {"A": "🟢", "B": "🟡", "C": "⚪"}.get(priority, "•")
        self._add(f"{icon}  [{priority}]  {title}",
                  bold=True, size_pt=12, color=color,
                  space_above=14, space_below=3)

    def angle_detail(self, emoji: str, label: str, value: str):
        self._add(f"   {emoji}  {label}:  {value}",
                  size_pt=10, color=C_LIGHT, indent=14, space_above=1, space_below=1)

    def headlines_label(self):
        self._add("   📌  Заголовки:",
                  size_pt=9.5, bold=True, color=C_GRAY, indent=14,
                  space_above=5, space_below=1)

    def headline_row(self, text: str, chars: int, fmt: str):
        ann = f"{chars} зн. · {fmt}"
        pad = max(1, 64 - len(text) - len(ann))
        self._add(f"        ▸  {text}{' ' * pad}{ann}",
                  size_pt=10.5, color=C_TEXT, indent=14, space_above=1, space_below=1)

    # ── Рекомендации ──────────────────────────────────────────────────────────

    def rec_header(self, rank, title: str):
        self._add(f"★  {rank}.  {title}",
                  bold=True, size_pt=12, color=C_GOLD,
                  space_above=12, space_below=3)

    def rec_detail(self, emoji: str, label: str, value: str):
        self._add(f"   {emoji}  {label}:  {value}",
                  size_pt=10, color=C_LIGHT, indent=14, space_above=1, space_below=2)

    def rec_scores(self, freshness: str, trigger: str, offer: str):
        parts = [p for p in [
            f"Свежесть: {freshness}" if freshness else None,
            f"Триггер: {trigger}"   if trigger   else None,
            f"Оффер: {offer}"       if offer      else None,
        ] if p]
        if parts:
            self._add("   " + "   ·   ".join(parts),
                      size_pt=10, color=C_TEAL, indent=14, space_above=1, space_below=1)

    # ── Риски ─────────────────────────────────────────────────────────────────

    def risk_header(self, title: str):
        self._add(f"⚠️   {title}",
                  bold=True, size_pt=11, color=C_ORANGE,
                  space_above=12, space_below=3)

    def risk_legal(self, items: list):
        self._add(f"   ⚖️   Юридические риски:  {';  '.join(items)}",
                  size_pt=10, color=_rgb(127, 29, 29), indent=14,
                  space_above=2, space_below=1)

    def risk_row(self, ban: str, neg: str, rep: str):
        _icon  = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        _label = {"high": "Высокий", "medium": "Средний", "low": "Низкий"}
        parts = [
            f"Бан: {_icon.get(ban,'')} {_label.get(ban, ban)}",
            f"Негатив: {_icon.get(neg,'')} {_label.get(neg, neg)}",
            f"Репутация: {_icon.get(rep,'')} {_label.get(rep, rep)}",
        ]
        self._add("   " + "   |   ".join(parts),
                  size_pt=10, color=C_GRAY, indent=14, space_above=2, space_below=1)

    def risk_expiry(self, date: str):
        self._add(f"   📅  Актуально до: {date}",
                  size_pt=10, italic=True, color=C_GRAY, indent=14,
                  space_above=1, space_below=1)

    # ── Срочность ─────────────────────────────────────────────────────────────

    def urgency_group(self, icon: str, label: str, count: int, color: dict):
        self._add(f"{icon}  {label}  ({count})",
                  bold=True, size_pt=12, color=color,
                  space_above=10, space_below=4)

    def urgency_bullet(self, text: str):
        self._add(f"   ▸  {text}",
                  size_pt=10.5, color=C_TEXT, indent=14,
                  space_above=1, space_below=1)

    # ── Прошлый выпуск ────────────────────────────────────────────────────────

    def prev_item(self, priority: str, title: str):
        color = {"A": C_GREEN, "B": C_AMBER, "C": C_GRAY}.get(priority, C_GRAY)
        icon  = {"A": "🟢", "B": "🟡", "C": "⚪"}.get(priority, "•")
        self._add(f"   {icon}  [{priority}]  {title}",
                  size_pt=10.5, color=color, indent=14,
                  space_above=2, space_below=2)

    # ── Сборка запросов ───────────────────────────────────────────────────────

    def build_requests(self) -> tuple[str, list[dict]]:
        """Возвращает (full_text, list_of_api_requests)."""
        full_text = "".join(s["text"] for s in self._segs)
        reqs: list[dict] = [
            {"insertText": {"location": {"index": 1}, "text": full_text}}
        ]

        pos = 1
        for seg in self._segs:
            ln   = _u16(seg["text"])
            end  = pos + ln
            cend = end - 1  # исключаем завершающий \n из text style

            # ── Paragraph style ───────────────────────────────────────────────
            ps: dict = {}
            pf: list = []

            ns = seg.get("named_style", "NORMAL_TEXT")
            if ns and ns != "NORMAL_TEXT":
                ps["namedStyleType"] = ns
                pf.append("namedStyleType")

            if seg.get("align"):
                ps["alignment"] = seg["align"]
                pf.append("alignment")

            if seg.get("space_above") is not None:
                ps["spaceAbove"] = {"magnitude": seg["space_above"], "unit": "PT"}
                pf.append("spaceAbove")

            if seg.get("space_below") is not None:
                ps["spaceBelow"] = {"magnitude": seg["space_below"], "unit": "PT"}
                pf.append("spaceBelow")

            if seg.get("indent") is not None:
                ps["indentStart"] = {"magnitude": seg["indent"], "unit": "PT"}
                pf.append("indentStart")

            if ps:
                reqs.append({
                    "updateParagraphStyle": {
                        "range": {"startIndex": pos, "endIndex": end},
                        "paragraphStyle": ps,
                        "fields": ",".join(pf),
                    }
                })

            # ── Text style ────────────────────────────────────────────────────
            if cend > pos:
                ts: dict = {}
                tf: list = []

                if seg.get("bold"):
                    ts["bold"] = True
                    tf.append("bold")

                if seg.get("italic"):
                    ts["italic"] = True
                    tf.append("italic")

                if seg.get("size_pt") is not None:
                    ts["fontSize"] = {"magnitude": seg["size_pt"], "unit": "PT"}
                    tf.append("fontSize")

                if seg.get("color"):
                    ts["foregroundColor"] = {"color": {"rgbColor": seg["color"]}}
                    tf.append("foregroundColor")

                if ts:
                    reqs.append({
                        "updateTextStyle": {
                            "range": {"startIndex": pos, "endIndex": cend},
                            "textStyle": ts,
                            "fields": ",".join(tf),
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
            creds.refresh(Request())
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

        doc = drive_svc.files().create(
            body={"name": doc_title,
                  "mimeType": "application/vnd.google-apps.document",
                  "parents": [folder_id]},
            fields="id,webViewLink",
        ).execute()
        doc_id   = doc["id"]
        doc_link = doc.get("webViewLink",
                           f"https://docs.google.com/document/d/{doc_id}/edit")

        _, reqs = _build_all_blocks(report_data)

        docs_svc.documents().batchUpdate(
            documentId=doc_id, body={"requests": reqs}
        ).execute()

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


# ── Построение документа ──────────────────────────────────────────────────────

def _fmt_date(iso: str) -> str:
    if not iso:
        return ""
    try:
        d = datetime.fromisoformat(iso[:19])
        months = ["янв","фев","мар","апр","май","июн",
                  "июл","авг","сен","окт","ноя","дек"]
        return f"{d.day} {months[d.month-1]} {d.year}"
    except Exception:
        return iso[:10]


def _build_all_blocks(r: dict) -> tuple[str, list[dict]]:
    d = DocBuilder()

    geo         = r.get("geo", "GEO")
    news        = r.get("news", [])
    angles      = r.get("angles", [])
    recs        = r.get("recommendations", [])
    risks       = r.get("risks", [])
    urg         = r.get("urgency", {})
    prev_liked  = r.get("prev_liked", [])
    stats       = r.get("stats", {})
    created_str = _fmt_date(r.get("created_at", ""))
    report_id   = r.get("report_id", "")
    title_val   = r.get("title", "").strip()
    team_lead   = r.get("team_lead", "")
    prev_id     = r.get("prev_report_id", "")
    vertical    = r.get("vertical", "")
    keywords    = r.get("keywords", "")
    cover_days  = r.get("coverage_days", 7)

    n_news = stats.get("total_news",      len(news))
    n_ang  = stats.get("total_angles",    len(angles))
    n_hl   = stats.get("total_headlines",
                        sum(len(a.get("headlines", [])) for a in angles))

    # ── ОБЛОЖКА ───────────────────────────────────────────────────────────────
    d.divider_thick()
    d.br()

    main_title = title_val or f"NewsForge — {geo} · Выпуск #{report_id}"
    d.cover_title(main_title)

    sub_parts = [p for p in [geo, f"Выпуск #{report_id}", created_str] if p]
    d.cover_sub("  ·  ".join(sub_parts))

    meta_parts = [p for p in [
        f"Период: {cover_days} дн.",
        f"Тимлид: {team_lead}"        if team_lead else None,
        f"Предыдущий выпуск: #{prev_id}" if prev_id  else None,
        f"Вертикаль: {vertical}"      if vertical  else None,
        f"Ключевые слова: {keywords}" if keywords  else None,
    ] if p]
    if meta_parts:
        d.cover_sub("  ·  ".join(meta_parts))

    d.br()
    d.cover_stats(
        f"📰  {n_news} инфоповодов     💡  {n_ang} углов     📝  {n_hl} заголовков"
    )
    d.br()
    d.divider_thick()
    d.br()

    # ── БЛОК 1. ИНФОПОВОДЫ ────────────────────────────────────────────────────
    d.section_header("Блок 1 — Инфоповоды", count=len(news))

    for i, n in enumerate(news, 1):
        urgency = n.get("urgency", "eternal")
        d.news_title(i, _clean(n.get("title", "")), urgency)

        src_parts = [n.get("source", ""),
                     SOURCE_RU.get(n.get("source_type", ""), n.get("source_type", ""))]
        pub = _fmt_date(n.get("published_at", ""))
        src_line = "   Источник: " + "  ·  ".join(p for p in src_parts if p)
        if pub:
            src_line += f"   ·   {pub}"
        d.news_meta(src_line)

        tags = []
        if n.get("emotional_trigger"):
            tags.append("Триггер: " + TRIGGER_RU.get(n["emotional_trigger"],
                                                       n["emotional_trigger"]))
        if n.get("category"):
            tags.append("Категория: " + CATEGORY_RU.get(n["category"], n["category"]))
        if tags:
            d.news_tags("   " + "   ·   ".join(tags))

        desc = _clean(n.get("description", ""))
        if desc:
            d.news_desc(f"   {desc[:280]}" + ("…" if len(desc) > 280 else ""))

        if n.get("original_url"):
            d.news_link(n["original_url"])

    d.br()
    d.divider()
    d.br()

    # ── БЛОК 2+3. УГЛЫ И ЗАГОЛОВКИ ───────────────────────────────────────────
    d.section_header(
        "Блок 2+3 — Маркетинговые углы и заголовки",
        count=f"{len(angles)} углов · {n_hl} заголовков"
    )

    for a in angles:
        pr = a.get("priority", "C")
        d.angle_header(pr, _clean(a.get("angle_title", "")))

        if a.get("news_title"):
            d.angle_detail("📰", "Инфоповод",
                           _clean(a["news_title"]))
        if a.get("creative_type"):
            d.angle_detail("🎯", "Тип",
                           CREATIVE_RU.get(a["creative_type"], a["creative_type"]))
        if a.get("target_pain"):
            d.angle_detail("💊", "Боль аудитории",
                           _clean(a["target_pain"]))
        if a.get("offer_connection"):
            d.angle_detail("💰", "Связь с оффером",
                           _clean(a["offer_connection"]))

        headlines = a.get("headlines", [])
        if headlines:
            d.headlines_label()
            for h in headlines:
                fmt_label = FORMAT_RU.get(h.get("format", ""), h.get("format", ""))
                chars     = h.get("character_count", len(h.get("text", "")))
                d.headline_row(_clean(h.get("text", "")), chars, fmt_label)

    d.br()
    d.divider()
    d.br()

    # ── БЛОК 4. РЕКОМЕНДАЦИИ ─────────────────────────────────────────────────
    if recs:
        d.section_header("Блок 4 — Топ-5 рекомендаций к тесту")

        for rec in recs[:5]:
            rank = rec.get("rank", "?")
            d.rec_header(rank, _clean(rec.get("angle_title", "")))

            if rec.get("news_title"):
                d.rec_detail("📰", "Инфоповод", _clean(rec["news_title"]))
            if rec.get("reasoning"):
                d.rec_detail("💬", "Обоснование", _clean(rec["reasoning"]))

            d.rec_scores(
                rec.get("freshness", ""),
                rec.get("trigger_strength", ""),
                rec.get("offer_fit", ""),
            )

        d.br()
        d.divider()
        d.br()

    # ── БЛОК 5. РИСКИ ────────────────────────────────────────────────────────
    if risks:
        d.section_header("Блок 5 — Оценка рисков", count=len(risks))

        for risk in risks:
            if risk.get("news_title"):
                d.risk_header(_clean(risk["news_title"]))

            legal = risk.get("legal_risks", [])
            if legal:
                d.risk_legal([_clean(x) for x in legal])

            d.risk_row(
                risk.get("platform_ban_risk", ""),
                risk.get("audience_negativity_risk", ""),
                risk.get("reputation_risk", ""),
            )

            if risk.get("expiry_date"):
                d.risk_expiry(risk["expiry_date"])

        d.br()
        d.divider()
        d.br()

    # ── БЛОК 6. СРОЧНОСТЬ ────────────────────────────────────────────────────
    d.section_header("Блок 6 — Срочность")

    urgent  = urg.get("urgent",  [])
    week    = urg.get("week",    [])
    eternal = urg.get("eternal", [])

    if urgent:
        d.urgency_group("🔥", "СРОЧНО — тестировать в ближайшие 48 часов",
                        len(urgent), C_RED)
        for t in urgent:
            d.urgency_bullet(_clean(t))

    if week:
        d.urgency_group("⏳", "НА НЕДЕЛЕ", len(week), C_ORANGE)
        for t in week:
            d.urgency_bullet(_clean(t))

    if eternal:
        d.urgency_group("♾️", "ВЕЧНЫЕ ТЕМЫ", len(eternal), C_GRAY)
        for t in eternal:
            d.urgency_bullet(_clean(t))

    d.br()
    d.divider_thick()
    d.br()

    # ── ПРОШЛЫЙ ВЫПУСК ───────────────────────────────────────────────────────
    if prev_liked:
        d.section_header(
            f"Что зашло в прошлый раз  (выпуск #{prev_id})"
        )
        d._add("   👍  Углы с положительной оценкой:",
               size_pt=10.5, italic=True, color=C_TEAL,
               indent=14, space_above=4, space_below=4)
        for a in prev_liked:
            d.prev_item(a.get("priority", "?"), _clean(a.get("angle_title", "")))
        d.br()

    return d.build_requests()

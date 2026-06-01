"""
NewsForge → Google Docs exporter — v3 (card-style, matching HTML template).

Воспроизводит визуальный стиль newsforge_template.html через
borderLeft + shading Google Docs API:
  • Цветная левая полоска срочности (как .acc-urgent / .acc-week / .acc-ever)
  • Тонированный фон карточки (как .tag-urgent bg / .tag-week bg / .tag-ever bg)
  • Цветные бейджи приоритета A/B/C  (как .grade-a / .grade-b)
  • Цветные бейджи рисков high/mid/low (как .rl-high / .rl-mid / .rl-low)
  • Топ-5 с пронумерованными карточками
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
SOURCE_RU    = {"top_media": "Топ СМИ", "local_tabloid": "Таблоид",
                "google_news": "Google News", "twitter_trend": "Twitter",
                "tiktok": "TikTok", "telegram": "Telegram", "forum": "Форум"}
CREATIVE_RU  = {"news": "Новостной", "emotional": "Эмоциональный",
                "investigation": "Разоблачение", "personal_story": "Личная история"}
FORMAT_RU    = {"question": "Вопрос", "shock": "Шок", "number": "Число",
                "quote": "Цитата", "intrigue": "Интрига"}
RISK_RU      = {"high": "Высокий", "medium": "Средний", "low": "Низкий"}
URGENCY_LABEL = {"urgent_48h": "Срочно · 48ч", "week": "На неделе", "eternal": "Вечная тема"}

# ── Цветовая палитра (точно как в HTML-шаблоне) ───────────────────────────────

def _rgb(r, g, b):
    return {"red": r / 255, "green": g / 255, "blue": b / 255}

# Акцентные цвета полоски (left border)
C_URGENT_ACC = _rgb(226, 75,  74)   # #E24B4A
C_WEEK_ACC   = _rgb(239, 159, 39)   # #EF9F27
C_EVER_ACC   = _rgb(29,  158, 117)  # #1D9E75

# Фоны карточек (shading)
C_URGENT_BG  = _rgb(252, 235, 235)  # #FCEBEB
C_WEEK_BG    = _rgb(254, 243, 226)  # #FEF3E2
C_EVER_BG    = _rgb(228, 247, 238)  # #E4F7EE
C_WHITE_BG   = _rgb(255, 255, 255)
C_CARD_BG    = _rgb(249, 249, 247)  # #F9F9F7  (body background)
C_GRAY_BG    = _rgb(246, 246, 244)  # #F6F6F4  (top-num background)

# Текстовые цвета тегов (совпадают с HTML)
C_URGENT_TXT = _rgb(163, 45,  45)   # #A32D2D
C_WEEK_TXT   = _rgb(133, 79,  11)   # #854F0B
C_EVER_TXT   = _rgb(15,  110, 86)   # #0F6E56

# Приоритеты
C_GRADE_A    = _rgb(15,  110, 86)   # grade-a text
C_GRADE_B    = _rgb(133, 79,  11)   # grade-b text
C_GRADE_C    = _rgb(100, 100, 100)

# Риски
C_RISK_H_TXT = _rgb(163, 45,  45)   # rl-high text
C_RISK_M_TXT = _rgb(133, 79,  11)   # rl-mid text
C_RISK_L_TXT = _rgb(59,  109, 17)   # rl-low text
C_RISK_H_BG  = _rgb(252, 235, 235)  # rl-high bg
C_RISK_M_BG  = _rgb(254, 243, 226)  # rl-mid bg
C_RISK_L_BG  = _rgb(234, 247, 238)  # rl-low bg

# Служебные
C_NAVY       = _rgb(15,  52,  96)
C_GRAY_TXT   = _rgb(100, 100, 100)
C_LIGHT_TXT  = _rgb(153, 153, 153)  # #999
C_BODY_TXT   = _rgb(26,  26,  26)   # #1a1a1a
C_BLUE_TXT   = _rgb(37,  99,  235)
C_GOLD_TXT   = _rgb(161, 98,  7)
C_DIVIDER    = _rgb(235, 235, 235)  # #ebebeb
C_INNER_DIV  = _rgb(240, 240, 238)  # #f0f0ee


# ── UTF-16 helper ─────────────────────────────────────────────────────────────

def _u16(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


# ── Утилиты текста ────────────────────────────────────────────────────────────

def _clean(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"&nbsp;",  " ", text)
    text = re.sub(r"&amp;",   "&", text)
    text = re.sub(r"&lt;",    "<", text)
    text = re.sub(r"&gt;",    ">", text)
    text = re.sub(r"&quot;",  '"', text)
    text = re.sub(r"&#\d+;",  "",  text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _short_url(url: str, max_len: int = 72) -> str:
    if not url or len(url) <= max_len:
        return url
    if "news.google.com" in url:
        return "news.google.com/…"
    try:
        from urllib.parse import urlparse
        p = urlparse(url)
        short = p.netloc + p.path[:40]
        return short + "…"
    except Exception:
        return url[:max_len] + "…"


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


# ── Border helpers ────────────────────────────────────────────────────────────

def _bspec(rgb: dict, width_pt: float = 1.0, pad_pt: float = 5.0) -> dict:
    return {
        "color":     {"color": {"rgbColor": rgb}},
        "width":     {"magnitude": width_pt, "unit": "PT"},
        "padding":   {"magnitude": pad_pt,   "unit": "PT"},
        "dashStyle": "SOLID",
    }


# ── DocBuilder ────────────────────────────────────────────────────────────────

class DocBuilder:
    def __init__(self):
        self._segs: list[dict] = []

    def _add(self, text: str, *,
             named_style: str = "NORMAL_TEXT",
             bold: bool = False,
             italic: bool = False,
             size_pt: float = None,
             color: dict = None,
             align: str = None,
             space_above: float = None,
             space_below: float = None,
             indent: float = None,
             border_left:   dict = None,
             border_top:    dict = None,
             border_bottom: dict = None,
             border_right:  dict = None,
             bg: dict = None):
        if text is not None:
            self._segs.append(dict(
                text=text + "\n",
                named_style=named_style,
                bold=bold, italic=italic,
                size_pt=size_pt, color=color,
                align=align,
                space_above=space_above, space_below=space_below,
                indent=indent,
                border_left=border_left, border_top=border_top,
                border_bottom=border_bottom, border_right=border_right,
                bg=bg,
            ))

    def br(self, above: float = 0, below: float = 0):
        self._add("", space_above=above, space_below=below)

    def build_requests(self) -> tuple[str, list[dict]]:
        full_text = "".join(s["text"] for s in self._segs)
        reqs: list[dict] = [
            {"insertText": {"location": {"index": 1}, "text": full_text}}
        ]

        pos = 1
        for seg in self._segs:
            ln   = _u16(seg["text"])
            end  = pos + ln
            cend = end - 1   # exclude trailing \n

            # ── Paragraph style ───────────────────────────────────────────────
            ps: dict = {}
            pf: list = []

            ns = seg.get("named_style", "NORMAL_TEXT")
            if ns and ns != "NORMAL_TEXT":
                ps["namedStyleType"] = ns; pf.append("namedStyleType")

            if seg.get("align"):
                ps["alignment"] = seg["align"]; pf.append("alignment")

            if seg.get("space_above") is not None:
                ps["spaceAbove"] = {"magnitude": seg["space_above"], "unit": "PT"}
                pf.append("spaceAbove")

            if seg.get("space_below") is not None:
                ps["spaceBelow"] = {"magnitude": seg["space_below"], "unit": "PT"}
                pf.append("spaceBelow")

            if seg.get("indent") is not None:
                ps["indentStart"] = {"magnitude": seg["indent"], "unit": "PT"}
                pf.append("indentStart")

            for side in ("left", "top", "bottom", "right"):
                spec = seg.get(f"border_{side}")
                if spec:
                    key = f"border{side.capitalize()}"
                    ps[key] = spec
                    pf.append(key)

            if seg.get("bg"):
                ps["shading"] = {
                    "backgroundColor": {"color": {"rgbColor": seg["bg"]}}
                }
                pf.append("shading")

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
                    ts["bold"] = True; tf.append("bold")
                if seg.get("italic"):
                    ts["italic"] = True; tf.append("italic")
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


# ── Credentials (unchanged) ───────────────────────────────────────────────────

def _load_credentials():
    try:
        from google.oauth2 import service_account
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
    except ImportError:
        print("[gdocs] Установи: pip install google-api-python-client google-auth")
        return None

    refresh_token = os.getenv("GOOGLE_OAUTH_REFRESH_TOKEN", "").strip()
    client_id     = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
    if refresh_token and client_id and client_secret:
        try:
            creds = Credentials(
                token=None, refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id, client_secret=client_secret, scopes=SCOPES,
            )
            creds.refresh(Request())
            print("[gdocs] OAuth2 (личный аккаунт)")
            return creds
        except Exception as e:
            print(f"[gdocs] OAuth2 ошибка: {e}")

    b64 = os.getenv("GOOGLE_CREDENTIALS_B64", "").strip()
    if b64:
        try:
            info = json.loads(base64.b64decode(b64).decode("utf-8"))
            creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
            print("[gdocs] Service Account (base64)")
            return creds
        except Exception as e:
            print(f"[gdocs] SA ошибка: {e}")

    path = os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH", "").strip()
    if path and os.path.exists(path):
        try:
            creds = service_account.Credentials.from_service_account_file(path, scopes=SCOPES)
            print("[gdocs] Service Account (файл)")
            return creds
        except Exception as e:
            print(f"[gdocs] SA файл ошибка: {e}")

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
    return bool(
        os.getenv("GOOGLE_OAUTH_REFRESH_TOKEN", "").strip() and
        os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip() and
        os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
    )


# ── Главная функция (unchanged) ───────────────────────────────────────────────

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

        geo       = report_data.get("geo", "GEO")
        report_id = report_data.get("report_id", "")
        date_str  = (report_data.get("created_at") or "")[:10]
        title_val = report_data.get("title", "").strip()
        doc_title = title_val or f"NewsForge — {geo} #{report_id} — {date_str}"

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
            print("[gdocs] Квота Drive исчерпана. Запусти: python setup_google_oauth.py")
        elif "notFound" in err or "404" in err:
            print("[gdocs] Папка не найдена. Проверь GOOGLE_DRIVE_FOLDER_ID")
        elif "403" in err:
            print(f"[gdocs] Нет доступа. Добавь {_get_sa_email()} как Editor")
        else:
            print(f"[gdocs] Ошибка: {exc}")
        return None


# ── Построение документа ──────────────────────────────────────────────────────

def _build_all_blocks(r: dict) -> tuple[str, list[dict]]:
    d = DocBuilder()

    geo        = r.get("geo", "GEO")
    news       = r.get("news", [])
    angles     = r.get("angles", [])
    recs       = r.get("recommendations", [])
    risks      = r.get("risks", [])
    urg        = r.get("urgency", {})
    prev_liked = r.get("prev_liked", [])
    stats      = r.get("stats", {})
    created_s  = _fmt_date(r.get("created_at", ""))
    title_val  = r.get("title", "").strip()
    report_id  = r.get("report_id", "")
    team_lead  = r.get("team_lead", "")
    prev_id    = r.get("prev_report_id", "")
    vertical   = r.get("vertical", "")
    keywords   = r.get("keywords", "")
    cover_days = r.get("coverage_days", 7)

    n_news = stats.get("total_news",      len(news))
    n_ang  = stats.get("total_angles",    len(angles))
    n_hl   = stats.get("total_headlines",
                        sum(len(a.get("headlines", [])) for a in angles))

    # ── ОБЛОЖКА ───────────────────────────────────────────────────────────────
    main_title = title_val or f"NewsForge — {geo} · Выпуск #{report_id}"
    d._add(main_title, bold=True, size_pt=22, color=C_NAVY,
           align="CENTER", space_above=14, space_below=4)

    sub_parts = [p for p in [geo, f"Выпуск #{report_id}", created_s] if p]
    d._add("  ·  ".join(sub_parts), size_pt=11, color=C_LIGHT_TXT,
           align="CENTER", space_above=2, space_below=2)

    meta_parts = [p for p in [
        f"Период: {cover_days} дн.",
        f"Тимлид: {team_lead}"              if team_lead else None,
        f"Предыдущий выпуск: #{prev_id}"    if prev_id   else None,
        f"Вертикаль: {vertical}"            if vertical  else None,
        f"Ключевые слова: {keywords}"       if keywords  else None,
    ] if p]
    if meta_parts:
        d._add("  ·  ".join(meta_parts), size_pt=10.5, color=C_LIGHT_TXT,
               align="CENTER", space_above=1, space_below=6)

    d._add(f"  📰  {n_news} инфоповодов     💡  {n_ang} углов     📝  {n_hl} заголовков",
           bold=True, size_pt=12, color=C_EVER_TXT, align="CENTER",
           space_above=6, space_below=10)

    # Толстый разделитель
    d._add("", border_bottom=_bspec(C_NAVY, width_pt=2, pad_pt=0),
           space_above=0, space_below=18)

    # ─────────────────────────────── БЛОК 1 — ИНФОПОВОДЫ ─────────────────────

    _section_title(d, "Блок 1 — Инфоповоды", n_news)

    _URGENCY_STYLE = {
        "urgent_48h": (C_URGENT_ACC, C_URGENT_BG, C_URGENT_TXT, "Срочно · 48ч"),
        "week":       (C_WEEK_ACC,   C_WEEK_BG,   C_WEEK_TXT,   "На неделе"),
        "eternal":    (C_EVER_ACC,   C_EVER_BG,   C_EVER_TXT,   "Вечная тема"),
    }

    for i, n in enumerate(news):
        urgency = n.get("urgency", "eternal")
        acc, bg, txt, tag_lbl = _URGENCY_STYLE.get(urgency, _URGENCY_STYLE["eternal"])
        bl = _bspec(acc, width_pt=3, pad_pt=6)

        # Meta (tag line)
        cat = CATEGORY_RU.get(n.get("category", ""), n.get("category", ""))
        src_parts = [n.get("source", ""),
                     SOURCE_RU.get(n.get("source_type", ""), n.get("source_type", ""))]
        pub = _fmt_date(n.get("published_at", ""))
        src_full = "  ·  ".join(p for p in src_parts if p)
        if pub:
            src_full += f"  ·  {pub}"
        meta_line = "  ".join(p for p in [tag_lbl, cat, src_full] if p)

        d._add(f"  {meta_line}",
               bold=True, size_pt=9.5, color=txt,
               border_left=bl, border_top=_bspec(C_DIVIDER, width_pt=0.5, pad_pt=0),
               bg=bg, space_above=10 if i == 0 else 8, space_below=0)

        # Title
        d._add(f"  {_clean(n.get('title', ''))}",
               bold=True, size_pt=11.5, color=C_BODY_TXT,
               border_left=bl, bg=C_WHITE_BG, space_above=0, space_below=0)

        # Description
        desc = _clean(n.get("description", ""))
        if desc:
            d._add(f"  {desc[:280]}{'…' if len(desc) > 280 else ''}",
                   italic=True, size_pt=10, color=C_GRAY_TXT,
                   border_left=_bspec(acc, width_pt=1.5, pad_pt=6),
                   bg=C_WHITE_BG, space_above=0, space_below=0)

        # Link
        url = n.get("original_url", "")
        if url:
            d._add(f"  🔗  {_short_url(url)}",
                   size_pt=9, color=C_BLUE_TXT, italic=True,
                   border_left=_bspec(acc, width_pt=1.5, pad_pt=6),
                   bg=C_WHITE_BG,
                   border_bottom=_bspec(C_INNER_DIV, width_pt=0.5, pad_pt=0),
                   space_above=0, space_below=2)
        else:
            # Close card bottom
            d._add("",
                   border_left=_bspec(acc, width_pt=1.5, pad_pt=6),
                   bg=C_WHITE_BG,
                   border_bottom=_bspec(C_INNER_DIV, width_pt=0.5, pad_pt=0),
                   space_above=0, space_below=2)

    d.br(above=4)
    _block_divider(d)

    # ─────────────────────────────── БЛОК 2+3 — УГЛЫ И ЗАГОЛОВКИ ─────────────

    _section_title(d, "Блок 2+3 — Маркетинговые углы и заголовки",
                   f"{len(angles)} углов · {n_hl} заголовков")

    _GRADE_STYLE = {
        "A": (C_GRADE_A, C_EVER_BG,   C_EVER_ACC,   "grade-a"),
        "B": (C_GRADE_B, C_WEEK_BG,   C_WEEK_ACC,   "grade-b"),
        "C": (C_GRADE_C, C_GRAY_BG,   C_GRAY_TXT,   "grade-c"),
    }

    for a in angles:
        pr = a.get("priority", "C")
        g_txt, g_bg, g_acc, _ = _GRADE_STYLE.get(pr, _GRADE_STYLE["C"])
        bl = _bspec(g_acc, width_pt=3, pad_pt=6)

        # Angle header (priority badge + title)
        d._add(f"  [{pr}]  {_clean(a.get('angle_title', ''))}",
               bold=True, size_pt=12, color=g_txt,
               border_left=bl, border_top=_bspec(C_DIVIDER, width_pt=0.5, pad_pt=0),
               bg=g_bg, space_above=12, space_below=0)

        # Инфоповод / тип / триггер
        meta_parts = []
        if a.get("news_title"):
            meta_parts.append(f"Инфоповод: {_clean(a['news_title'])}")
        if a.get("creative_type"):
            meta_parts.append(CREATIVE_RU.get(a["creative_type"], a["creative_type"]))
        if a.get("emotional_trigger"):
            meta_parts.append("Триггер: " + TRIGGER_RU.get(a.get("emotional_trigger",""), ""))
        if meta_parts:
            d._add(f"  {' · '.join(meta_parts)}",
                   size_pt=10, color=C_LIGHT_TXT,
                   border_left=_bspec(g_acc, width_pt=1, pad_pt=6),
                   bg=C_WHITE_BG, space_above=0, space_below=0)

        if a.get("target_pain"):
            d._add(f"  Боль: {_clean(a['target_pain'])}",
                   size_pt=10.5, color=C_GRAY_TXT,
                   border_left=_bspec(g_acc, width_pt=1, pad_pt=6),
                   bg=C_WHITE_BG, space_above=0, space_below=0)

        if a.get("offer_connection"):
            d._add(f"  {_clean(a['offer_connection'])}",
                   size_pt=10.5, italic=True, color=C_GRAY_TXT,
                   border_left=_bspec(g_acc, width_pt=2.5, pad_pt=6),
                   bg=C_WHITE_BG, space_above=0, space_below=0)

        headlines = a.get("headlines", [])
        if headlines:
            d._add("  📌  Заголовки:",
                   size_pt=9.5, bold=True, color=C_LIGHT_TXT,
                   border_left=_bspec(g_acc, width_pt=1, pad_pt=6),
                   border_top=_bspec(C_INNER_DIV, width_pt=0.5, pad_pt=0),
                   bg=C_WHITE_BG, space_above=6, space_below=0)

            for hi, h in enumerate(headlines):
                fmt_lbl = FORMAT_RU.get(h.get("format", ""), h.get("format", ""))
                chars   = h.get("character_count", len(h.get("text", "")))
                is_last = (hi == len(headlines) - 1)
                d._add(f"      ▸  {_clean(h.get('text',''))}   →   {chars} зн. · {fmt_lbl}",
                       size_pt=10.5, color=C_BODY_TXT,
                       border_left=_bspec(g_acc, width_pt=1, pad_pt=6),
                       border_bottom=_bspec(C_INNER_DIV, width_pt=0.5, pad_pt=0) if is_last else None,
                       bg=C_WHITE_BG, space_above=1, space_below=1 if not is_last else 4)
        else:
            # Close card
            d._add("", border_bottom=_bspec(C_INNER_DIV, width_pt=0.5, pad_pt=0),
                   bg=C_WHITE_BG, space_above=0, space_below=4)

    d.br(above=4)
    _block_divider(d)

    # ─────────────────────────────── БЛОК 4 — ТОП-5 ──────────────────────────

    if recs:
        _section_title(d, "Блок 4 — Топ-5 рекомендаций к тесту")

        for rec in recs[:5]:
            rank = rec.get("rank", "?")

            # Number badge (как .top-num в HTML)
            d._add(f"  {rank}   {_clean(rec.get('angle_title', ''))}",
                   bold=True, size_pt=12, color=C_BODY_TXT,
                   border_left=_bspec(C_GOLD_TXT, width_pt=3, pad_pt=6),
                   border_top=_bspec(C_DIVIDER, width_pt=0.5, pad_pt=0),
                   bg=C_GRAY_BG, space_above=12, space_below=0)

            if rec.get("news_title"):
                d._add(f"  Инфоповод: {_clean(rec['news_title'])}",
                       size_pt=10, color=C_LIGHT_TXT,
                       border_left=_bspec(C_GOLD_TXT, width_pt=1, pad_pt=6),
                       bg=C_WHITE_BG, space_above=0, space_below=0)

            if rec.get("reasoning"):
                d._add(f"  {_clean(rec['reasoning'])}",
                       size_pt=10.5, color=C_GRAY_TXT,
                       border_left=_bspec(C_GOLD_TXT, width_pt=1, pad_pt=6),
                       bg=C_WHITE_BG, space_above=0, space_below=0)

            scores = [p for p in [
                f"Свежесть: {rec['freshness']}"        if rec.get("freshness")        else None,
                f"Триггер: {rec['trigger_strength']}"  if rec.get("trigger_strength") else None,
                f"Оффер: {rec['offer_fit']}"            if rec.get("offer_fit")        else None,
            ] if p]
            if scores:
                d._add(f"  {'   ·   '.join(scores)}",
                       size_pt=9.5, color=C_EVER_TXT,
                       border_left=_bspec(C_GOLD_TXT, width_pt=1, pad_pt=6),
                       border_bottom=_bspec(C_INNER_DIV, width_pt=0.5, pad_pt=0),
                       bg=C_WHITE_BG, space_above=2, space_below=4)

        d.br(above=4)
        _block_divider(d)

    # ─────────────────────────────── БЛОК 5 — РИСКИ ───────────────────────────

    if risks:
        _section_title(d, "Блок 5 — Оценка рисков", len(risks))

        _RISK_STYLE = {
            "high":   (C_RISK_H_TXT, C_RISK_H_BG, C_URGENT_ACC),
            "medium": (C_RISK_M_TXT, C_RISK_M_BG, C_WEEK_ACC),
            "low":    (C_RISK_L_TXT, C_RISK_L_BG, C_EVER_ACC),
        }

        for risk in risks:
            ban = risk.get("platform_ban_risk",        "")
            neg = risk.get("audience_negativity_risk", "")
            rep = risk.get("reputation_risk",          "")
            # Pick the most severe level for the card accent
            severity_order = ["high", "medium", "low"]
            worst = next((s for s in severity_order if s in (ban, neg, rep)), "low")
            r_txt, r_bg, r_acc = _RISK_STYLE.get(worst, _RISK_STYLE["low"])
            bl = _bspec(r_acc, width_pt=3, pad_pt=6)

            if risk.get("news_title"):
                d._add(f"  {_clean(risk['news_title'])}",
                       bold=True, size_pt=11.5, color=C_BODY_TXT,
                       border_left=bl, border_top=_bspec(C_DIVIDER, width_pt=0.5, pad_pt=0),
                       bg=C_WHITE_BG, space_above=12, space_below=0)

            # Risk badges
            def _rbadge(label, val):
                style = _RISK_STYLE.get(val, _RISK_STYLE["low"])
                lbl   = RISK_RU.get(val, val)
                return f"{label}: {lbl}"

            badges_line = "     ".join([
                _rbadge("Бан", ban),
                _rbadge("Негатив", neg),
                _rbadge("Репутация", rep),
            ])
            d._add(f"  {badges_line}",
                   size_pt=10, bold=True, color=r_txt,
                   border_left=bl, bg=r_bg,
                   space_above=0, space_below=0)

            legal = risk.get("legal_risks", [])
            if legal:
                d._add(f"  ⚖️  {';  '.join(_clean(x) for x in legal)}",
                       size_pt=10, color=C_RISK_H_TXT,
                       border_left=_bspec(r_acc, width_pt=1, pad_pt=6),
                       bg=C_WHITE_BG, space_above=0, space_below=0)

            if risk.get("expiry_date"):
                d._add(f"  📅  Актуально до: {risk['expiry_date']}",
                       size_pt=10, italic=True, color=C_LIGHT_TXT,
                       border_left=_bspec(r_acc, width_pt=1, pad_pt=6),
                       border_bottom=_bspec(C_INNER_DIV, width_pt=0.5, pad_pt=0),
                       bg=C_WHITE_BG, space_above=0, space_below=4)

        d.br(above=4)
        _block_divider(d)

    # ─────────────────────────────── БЛОК 6 — СРОЧНОСТЬ ──────────────────────

    _section_title(d, "Блок 6 — Срочность")

    urgent  = urg.get("urgent",  [])
    week    = urg.get("week",    [])
    eternal = urg.get("eternal", [])

    _URG_GROUPS = [
        (urgent,  C_URGENT_TXT, C_URGENT_ACC, C_URGENT_BG, "Срочно — тестировать в ближайшие 48 часов"),
        (week,    C_WEEK_TXT,   C_WEEK_ACC,   C_WEEK_BG,   "На неделе"),
        (eternal, C_EVER_TXT,   C_EVER_ACC,   C_EVER_BG,   "Вечные темы"),
    ]
    for items, txt, acc, bg, label in _URG_GROUPS:
        if not items:
            continue
        d._add(f"  {label}  ({len(items)})",
               bold=True, size_pt=11, color=txt,
               space_above=10, space_below=4)
        for title_str in items:
            d._add(f"  {_clean(title_str)}",
                   size_pt=11, color=C_BODY_TXT,
                   border_left=_bspec(acc, width_pt=2, pad_pt=6),
                   border_top=_bspec(C_DIVIDER, width_pt=0.5, pad_pt=0),
                   border_bottom=_bspec(C_INNER_DIV, width_pt=0.5, pad_pt=0),
                   bg=C_WHITE_BG, space_above=2, space_below=2)

    d.br(above=6)
    # Финальный разделитель
    d._add("", border_bottom=_bspec(C_NAVY, width_pt=2, pad_pt=0),
           space_above=0, space_below=16)

    # ─────────────────────────────── ПРОШЛЫЙ ВЫПУСК ───────────────────────────

    if prev_liked:
        prev_label = f"Что зашло в прошлый раз (выпуск #{prev_id})" if prev_id else "Что зашло в прошлый раз"
        _section_title(d, prev_label)

        d._add("  👍  Углы с положительной оценкой:",
               size_pt=10.5, italic=True, color=C_EVER_TXT,
               space_above=4, space_below=4)

        for a in prev_liked:
            pr = a.get("priority", "?")
            g_txt, g_bg, g_acc, _ = _GRADE_STYLE.get(pr, _GRADE_STYLE["C"])
            d._add(f"  [{pr}]  {_clean(a.get('angle_title', ''))}",
                   size_pt=10.5, color=g_txt,
                   border_left=_bspec(g_acc, width_pt=2, pad_pt=6),
                   border_top=_bspec(C_DIVIDER, width_pt=0.5, pad_pt=0),
                   border_bottom=_bspec(C_INNER_DIV, width_pt=0.5, pad_pt=0),
                   bg=g_bg, space_above=2, space_below=2)

    return d.build_requests()


# ── Мелкие помощники ──────────────────────────────────────────────────────────

def _section_title(d: DocBuilder, label: str, count=None):
    tail = f"  ({count})" if count is not None else ""
    d._add(f"  {label.upper()}{tail}",
           bold=True, size_pt=11, color=C_LIGHT_TXT,
           space_above=18, space_below=6)


def _block_divider(d: DocBuilder):
    d._add("", border_bottom=_bspec(C_DIVIDER, width_pt=1, pad_pt=0),
           space_above=0, space_below=4)

"""
NewsForge → HTML Digest exporter.
Генерирует самодостаточный стилизованный HTML-отчёт из report_data.
"""
import html as _html
import re
from datetime import datetime

# ── Локализация ────────────────────────────────────────────────────────────────

TRIGGER_RU  = {"money": "Деньги", "crisis": "Кризис", "opportunity": "Возможность",
               "fear": "Страх", "trust": "Доверие"}
CATEGORY_RU = {"economy": "Экономика", "politics": "Политика", "social_media": "Соцсети",
               "celebrity": "Селеба", "scandal": "Скандал", "banks_taxes": "Банки/Налоги",
               "fears": "Страхи"}
SOURCE_RU   = {"top_media": "Топ СМИ", "local_tabloid": "Таблоид",
               "google_news": "Google News", "twitter_trend": "Twitter",
               "tiktok": "TikTok", "telegram": "Telegram", "forum": "Форум"}
CREATIVE_RU = {"news": "Новостной", "emotional": "Эмоциональный",
               "investigation": "Разоблачение", "personal_story": "Личная история"}
FORMAT_RU   = {"question": "Вопрос", "shock": "Шок", "number": "Число",
               "quote": "Цитата", "intrigue": "Интрига"}

_URGENCY = {
    "urgent_48h": ("acc-urgent", "tag-urgent", "Срочно · 48ч"),
    "week":       ("acc-week",   "tag-week",   "На неделе"),
    "eternal":    ("acc-ever",   "tag-ever",   "Вечная тема"),
}
_RISK_CLS = {"high": "rl-high", "medium": "rl-mid",  "low": "rl-low"}
_RISK_LBL = {"high": "Высокий", "medium": "Средний", "low": "Низкий"}
_GRADE    = {"A": "grade-a",    "B": "grade-b",      "C": "grade-c"}

# ── CSS (встроен inline, без внешних зависимостей) ────────────────────────────

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: #f9f9f7; color: #1a1a1a; padding: 2rem;
}
.wrap { max-width: 820px; margin: 0 auto; }

/* HEADER */
.header {
  display: flex; justify-content: space-between; align-items: flex-end;
  margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 1px solid #e0e0da;
}
.header-title { font-size: 20px; font-weight: 600; }
.header-sub   { font-size: 12px; color: #888; margin-top: 4px; }
.header-stats { display: flex; gap: 20px; text-align: right; }
.stat         { font-size: 12px; color: #888; }
.stat strong  { display: block; font-size: 22px; font-weight: 600;
                color: #1a1a1a; line-height: 1.1; }

/* BLOCK TITLE */
.block-title {
  font-size: 11px; font-weight: 600; letter-spacing: 0.07em; color: #999;
  text-transform: uppercase; margin: 2rem 0 0.75rem;
}

/* NEWS */
.card        { background: #fff; border: 1px solid #ebebeb; border-radius: 10px;
               overflow: hidden; margin-bottom: 6px; }
.news-item   { display: flex; align-items: stretch; }
.news-accent { width: 3px; flex-shrink: 0; }
.acc-urgent  { background: #E24B4A; }
.acc-week    { background: #EF9F27; }
.acc-ever    { background: #1D9E75; }
.news-body   { padding: 9px 14px; flex: 1; min-width: 0; }
.news-meta   { display: flex; align-items: center; gap: 6px; margin-bottom: 3px; flex-wrap: wrap; }
.tag         { font-size: 11px; font-weight: 600; padding: 1px 7px; border-radius: 4px; }
.tag-urgent  { background: #FCEBEB; color: #A32D2D; }
.tag-week    { background: #FEF3E2; color: #854F0B; }
.tag-ever    { background: #E4F7EE; color: #0F6E56; }
.tag-cat     { background: #f2f2f0; color: #666; }
.news-source { font-size: 11px; color: #bbb; }
.news-text   { font-size: 13px; color: #1a1a1a; line-height: 1.45; }
.news-desc   { font-size: 12px; color: #666; margin-top: 3px; line-height: 1.45; }
.news-link   { font-size: 11px; color: #3b82f6; margin-top: 3px;
               word-break: break-all; text-decoration: none; }
.news-link:hover { text-decoration: underline; }
.divider     { height: 1px; background: #f0f0ee; }

/* ANGLES */
.angle-card   { background: #fff; border: 1px solid #ebebeb; border-radius: 10px;
                padding: 12px 14px; margin-bottom: 6px; }
.angle-header { display: flex; gap: 8px; align-items: flex-start; margin-bottom: 6px; }
.angle-grade  { font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px;
                flex-shrink: 0; margin-top: 2px; }
.grade-a      { background: #E4F7EE; color: #0F6E56; }
.grade-b      { background: #FEF3E2; color: #854F0B; }
.grade-c      { background: #f2f2f0; color: #666; }
.angle-title  { font-size: 13px; font-weight: 600; color: #1a1a1a; line-height: 1.4; }
.angle-news   { font-size: 11px; color: #aaa; margin-bottom: 5px; }
.angle-pain   { font-size: 12px; color: #555; line-height: 1.5; margin-bottom: 7px; }
.angle-offer  { font-size: 12px; color: #555; line-height: 1.5;
                border-left: 2px solid #ddd; padding-left: 8px; }
.headlines    { display: flex; flex-direction: column; gap: 5px;
                margin-top: 10px; padding-top: 10px; border-top: 1px solid #f0f0ee; }
.headline-row { display: flex; gap: 8px; align-items: baseline; }
.headline-type { font-size: 11px; color: #bbb; min-width: 58px; flex-shrink: 0; }
.headline-text { font-size: 12px; color: #1a1a1a; line-height: 1.4; }
.hl-chars     { font-size: 11px; color: #ccc; margin-left: auto; white-space: nowrap; }

/* TOP-5 */
.top-card  { background: #fff; border: 1px solid #ebebeb; border-radius: 10px;
             overflow: hidden; margin-bottom: 6px; }
.top-num   { font-size: 12px; font-weight: 500; background: #f6f6f4;
             padding: 8px 14px; color: #666; display: flex; align-items: center; gap: 10px; }
.top-num span { font-size: 20px; font-weight: 700; color: #1a1a1a; }
.top-body  { padding: 10px 14px; }
.top-title { font-size: 13px; font-weight: 600; color: #1a1a1a;
             margin-bottom: 4px; line-height: 1.4; }
.top-news  { font-size: 11px; color: #aaa; margin-bottom: 6px; }
.top-reason { font-size: 12px; color: #555; line-height: 1.5; }
.top-scores { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
.score-tag  { font-size: 11px; background: #f2f2f0; color: #666;
              padding: 2px 8px; border-radius: 4px; }

/* RISKS */
.risk-card   { background: #fff; border: 1px solid #ebebeb; border-radius: 10px;
               padding: 10px 14px; margin-bottom: 6px; }
.risk-title  { font-size: 13px; font-weight: 600; color: #1a1a1a;
               margin-bottom: 8px; line-height: 1.4; }
.risk-levels { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 6px; }
.risk-level  { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px; }
.rl-high     { background: #FCEBEB; color: #A32D2D; }
.rl-mid      { background: #FEF3E2; color: #854F0B; }
.rl-low      { background: #EAF7EE; color: #3B6D11; }
.risk-text   { font-size: 12px; color: #555; line-height: 1.5; }

/* URGENCY */
.urgency-section { display: flex; flex-direction: column; gap: 14px; }
.urg-label   { font-size: 11px; font-weight: 600; margin-bottom: 6px; }
.urg-items   { display: flex; flex-direction: column; gap: 3px; }
.urg-item    { font-size: 13px; color: #1a1a1a; padding: 7px 10px;
               background: #fff; border: 1px solid #ebebeb; border-radius: 7px; }

/* PREV LIKED */
.prev-card   { background: #f9f0ff; border: 1px solid #e8d5f5; border-radius: 10px;
               padding: 10px 14px; margin-bottom: 6px; }
.prev-grade  { font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px;
               display: inline-block; margin-right: 6px; }
.prev-title  { font-size: 13px; color: #1a1a1a; line-height: 1.4; display: inline; }

@media print {
  body { padding: 0; background: #fff; }
  .wrap { max-width: 100%; }
}
"""

# ── Утилиты ───────────────────────────────────────────────────────────────────

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


def _h(text) -> str:
    """HTML-escape + clean."""
    return _html.escape(_clean(str(text or "")))


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


def _short_url(url: str, max_len: int = 80) -> str:
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


# ── Построители HTML-блоков ───────────────────────────────────────────────────

def _block_title(label: str) -> str:
    return f'<div class="block-title">{_h(label)}</div>\n'


def _news_block(news: list) -> str:
    if not news:
        return ""
    items_html = ""
    for i, n in enumerate(news):
        urgency = n.get("urgency", "eternal")
        acc_cls, tag_cls, tag_lbl = _URGENCY.get(urgency, ("acc-ever", "tag-ever", "Вечная тема"))

        cat   = CATEGORY_RU.get(n.get("category", ""), n.get("category", ""))
        src   = n.get("source", "")
        src_t = SOURCE_RU.get(n.get("source_type", ""), n.get("source_type", ""))
        src_full = "  ·  ".join(p for p in [src, src_t] if p)

        pub = _fmt_date(n.get("published_at", ""))
        if pub:
            src_full += f"  ·  {pub}"

        desc = _clean(n.get("description", ""))
        url  = n.get("original_url", "")

        desc_html = f'<div class="news-desc">{_h(desc[:280])}{"…" if len(desc) > 280 else ""}</div>' if desc else ""
        url_html  = ""
        if url:
            short = _short_url(url)
            url_html = f'<a class="news-link" href="{_h(url)}" target="_blank" rel="noopener">🔗 {_h(short)}</a>'

        divider = '<div class="divider"></div>\n' if i < len(news) - 1 else ""
        items_html += f"""
  <div class="news-item">
    <div class="news-accent {acc_cls}"></div>
    <div class="news-body">
      <div class="news-meta">
        <span class="tag {tag_cls}">{_h(tag_lbl)}</span>
        {"<span class='tag tag-cat'>" + _h(cat) + "</span>" if cat else ""}
        <span class="news-source">{_h(src_full)}</span>
      </div>
      <div class="news-text">{_h(n.get("title", ""))}</div>
      {desc_html}
      {url_html}
    </div>
  </div>
{divider}"""

    return _block_title("Блок 1 — Инфоповоды") + f'<div class="card">{items_html}</div>\n'


def _angles_block(angles: list) -> str:
    if not angles:
        return ""
    n_hl = sum(len(a.get("headlines", [])) for a in angles)
    html_out = _block_title(f"Блок 2+3 — Маркетинговые углы и заголовки  ({len(angles)} / {n_hl} заголовков)")

    for a in angles:
        pr    = a.get("priority", "C")
        grade = _GRADE.get(pr, "grade-c")

        news_t    = _h(a.get("news_title", ""))
        ctype     = CREATIVE_RU.get(a.get("creative_type", ""), a.get("creative_type", ""))
        trigger   = TRIGGER_RU.get(a.get("emotional_trigger", ""), "")
        meta_parts = [p for p in [news_t, _h(ctype), ("Триггер: " + _h(trigger)) if trigger else ""] if p]
        meta_line  = "  ·  ".join(meta_parts)

        pain_html  = f'<div class="angle-pain">Боль: {_h(a.get("target_pain", ""))}</div>' if a.get("target_pain") else ""
        offer_html = f'<div class="angle-offer">{_h(a.get("offer_connection", ""))}</div>' if a.get("offer_connection") else ""

        headlines = a.get("headlines", [])
        hl_rows = ""
        if headlines:
            for h in headlines:
                fmt   = FORMAT_RU.get(h.get("format", ""), h.get("format", ""))
                chars = h.get("character_count", len(h.get("text", "")))
                hl_rows += f"""
      <div class="headline-row">
        <span class="headline-type">{_h(fmt)}</span>
        <span class="headline-text">{_h(h.get("text", ""))}</span>
        <span class="hl-chars">{chars} зн.</span>
      </div>"""

        hl_block = f'<div class="headlines">{hl_rows}\n    </div>' if hl_rows else ""

        html_out += f"""<div class="angle-card">
  <div class="angle-header">
    <span class="angle-grade {grade}">{_h(pr)}</span>
    <div class="angle-title">{_h(a.get("angle_title", ""))}</div>
  </div>
  {"<div class='angle-news'>Инфоповод: " + meta_line + "</div>" if meta_line else ""}
  {pain_html}
  {offer_html}
  {hl_block}
</div>\n"""

    return html_out


def _recs_block(recs: list) -> str:
    if not recs:
        return ""
    html_out = _block_title("Блок 4 — Топ-5 рекомендаций к тесту")

    for rec in recs[:5]:
        rank   = rec.get("rank", "?")
        scores = [
            f"Свежесть: {rec['freshness']}"        if rec.get("freshness")        else None,
            f"Триггер: {rec['trigger_strength']}"   if rec.get("trigger_strength") else None,
            f"Оффер: {rec['offer_fit']}"             if rec.get("offer_fit")        else None,
        ]
        score_tags = "".join(
            f'<span class="score-tag">{_h(s)}</span>'
            for s in scores if s
        )
        scores_html = f'<div class="top-scores">{score_tags}</div>' if score_tags else ""

        html_out += f"""<div class="top-card">
  <div class="top-num"><span>{_h(rank)}</span>{_h(rec.get("angle_title", ""))}</div>
  <div class="top-body">
    {"<div class='top-news'>Инфоповод: " + _h(rec.get("news_title","")) + "</div>" if rec.get("news_title") else ""}
    {"<div class='top-reason'>" + _h(rec.get("reasoning","")) + "</div>" if rec.get("reasoning") else ""}
    {scores_html}
  </div>
</div>\n"""

    return html_out


def _risks_block(risks: list) -> str:
    if not risks:
        return ""
    html_out = _block_title(f"Блок 5 — Оценка рисков  ({len(risks)})")

    for risk in risks:
        ban = risk.get("platform_ban_risk",       "")
        neg = risk.get("audience_negativity_risk","")
        rep = risk.get("reputation_risk",         "")

        def _badge(label, val):
            cls = _RISK_CLS.get(val, "rl-low")
            lbl = _RISK_LBL.get(val, val)
            return f'<span class="risk-level {cls}">{_h(label)}: {_h(lbl)}</span>'

        badges = _badge("Бан", ban) + _badge("Негатив", neg) + _badge("Репутация", rep)
        if risk.get("expiry_date"):
            badges += f'<span class="risk-level rl-low">До: {_h(risk["expiry_date"])}</span>'

        legal = risk.get("legal_risks", [])
        legal_html = ""
        if legal:
            legal_html = f'<div class="risk-text">⚖️ {_h("; ".join(legal))}</div>'

        html_out += f"""<div class="risk-card">
  {"<div class='risk-title'>" + _h(risk.get("news_title","")) + "</div>" if risk.get("news_title") else ""}
  <div class="risk-levels">{badges}</div>
  {legal_html}
</div>\n"""

    return html_out


def _urgency_block(urg: dict) -> str:
    urgent  = urg.get("urgent",  [])
    week    = urg.get("week",    [])
    eternal = urg.get("eternal", [])

    def _group(color, label, items):
        if not items:
            return ""
        rows = "".join(f'<div class="urg-item">{_h(t)}</div>\n' for t in items)
        return f"""  <div>
    <div class="urg-label" style="color:{color};">{_h(label)}  ({len(items)})</div>
    <div class="urg-items">{rows}    </div>
  </div>\n"""

    body = (
        _group("#A32D2D", "Срочно — тестировать в ближайшие 48 часов", urgent) +
        _group("#854F0B", "На неделе",    week) +
        _group("#0F6E56", "Вечные темы", eternal)
    )
    if not body:
        return ""
    return _block_title("Блок 6 — Срочность") + f'<div class="urgency-section">\n{body}</div>\n'


def _prev_block(prev_liked: list, prev_id) -> str:
    if not prev_liked:
        return ""
    label = f"Что зашло в прошлый раз (выпуск #{prev_id})" if prev_id else "Что зашло в прошлый раз"
    items_html = ""
    for a in prev_liked:
        pr    = a.get("priority", "?")
        grade = _GRADE.get(pr, "grade-c")
        items_html += f"""<div class="prev-card">
  <span class="prev-grade {grade}">{_h(pr)}</span>
  <span class="prev-title">{_h(a.get("angle_title", ""))}</span>
</div>\n"""

    return _block_title(label) + items_html


# ── Главная функция ───────────────────────────────────────────────────────────

def generate_html(report_data: dict) -> str:
    """Возвращает полный HTML-дайджест по данным отчёта."""
    r = report_data

    geo        = r.get("geo", "GEO")
    report_id  = r.get("report_id") or r.get("id", "")
    created_s  = _fmt_date(r.get("created_at", ""))
    title_val  = r.get("title", "").strip()
    team_lead  = r.get("team_lead", "")
    prev_id    = r.get("prev_report_id", "")
    cover_days = r.get("coverage_days", 7)
    vertical   = r.get("vertical", "")
    keywords   = r.get("keywords", "")

    news     = r.get("news", [])
    angles   = r.get("angles", [])
    recs     = r.get("recommendations", [])
    risks    = r.get("risks", [])
    urg      = r.get("urgency", {})
    prev_lik = r.get("prev_liked", [])
    stats    = r.get("stats", {})

    n_news = stats.get("total_news",      len(news))
    n_ang  = stats.get("total_angles",    len(angles))
    n_hl   = stats.get("total_headlines",
                        sum(len(a.get("headlines", [])) for a in angles))

    doc_title = title_val or f"NewsForge — {geo} #{report_id} — {created_s}"

    sub_parts = [p for p in [
        created_s,
        f"Период: {cover_days} дн.",
        f"Тимлид: {team_lead}"              if team_lead else None,
        f"Предыдущий выпуск: #{prev_id}"    if prev_id   else None,
        f"Вертикаль: {vertical}"            if vertical  else None,
        f"Ключевые слова: {keywords}"       if keywords  else None,
    ] if p]
    sub_line = "  ·  ".join(sub_parts)

    header_title = title_val or f"NewsForge {geo} · Выпуск #{report_id}"

    body = "".join([
        _news_block(news),
        _angles_block(angles),
        _recs_block(recs),
        _risks_block(risks),
        _urgency_block(urg),
        _prev_block(prev_lik, prev_id),
    ])

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_h(doc_title)}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="wrap">

<div class="header">
  <div>
    <div class="header-title">{_h(header_title)}</div>
    <div class="header-sub">{_h(sub_line)}</div>
  </div>
  <div class="header-stats">
    <div class="stat"><strong>{n_news}</strong>инфоповодов</div>
    <div class="stat"><strong>{n_ang}</strong>углов</div>
    <div class="stat"><strong>{n_hl}</strong>заголовков</div>
  </div>
</div>

{body}
</div>
</body>
</html>"""

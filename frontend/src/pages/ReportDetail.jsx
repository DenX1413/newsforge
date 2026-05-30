import { useState, useMemo, useRef, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  ArrowLeft, Newspaper, Lightbulb, Type, ThumbsUp, ThumbsDown,
  Clock, Zap, ExternalLink, Copy, Check, Star, Shield,
  AlertTriangle, TrendingUp, History, ChevronDown, ChevronUp,
  Search, X, Filter, Trash2, FileText, Printer, Pencil,
} from "lucide-react";
import { useReport, setFeedback, deleteReport, toggleFavorite, updateReportTitle } from "../hooks/useApi.js";
import { GeoFlag } from "../components/ReportCard.jsx";

// ── Constants ─────────────────────────────────────────────────────────────────

const URGENCY = {
  urgent_48h: { label: "🔥 Срочно (48ч)", cls: "bg-red-500/15 text-red-400 border border-red-500/20" },
  week:       { label: "⏳ Неделя",        cls: "bg-amber-500/15 text-amber-400 border border-amber-500/20" },
  eternal:    { label: "♾️ Вечная",        cls: "bg-gray-700/60 text-gray-400 border border-gray-700" },
};
const TRIGGER_CLS = {
  money:       "bg-emerald-500/15 text-emerald-400",
  crisis:      "bg-red-500/15 text-red-400",
  opportunity: "bg-sky-500/15 text-sky-400",
  fear:        "bg-orange-500/15 text-orange-400",
  trust:       "bg-violet-500/15 text-violet-400",
};
const TRIGGER_RU  = { money:"Деньги", crisis:"Кризис", opportunity:"Возможность", fear:"Страх", trust:"Доверие" };
const CATEGORY_RU = { economy:"Экономика", politics:"Политика", social_media:"Соцсети", celebrity:"Селеба", scandal:"Скандал", banks_taxes:"Банки/налоги", fears:"Страхи" };
const PRIORITY_CLS = { A:"bg-emerald-500 text-white", B:"bg-amber-500 text-white", C:"bg-gray-600 text-white" };
const SOURCE_TYPE_RU = {
  top_media: "Топ СМИ", local_tabloid: "Таблоид",
  google_news: "Google News", twitter_trend: "Twitter", tiktok: "TikTok",
  telegram: "Telegram", forum: "Форум",
};
const RISK_CLS = { high: "text-red-400", medium: "text-amber-400", low: "text-emerald-400" };
const TYPE_RU = { news:"Новостной", emotional:"Эмоц.", investigation:"Расследование", personal_story:"Личная ист." };

function fmt(iso) {
  return new Date(iso).toLocaleString("ru-RU", {
    day:"2-digit", month:"long", year:"numeric", hour:"2-digit", minute:"2-digit",
  });
}

// ── Export util ───────────────────────────────────────────────────────────────

function buildExportText(report) {
  const hr = "─".repeat(56);
  const lines = [
    `NEWSFORGE — ОТЧЁТ ${report.geo} #${report.id}`,
    `Дата: ${fmt(report.created_at)}`,
    `Период: последние ${report.coverage_days ?? 7} дней`,
    report.team_lead ? `Тимлид: ${report.team_lead}` : "",
    `Всего: ${report.stats.total_news} новостей · ${report.stats.total_angles} углов · ${report.stats.total_headlines} заголовков`,
    "",
  ].filter(Boolean);

  if (report.recommendations?.length) {
    lines.push(hr, "ТОП-5 РЕКОМЕНДАЦИЙ К ТЕСТУ", hr);
    report.recommendations.forEach(r => {
      lines.push(`${r.rank}. [${r.angle_title}]`);
      lines.push(`   ${r.reasoning}`);
      lines.push("");
    });
  }

  lines.push(hr, `ИНФОПОВОДЫ (${report.news.length})`, hr);
  report.news.forEach((n, i) => {
    const pubDate = n.published_at ? new Date(n.published_at).toLocaleDateString("ru-RU", { day:"numeric", month:"short", year:"numeric" }) : null;
    lines.push(`${i + 1}. ${n.title}${pubDate ? ` (${pubDate})` : ""}`);
    lines.push(`   Источник: ${n.source} [${SOURCE_TYPE_RU[n.source_type] ?? n.source_type}]`);
    lines.push(`   Триггер: ${TRIGGER_RU[n.emotional_trigger] ?? n.emotional_trigger} | ${CATEGORY_RU[n.category] ?? n.category} | ${URGENCY[n.urgency]?.label ?? n.urgency}`);
    if (n.description) lines.push(`   ${n.description.slice(0, 200)}`);
    if (n.original_url) lines.push(`   ${n.original_url}`);
    lines.push("");
  });

  lines.push(hr, `УГЛЫ И ЗАГОЛОВКИ (${report.angles.length})`, hr);
  report.angles.forEach(a => {
    lines.push(`[${a.priority}] ${a.angle_title}`);
    if (a.news_title) lines.push(`   ← ${a.news_title}`);
    lines.push(`   Оффер: ${a.offer_connection}`);
    lines.push(`   Боль: ${a.target_pain}`);
    lines.push(`   Тип: ${TYPE_RU[a.creative_type] ?? a.creative_type}`);
    if (a.headlines?.length) {
      lines.push("   Заголовки:");
      a.headlines.forEach(h => lines.push(`     • ${h.text}  (${h.character_count} зн.)`));
    }
    lines.push("");
  });

  return lines.join("\n");
}

function buildPrintHtml(report) {
  const esc = s => String(s ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  const date = new Date(report.created_at).toLocaleString("ru-RU", {day:"2-digit",month:"long",year:"numeric",hour:"2-digit",minute:"2-digit"});

  const newsHtml = report.news.map((n,i) => {
    const badge = n.urgency==="urgent_48h" ? `<span style="color:#ef4444">🔥 Срочно</span>` : n.urgency==="eternal" ? `<span style="color:#6b7280">♾ Вечная</span>` : "";
    const pubDate = n.published_at ? new Date(n.published_at).toLocaleDateString("ru-RU", {day:"numeric",month:"short",year:"numeric"}) : "";
    return `<div style="margin-bottom:10px;padding:10px;background:#f9fafb;border-radius:6px;border-left:3px solid #e5e7eb">
      <div style="font-weight:600;color:#111">${i+1}. ${esc(n.title)} ${badge}</div>
      <div style="font-size:12px;color:#6b7280;margin-top:3px">
        ${n.source ? `<b>${esc(n.source)}</b> · ` : ""}${esc(SOURCE_TYPE_RU[n.source_type] ?? n.source_type)}${pubDate ? ` · ${pubDate}` : ""}
      </div>
    </div>`;
  }).join("");

  const anglesHtml = report.angles.map((a,i) => {
    const hl = a.headlines.map(h => `<li style="margin:3px 0;color:#374151">${esc(h.text)}</li>`).join("");
    const pCls = a.priority==="A" ? "#16a34a" : a.priority==="B" ? "#d97706" : "#6b7280";
    return `<div style="margin-bottom:16px;padding:12px;border:1px solid #e5e7eb;border-radius:8px">
      <div style="font-size:15px;font-weight:700;color:#111;margin-bottom:6px">
        <span style="background:${pCls};color:#fff;padding:1px 7px;border-radius:4px;font-size:12px;margin-right:6px">${esc(a.priority)}</span>${esc(a.angle_title)}
      </div>
      ${a.target_pain ? `<div style="font-size:12px;color:#6b7280;margin-bottom:4px"><b>Боль:</b> ${esc(a.target_pain)}</div>` : ""}
      ${a.offer_connection ? `<div style="font-size:12px;color:#6b7280;margin-bottom:6px"><b>Оффер:</b> ${esc(a.offer_connection)}</div>` : ""}
      ${hl ? `<div style="font-size:13px;font-weight:600;margin-bottom:4px">Заголовки:</div><ul style="margin:0;padding-left:20px">${hl}</ul>` : ""}
    </div>`;
  }).join("");

  const recsHtml = (report.recommendations ?? []).slice(0,5).map(r =>
    `<div style="margin-bottom:10px;padding:10px;background:#fffbeb;border-radius:6px;border-left:3px solid #f59e0b">
      <div style="font-weight:700">${esc(r.rank)}. ${esc(r.angle_title)}</div>
      ${r.reasoning ? `<div style="font-size:12px;color:#6b7280;margin-top:4px">${esc(r.reasoning)}</div>` : ""}
    </div>`
  ).join("");

  return `<!DOCTYPE html><html><head><meta charset="utf-8">
  <title>NewsForge — ${esc(report.geo)} #${report.id}</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Segoe UI',Arial,sans-serif;font-size:14px;color:#111;padding:32px;max-width:900px;margin:0 auto}
    h1{font-size:22px;font-weight:800;margin-bottom:4px}
    h2{font-size:16px;font-weight:700;margin:24px 0 12px;padding-bottom:6px;border-bottom:2px solid #e5e7eb}
    .meta{font-size:13px;color:#6b7280;margin-bottom:24px}
    @media print{body{padding:16px}h2{break-before:auto}}
  </style></head><body>
  <h1>NewsForge — Отчёт ${esc(report.geo)} #${report.id}</h1>
  <div class="meta">
    ${date}${report.team_lead ? ` · Тимлид: ${esc(report.team_lead)}` : ""}
    &nbsp;·&nbsp; ${report.stats.total_news} инфоповодов · ${report.stats.total_angles} углов · ${report.stats.total_headlines} заголовков
  </div>
  ${recsHtml ? `<h2>Топ-5 рекомендаций к тесту</h2>${recsHtml}` : ""}
  ${anglesHtml ? `<h2>Маркетинговые углы (${report.angles.length})</h2>${anglesHtml}` : ""}
  ${newsHtml ? `<h2>Инфоповоды (${report.news.length})</h2>${newsHtml}` : ""}
  </body></html>`;
}

function downloadTxt(text, filename) {
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

// ── Small helpers ─────────────────────────────────────────────────────────────

function CopyBtn({ text, small = false }) {
  const [ok, setOk] = useState(false);
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(text); setOk(true); setTimeout(() => setOk(false), 1500); }}
      className={`btn-ghost shrink-0 ${small ? "p-1" : "p-1.5"}`}
      title="Копировать"
    >
      {ok ? <Check size={small ? 11 : 13} className="text-emerald-400" /> : <Copy size={small ? 11 : 13} />}
    </button>
  );
}

function SectionTitle({ icon: Icon, iconCls, children, count }) {
  return (
    <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-2">
      <Icon size={14} className={iconCls} />
      {children}
      {count !== undefined && (
        <span className="text-gray-600 font-normal normal-case tracking-normal">({count})</span>
      )}
    </h2>
  );
}

// ── Block 6: Urgency ──────────────────────────────────────────────────────────

function UrgencyBlock({ news }) {
  const urgent  = news.filter(n => n.urgency === "urgent_48h");
  const week    = news.filter(n => n.urgency === "week");
  const eternal = news.filter(n => n.urgency === "eternal");

  const Col = ({ icon, label, items, cardCls, titleCls }) => (
    <div className={`card space-y-2 ${cardCls}`}>
      <p className={`text-sm font-semibold flex items-center gap-1.5 ${titleCls}`}>
        {icon} {label} <span className="ml-auto text-lg font-bold text-white">{items.length}</span>
      </p>
      {items.length === 0
        ? <p className="text-xs text-gray-600">Нет инфоповодов</p>
        : <ul className="space-y-1">
            {items.map(n => (
              <li key={n.id} className="flex items-start gap-1.5">
                <span className="text-gray-600 shrink-0 mt-0.5">·</span>
                <span className="text-xs text-gray-400 leading-snug line-clamp-2">{n.title}</span>
              </li>
            ))}
          </ul>
      }
    </div>
  );

  return (
    <section className="space-y-3">
      <SectionTitle icon={Zap} iconCls="text-amber-400">Срочность и актуальность</SectionTitle>
      <div className="grid gap-3 sm:grid-cols-3">
        <Col icon="🔥" label="Срочно (48ч)" items={urgent}  cardCls="bg-red-950/10 border-red-900/30"    titleCls="text-red-400" />
        <Col icon="⏳" label="На неделе"    items={week}    cardCls="bg-amber-950/10 border-amber-900/30" titleCls="text-amber-400" />
        <Col icon="♾️" label="Вечная тема"  items={eternal} cardCls=""                                    titleCls="text-gray-400" />
      </div>
    </section>
  );
}

// ── Block 4: Recommendations ──────────────────────────────────────────────────

function RecommendationCard({ rec, angle }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="card border border-amber-900/30 bg-amber-950/5 space-y-3">
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-full bg-amber-500 text-black text-sm font-bold flex items-center justify-center shrink-0">
          {rec.rank}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-white leading-snug">{rec.angle_title}</p>
          {rec.news_title && (
            <p className="text-xs text-gray-500 mt-0.5 flex items-center gap-1">
              <Newspaper size={10} /> {rec.news_title}
            </p>
          )}
        </div>
        {angle && <span className={`badge shrink-0 ${PRIORITY_CLS[angle.priority] ?? "bg-gray-600 text-white"}`}>{angle.priority}</span>}
      </div>

      <p className="text-xs text-gray-400 leading-relaxed">{rec.reasoning}</p>

      <button onClick={() => setOpen(v => !v)} className="flex items-center gap-1 text-xs text-gray-600 hover:text-gray-400 transition-colors">
        {open ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        {open ? "Скрыть" : "Подробнее"}
      </button>

      {open && (
        <div className="pt-2 border-t border-gray-800 grid grid-cols-3 gap-3 text-xs">
          {[["Свежесть", rec.freshness], ["Сила триггера", rec.trigger_strength], ["Соответствие офферу", rec.offer_fit]].map(([k, v]) => (
            <div key={k}>
              <p className="text-gray-600 uppercase tracking-wider text-[10px] mb-1">{k}</p>
              <p className="text-gray-300">{v}</p>
            </div>
          ))}
        </div>
      )}

      {angle?.headlines?.length > 0 && (
        <div className="pt-2 border-t border-gray-800 space-y-1">
          <p className="text-[10px] text-gray-600 uppercase tracking-wider">Топ-заголовки:</p>
          {angle.headlines.slice(0, 3).map(h => (
            <div key={h.id} className="flex items-center gap-2 bg-gray-800/50 rounded px-2.5 py-1">
              <span className="flex-1 text-xs text-gray-300">{h.text}</span>
              <span className="text-[10px] text-gray-600 shrink-0">{h.character_count} зн.</span>
              <CopyBtn text={h.text} small />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Block 1: News ─────────────────────────────────────────────────────────────

function fmtNewsDate(iso) {
  if (!iso) return null;
  const d    = new Date(iso);
  const diff = Date.now() - d;
  if (diff < 3_600_000)  return `${Math.floor(diff / 60_000)} мин. назад`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)} ч. назад`;
  if (diff < 172_800_000) return "вчера";
  return d.toLocaleDateString("ru-RU", { day: "numeric", month: "short" });
}

function NewsSection({ items }) {
  const [showAll, setShowAll] = useState(false);
  const visible = showAll ? items : items.slice(0, 8);
  return (
    <section className="space-y-3">
      <SectionTitle icon={Newspaper} count={items.length}>Инфоповоды</SectionTitle>
      <div className="grid gap-3 sm:grid-cols-2">
        {visible.map(n => {
          const urg     = URGENCY[n.urgency] ?? URGENCY.eternal;
          const dateStr = fmtNewsDate(n.published_at);
          return (
            <div key={n.id} className="card space-y-2.5">
              {/* Заголовок + ссылка */}
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-medium text-white leading-snug">{n.title}</p>
                {n.original_url && (
                  <a href={n.original_url} target="_blank" rel="noreferrer"
                     className="shrink-0 text-gray-600 hover:text-sky-400 transition-colors">
                    <ExternalLink size={13} />
                  </a>
                )}
              </div>

              {/* Описание */}
              {n.description && <p className="text-xs text-gray-500 line-clamp-2">{n.description}</p>}

              {/* Источник + дата публикации */}
              <div className="flex items-center gap-2 text-[11px] text-gray-600">
                <span className="font-medium text-gray-500">{n.source}</span>
                <span className="text-gray-700">·</span>
                <span className="uppercase tracking-wide text-[10px]">{SOURCE_TYPE_RU[n.source_type] ?? n.source_type}</span>
                {dateStr && (
                  <>
                    <span className="text-gray-700">·</span>
                    <span className="flex items-center gap-0.5">
                      <Clock size={10} className="text-gray-700" /> {dateStr}
                    </span>
                  </>
                )}
              </div>

              {/* Теги */}
              <div className="flex flex-wrap gap-1.5">
                <span className={`badge ${urg.cls}`}>{urg.label}</span>
                <span className={`badge ${TRIGGER_CLS[n.emotional_trigger] ?? "bg-gray-700 text-gray-400"}`}>
                  {TRIGGER_RU[n.emotional_trigger] ?? n.emotional_trigger}
                </span>
                <span className="badge bg-gray-800 text-gray-400">{CATEGORY_RU[n.category] ?? n.category}</span>
              </div>
            </div>
          );
        })}
      </div>
      {items.length > 8 && (
        <button onClick={() => setShowAll(v => !v)} className="btn-ghost w-full text-center text-sm py-2">
          {showAll ? "Скрыть" : `Показать ещё ${items.length - 8}`}
        </button>
      )}
    </section>
  );
}

// ── Angle card ────────────────────────────────────────────────────────────────

function AngleCard({ angle }) {
  const [fb, setFb] = useState(angle.feedback ?? 0);
  const vote = async (val) => {
    const next = fb === val ? 0 : val;
    setFb(next);
    await setFeedback(angle.id, next);
  };

  const copyText = [
    `[${angle.priority}] ${angle.angle_title}`,
    `Оффер: ${angle.offer_connection}`,
    `Боль: ${angle.target_pain}`,
    `Тип: ${TYPE_RU[angle.creative_type] ?? angle.creative_type}`,
    "",
    ...(angle.headlines ?? []).map(h => `• ${h.text}`),
  ].join("\n");

  return (
    <div className="card space-y-3">
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-semibold text-white leading-snug">{angle.angle_title}</p>
        <div className="flex items-center gap-1 shrink-0">
          <CopyBtn text={copyText} small />
          <span className={`badge ${PRIORITY_CLS[angle.priority] ?? "bg-gray-600 text-white"}`}>{angle.priority}</span>
        </div>
      </div>

      {angle.news_title && (
        <p className="text-[11px] text-gray-600 flex items-center gap-1 -mt-1">
          <Newspaper size={10} className="shrink-0" />
          <span className="line-clamp-1">{angle.news_title}</span>
        </p>
      )}

      <div className="space-y-1 text-xs text-gray-500">
        <p><span className="text-gray-600">Оффер:</span> {angle.offer_connection}</p>
        <p><span className="text-gray-600">Боль:</span> {angle.target_pain}</p>
        <p><span className="text-gray-600">Тип:</span> {TYPE_RU[angle.creative_type] ?? angle.creative_type}</p>
      </div>

      {angle.headlines?.length > 0 && (
        <div className="space-y-1.5 pt-1 border-t border-gray-800">
          <p className="text-[10px] font-medium text-gray-600 uppercase tracking-wider flex items-center gap-1">
            <Type size={10} /> Заголовки ({angle.headlines.length})
          </p>
          {angle.headlines.map(h => (
            <div key={h.id} className="flex items-center gap-2 bg-gray-800/60 rounded-lg px-3 py-1.5">
              <span className="flex-1 text-xs text-gray-300">{h.text}</span>
              <span className="text-[10px] text-gray-700 shrink-0">{h.format}</span>
              <span className="text-[10px] text-gray-600 shrink-0">{h.character_count} зн.</span>
              <CopyBtn text={h.text} small />
            </div>
          ))}
        </div>
      )}

      <div className="flex items-center gap-2 pt-1 border-t border-gray-800">
        <span className="text-xs text-gray-600">Оценить:</span>
        <button onClick={() => vote(1)}  className={`btn-ghost p-1.5 ${fb === 1  ? "text-emerald-400" : ""}`}><ThumbsUp   size={14} /></button>
        <button onClick={() => vote(-1)} className={`btn-ghost p-1.5 ${fb === -1 ? "text-red-400"     : ""}`}><ThumbsDown size={14} /></button>
      </div>
    </div>
  );
}

// ── Angles section with filter + search ───────────────────────────────────────

function AnglesSection({ angles }) {
  const [search,    setSearch]    = useState("");
  const [fPriority, setFPriority] = useState(null);
  const [fType,     setFType]     = useState(null);
  const [showAll,   setShowAll]   = useState(false);

  const filtered = useMemo(() => {
    return angles.filter(a => {
      if (fPriority && a.priority !== fPriority) return false;
      if (fType     && a.creative_type !== fType) return false;
      if (search) {
        const q = search.toLowerCase();
        return (
          a.angle_title.toLowerCase().includes(q) ||
          a.target_pain?.toLowerCase().includes(q) ||
          a.headlines?.some(h => h.text.toLowerCase().includes(q))
        );
      }
      return true;
    });
  }, [angles, search, fPriority, fType]);

  const visible   = showAll ? filtered : filtered.slice(0, 6);
  const hasFilter = !!search || !!fPriority || !!fType;
  const allHeadlines = angles.flatMap(a => a.headlines ?? []).map(h => h.text).join("\n");

  const Chip = ({ label, active, onClick }) => (
    <button
      onClick={onClick}
      className={`px-2.5 py-1 rounded-full text-xs transition-colors ${
        active ? "bg-sky-600 text-white" : "bg-gray-800 text-gray-500 hover:text-gray-300"
      }`}
    >
      {label}
    </button>
  );

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <SectionTitle icon={Lightbulb} count={filtered.length !== angles.length ? `${filtered.length}/${angles.length}` : angles.length}>
          Маркетинговые углы и заголовки
        </SectionTitle>
        {/* Copy all headlines */}
        <button
          onClick={() => navigator.clipboard.writeText(allHeadlines)}
          className="btn-ghost py-1 px-2.5 text-xs flex items-center gap-1.5"
          title="Скопировать все заголовки"
        >
          <Copy size={11} /> Все заголовки
        </button>
      </div>

      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Search */}
        <div className="relative flex-1 min-w-[180px]">
          <Search size={12} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Поиск по углам и заголовкам…"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-8 pr-8 py-1.5 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-sky-500 transition-colors"
          />
          {search && (
            <button onClick={() => setSearch("")} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-400">
              <X size={12} />
            </button>
          )}
        </div>

        {/* Priority filter */}
        <div className="flex gap-1">
          {["A","B","C"].map(p => (
            <Chip key={p} label={p} active={fPriority === p} onClick={() => setFPriority(fPriority === p ? null : p)} />
          ))}
        </div>

        {/* Type filter */}
        <div className="flex gap-1">
          {[
            ["news","Новостной"], ["emotional","Эмоц."],
            ["investigation","Расслед."], ["personal_story","История"],
          ].map(([v, l]) => (
            <Chip key={v} label={l} active={fType === v} onClick={() => setFType(fType === v ? null : v)} />
          ))}
        </div>

        {/* Clear */}
        {hasFilter && (
          <button onClick={() => { setSearch(""); setFPriority(null); setFType(null); }}
            className="text-xs text-gray-600 hover:text-gray-400 flex items-center gap-1">
            <X size={11} /> Сбросить
          </button>
        )}
      </div>

      {filtered.length === 0 ? (
        <div className="card text-center py-8 text-gray-600 text-sm">
          <Filter size={20} className="mx-auto mb-2 text-gray-700" />
          Нет углов под текущий фильтр
        </div>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2">
            {visible.map(a => <AngleCard key={a.id} angle={a} />)}
          </div>
          {filtered.length > 6 && (
            <button onClick={() => setShowAll(v => !v)} className="btn-ghost w-full text-center text-sm py-2">
              {showAll ? "Скрыть" : `Показать ещё ${filtered.length - 6}`}
            </button>
          )}
        </>
      )}
    </section>
  );
}

// ── Block 5: Risks ────────────────────────────────────────────────────────────

function RisksSection({ risks }) {
  if (!risks?.length) return null;
  return (
    <section className="space-y-3">
      <SectionTitle icon={Shield} iconCls="text-red-400" count={risks.length}>Оценка рисков</SectionTitle>
      <div className="grid gap-3 sm:grid-cols-2">
        {risks.map((r, i) => (
          <div key={i} className="card space-y-2.5 border border-red-900/20">
            {r.news_title && (
              <p className="text-xs font-medium text-gray-300 flex items-center gap-1">
                <Newspaper size={11} /> {r.news_title}
              </p>
            )}
            <div className="grid grid-cols-3 gap-2 text-xs">
              {[["Бан", r.platform_ban_risk], ["Негатив", r.audience_negativity_risk], ["Репутация", r.reputation_risk]].map(([l, v]) => (
                <div key={l}>
                  <p className="text-gray-600 text-[10px]">{l}</p>
                  <p className={`font-medium ${RISK_CLS[v] ?? "text-gray-400"}`}>
                    {v === "high" ? "Высокий" : v === "medium" ? "Средний" : "Низкий"}
                  </p>
                </div>
              ))}
            </div>
            {r.legal_risks?.length > 0 && (
              <ul className="space-y-0.5">
                {r.legal_risks.map((lr, j) => (
                  <li key={j} className="text-xs text-gray-500 flex items-start gap-1">
                    <AlertTriangle size={10} className="shrink-0 mt-0.5 text-amber-500" /> {lr}
                  </li>
                ))}
              </ul>
            )}
            <p className="text-[10px] text-gray-600">Срок: <span className="text-gray-400">{r.expiry_date}</span></p>
          </div>
        ))}
      </div>
    </section>
  );
}

// ── Prev performance ──────────────────────────────────────────────────────────

function PrevPerformance({ prev, prevReportId }) {
  if (!prev?.count) return null;
  return (
    <section className="space-y-3">
      <SectionTitle icon={History} iconCls="text-violet-400" count={prev.count}>
        Что зашло в прошлый раз
        {prevReportId && (
          <Link to={`/report/${prevReportId}`}
            className="ml-2 text-xs text-gray-600 hover:text-sky-400 transition-colors font-normal normal-case tracking-normal">
            → Отчёт #{prevReportId}
          </Link>
        )}
      </SectionTitle>
      <div className="grid gap-2 sm:grid-cols-2">
        {prev.liked.map(a => (
          <div key={a.id} className="card flex items-center gap-3 bg-violet-950/10 border-violet-900/30">
            <ThumbsUp size={14} className="text-violet-400 shrink-0" />
            <p className="text-sm text-white leading-snug line-clamp-2 flex-1">{a.angle_title}</p>
            <span className={`badge shrink-0 ${PRIORITY_CLS[a.priority] ?? "bg-gray-600 text-white"}`}>{a.priority}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

// ── Main ──────────────────────────────────────────────────────────────────────

export default function ReportDetail() {
  const { id }    = useParams();
  const navigate  = useNavigate();
  const { report, loading } = useReport(id);
  const [copied,        setCopied]        = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting,      setDeleting]      = useState(false);
  const [favorite,      setFavorite]      = useState(false);
  const [favLoading,    setFavLoading]    = useState(false);
  const [titleValue,    setTitleValue]    = useState("");
  const [titleEditing,  setTitleEditing]  = useState(false);
  const [titleSaving,   setTitleSaving]   = useState(false);
  const titleInputRef = useRef(null);

  // Синхронизируем favorite и title один раз при загрузке отчёта
  useEffect(() => {
    if (report) {
      setFavorite(!!report.is_favorite);
      setTitleValue(report.title || "");
    }
  }, [report?.id]); // только при смене отчёта, не на каждом рендере

  if (loading) return (
    <div className="space-y-4">
      {[1,2,3].map(i => <div key={i} className="card animate-pulse h-32 bg-gray-800/50" />)}
    </div>
  );
  if (!report) return <div className="p-6 text-gray-500">Отчёт не найден</div>;

  const angleById = Object.fromEntries(report.angles.map(a => [a.id, a]));

  // Риски приходят напрямую из API (БД), fallback — старый JSON blob
  let risks = [];
  if (report.risks?.length) {
    risks = report.risks;
  } else {
    try {
      const data = report.data ? JSON.parse(report.data) : {};
      risks = (data.risks ?? []).map((r, i) => ({ ...r, news_title: r.news_title || report.news[i]?.title || "" }));
    } catch (_) {}
  }

  const handleCopyAll = () => {
    navigator.clipboard.writeText(buildExportText(report));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handlePdf = () => {
    const w = window.open("", "_blank");
    w.document.write(buildPrintHtml(report));
    w.document.close();
    w.focus();
    setTimeout(() => { w.print(); }, 400);
  };

  const handleDocx = () => {
    const a = document.createElement("a");
    a.href = `/api/reports/${report.id}/export.docx`;
    a.download = `newsforge-${report.geo}-${report.id}.docx`;
    a.click();
  };

  const handleDelete = async () => {
    setDeleting(true);
    await deleteReport(report.id);
    navigate("/");
  };

  const handleFavorite = async () => {
    setFavLoading(true);
    const res = await toggleFavorite(report.id);
    setFavorite(res.is_favorite);
    setFavLoading(false);
  };

  const openTitleEdit = () => {
    setTitleEditing(true);
    setTimeout(() => titleInputRef.current?.focus(), 0);
  };

  const saveTitle = async () => {
    setTitleSaving(true);
    await updateReportTitle(report.id, titleValue.trim());
    setTitleSaving(false);
    setTitleEditing(false);
  };

  const cancelTitle = () => {
    setTitleValue(report.title || "");
    setTitleEditing(false);
  };

  return (
    <div className="space-y-8">

      {/* ── Header ── */}
      <div className="card space-y-4">
        <div className="flex items-start gap-3 flex-wrap">
          <button onClick={() => navigate(-1)} className="btn-ghost flex items-center gap-1.5 py-1.5 -ml-1 text-sm shrink-0">
            <ArrowLeft size={14} /> Назад
          </button>

          <div className="flex-1 min-w-0">
            {/* Editable title */}
            {titleEditing ? (
              <div className="flex items-center gap-2 mb-1">
                <input
                  ref={titleInputRef}
                  value={titleValue}
                  onChange={e => setTitleValue(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === "Enter")  saveTitle();
                    if (e.key === "Escape") cancelTitle();
                  }}
                  onBlur={saveTitle}
                  maxLength={500}
                  placeholder="Название отчёта…"
                  className="flex-1 bg-gray-800 border border-sky-500/60 rounded-lg px-3 py-1.5 text-lg font-bold text-white placeholder-gray-600 focus:outline-none"
                />
                <button onClick={saveTitle}  disabled={titleSaving} className="p-1.5 rounded-lg text-emerald-400 hover:bg-emerald-500/10"><Check size={16} /></button>
                <button onClick={cancelTitle} className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-700"><X size={16} /></button>
              </div>
            ) : (
              <div className="flex items-center gap-2 mb-1 group/htitle">
                <h1
                  className={`text-xl font-bold leading-tight cursor-text ${titleValue ? "text-white" : "text-gray-600 italic"}`}
                  onClick={openTitleEdit}
                  title="Нажмите чтобы переименовать"
                >
                  {titleValue || "Без названия"}
                </h1>
                <button onClick={openTitleEdit} className="p-1 rounded text-gray-700 hover:text-gray-400 opacity-0 group-hover/htitle:opacity-100 transition-all" title="Переименовать">
                  <Pencil size={13} />
                </button>
              </div>
            )}

            {/* GEO / id / teamlead row */}
            <div className="flex items-center gap-2 flex-wrap">
              <span className="flex items-center gap-1.5 text-sm text-gray-500">
                <GeoFlag geo={report.geo} size={16} /> {report.geo}
                <span className="text-gray-600">#{report.id}</span>
              </span>
              {report.team_lead && (
                <span className="text-xs text-gray-600 flex items-center gap-1">
                  <Star size={11} className="text-amber-500" /> {report.team_lead}
                </span>
              )}
            </div>

            <div className="flex flex-wrap gap-3 mt-1 text-xs text-gray-500">
              <span className="flex items-center gap-1"><Clock size={11} /> {fmt(report.created_at)}</span>
              <span className="flex items-center gap-1"><Newspaper size={11} className="text-gray-700" /> Период: {report.coverage_days ?? 7} дней</span>
              {report.prev_report_id && (
                <Link to={`/report/${report.prev_report_id}`}
                  className="flex items-center gap-1 hover:text-sky-400 transition-colors">
                  <History size={11} /> Предыдущий #{report.prev_report_id}
                </Link>
              )}
            </div>
          </div>

          {/* Stats + export */}
          <div className="flex items-center gap-4 flex-wrap">
            {[
              { label:"Новостей",   value:report.stats.total_news,      Icon:Newspaper },
              { label:"Углов",      value:report.stats.total_angles,    Icon:Lightbulb },
              { label:"Заголовков", value:report.stats.total_headlines, Icon:Type },
            ].map(({ label, value, Icon }) => (
              <div key={label} className="text-center">
                <p className="text-lg font-bold text-white tabular-nums">{value}</p>
                <p className="text-[11px] text-gray-600 flex items-center gap-1 justify-center"><Icon size={10} /> {label}</p>
              </div>
            ))}

            {/* Export + Delete */}
            <div className="flex gap-1.5 ml-2 flex-wrap">
              {/* Favourite */}
              <button
                onClick={handleFavorite}
                disabled={favLoading}
                className={`btn-ghost py-1.5 px-2.5 flex items-center gap-1.5 text-xs transition-colors ${
                  favorite ? "text-amber-400 hover:text-amber-300" : "hover:text-amber-400"
                }`}
                title={favorite ? "Убрать из избранного" : "Добавить в избранное"}
              >
                <Star size={13} fill={favorite ? "currentColor" : "none"} />
                {favorite ? "Избранное" : "В избранное"}
              </button>

              <button
                onClick={handleCopyAll}
                className="btn-ghost py-1.5 px-2.5 flex items-center gap-1.5 text-xs"
                title="Скопировать текст отчёта"
              >
                {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
                {copied ? "Скопировано" : "Копировать"}
              </button>

              <button
                onClick={handlePdf}
                className="btn-ghost py-1.5 px-2.5 flex items-center gap-1.5 text-xs"
                title="Сохранить как PDF"
              >
                <Printer size={13} /> PDF
              </button>

              <button
                onClick={handleDocx}
                className="btn-ghost py-1.5 px-2.5 flex items-center gap-1.5 text-xs"
                title="Скачать DOCX"
              >
                <FileText size={13} /> DOCX
              </button>

              {report.gdocs_url && (
                <a
                  href={report.gdocs_url}
                  target="_blank"
                  rel="noreferrer"
                  className="btn-ghost py-1.5 px-2.5 flex items-center gap-1.5 text-xs text-emerald-400 hover:text-emerald-300"
                  title="Открыть в Google Docs"
                >
                  <ExternalLink size={13} /> Docs
                </a>
              )}

              {/* Delete */}
              {!confirmDelete ? (
                <button
                  onClick={() => setConfirmDelete(true)}
                  className="btn-ghost py-1.5 px-2.5 flex items-center gap-1.5 text-xs text-gray-600 hover:text-red-400 hover:bg-red-500/10"
                  title="Удалить отчёт"
                >
                  <Trash2 size={13} />
                </button>
              ) : (
                <div className="flex items-center gap-1.5 border border-red-900/40 rounded-lg px-2 py-1">
                  <span className="text-xs text-gray-400">Удалить?</span>
                  <button
                    onClick={handleDelete}
                    disabled={deleting}
                    className="text-xs px-2 py-0.5 rounded bg-red-500/20 text-red-400 hover:bg-red-500/30 font-medium"
                  >
                    {deleting ? "…" : "Да"}
                  </button>
                  <button
                    onClick={() => setConfirmDelete(false)}
                    className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-400 hover:bg-gray-700"
                  >
                    Нет
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ── Block 6 ── */}
      {report.news.length > 0 && <UrgencyBlock news={report.news} />}

      {/* ── Block 4 ── */}
      {report.recommendations?.length > 0 && (
        <section className="space-y-3">
          <SectionTitle icon={TrendingUp} iconCls="text-amber-400" count={report.recommendations.length}>
            Рекомендации к тесту
          </SectionTitle>
          <div className="grid gap-3 sm:grid-cols-2">
            {report.recommendations.map(rec => (
              <RecommendationCard key={rec.rank} rec={rec} angle={angleById[rec.angle_id]} />
            ))}
          </div>
        </section>
      )}

      {/* ── What worked ── */}
      {report.prev_performance?.count > 0 && (
        <PrevPerformance prev={report.prev_performance} prevReportId={report.prev_report_id} />
      )}

      {/* ── Block 1 ── */}
      {report.news.length > 0 && <NewsSection items={report.news} />}

      {/* ── Blocks 2+3 ── */}
      {report.angles.length > 0 && <AnglesSection angles={report.angles} />}

      {/* ── Block 5 ── */}
      <RisksSection risks={risks} />
    </div>
  );
}

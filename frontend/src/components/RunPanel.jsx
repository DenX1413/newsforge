import { useState, useCallback } from "react";
import { Play, FlaskConical, User, ChevronDown, CheckCheck, Globe, Tag } from "lucide-react";
import { triggerRun } from "../hooks/useApi.js";
import { GeoFlag } from "./ReportCard.jsx";
import { useLang } from "../hooks/useLang.js";

const GEOS = ["RU", "UA", "BY", "KZ", "IN", "BR", "MX", "DE", "PL"];

const GEO_SEL = {
  RU: "border-red-500/60 text-red-300 bg-red-500/15",
  UA: "border-yellow-500/60 text-yellow-300 bg-yellow-500/15",
  BY: "border-green-500/60 text-green-300 bg-green-500/15",
  KZ: "border-blue-500/60 text-blue-300 bg-blue-500/15",
  IN: "border-orange-500/60 text-orange-300 bg-orange-500/15",
  BR: "border-emerald-500/60 text-emerald-300 bg-emerald-500/15",
  MX: "border-lime-500/60 text-lime-300 bg-lime-500/15",
  DE: "border-purple-500/60 text-purple-300 bg-purple-500/15",
  PL: "border-pink-500/60 text-pink-300 bg-pink-500/15",
};

const GEO_LANG = {
  RU: "русский", UA: "украинский", BY: "белорусский",
  KZ: "русский", IN: "English", BR: "português",
  MX: "español", DE: "Deutsch", PL: "polski",
};

export default function RunPanel({ onDone }) {
  const { t } = useLang();

  const VERTICALS = [
    { value: "",              label: t("no_vertical") },
    { value: "финансы",       label: "💰 Финансы / инвестиции" },
    { value: "крипто",        label: "₿ Крипто / блокчейн" },
    { value: "форекс",        label: "📈 Форекс / трейдинг" },
    { value: "займы",         label: "🏦 Займы / кредиты" },
    { value: "e-commerce",    label: "🛒 E-commerce" },
    { value: "образование",   label: "🎓 Образование" },
    { value: "недвижимость",  label: "🏠 Недвижимость" },
    { value: "гемблинг",      label: "🎰 Гемблинг / ставки" },
    { value: "custom",        label: t("custom_keywords") },
  ];

  const [selected, setSelected]   = useState(new Set(["RU"]));
  const [useMock, setUseMock]     = useState(false);
  const [teamLead, setTeamLead]   = useState("");
  const [showLead, setShowLead]   = useState(false);
  const [vertical, setVertical]   = useState("");
  const [keywords, setKeywords]   = useState("");
  const [language, setLanguage]   = useState("");

  const [running, setRunning]   = useState(false);
  const [progress, setProgress] = useState(null);  // { pct, message }
  const [multiDone, setMultiDone] = useState(null); // "Запущено N задач"
  const [error, setError]       = useState(null);

  const toggleGeo = (g) => {
    if (running) return;
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(g) && next.size > 1) next.delete(g);
      else next.add(g);
      return next;
    });
    setMultiDone(null);
    setError(null);
  };

  const isSingle = selected.size === 1;
  const geoList  = [...selected];

  // ── Single GEO run with polling progress ─────────────────────────────────
  const runSingle = useCallback(async (geo) => {
    setError(null);
    setRunning(true);
    setProgress({ pct: 5, message: `${t("running_btn")}` });

    const vert = vertical === "custom" ? "" : vertical;
    const kw   = vertical === "custom" ? keywords : "";
    const lang = language || GEO_LANG[geo] || "";
    const { report_id } = await triggerRun(geo, useMock, teamLead, vert, kw, lang);

    const STEPS = [
      "RSS & Google News…",
      "Haiku…",
      "Sonnet angles…",
      "Sonnet headlines…",
      "Risks & recs…",
      "Report…",
    ];
    let stepIdx = 0;
    let pct = 10;

    const poll = setInterval(async () => {
      try {
        const r   = await fetch(`/api/reports/${report_id}`);
        const data = await r.json();

        if (data.status === "done") {
          clearInterval(poll);
          setProgress({ pct: 100, message: t("report_ready") });
          setRunning(false);
          onDone?.(report_id);
          return;
        }
        if (data.status === "error") {
          clearInterval(poll);
          setError(t("status_error"));
          setRunning(false);
          return;
        }
        // animate
        pct = Math.min(pct + 4, 88);
        stepIdx = Math.min(Math.floor(pct / 15), STEPS.length - 1);
        setProgress({ pct, message: STEPS[stepIdx] });
      } catch (_) {}
    }, 5000);

    setTimeout(() => { clearInterval(poll); if (running) { setError("Timeout"); setRunning(false); } }, 600000);
  }, [useMock, teamLead, onDone]);

  // ── Multi GEO run ─────────────────────────────────────────────────────────
  const runMulti = useCallback(async () => {
    setError(null);
    setRunning(true);
    setMultiDone(null);
    setProgress({ pct: 0, message: `${t("launched")} ${geoList.join(", ")}…` });

    const ids = [];
    for (const g of geoList) {
      try {
        const vert = vertical === "custom" ? "" : vertical;
        const kw   = vertical === "custom" ? keywords : "";
        const lang = language || GEO_LANG[g] || "";
        const { report_id } = await triggerRun(g, useMock, teamLead, vert, kw, lang);
        ids.push({ geo: g, id: report_id });
        await new Promise(r => setTimeout(r, 400));
      } catch (e) {
        console.error(e);
      }
    }

    setProgress({ pct: 100, message: `${t("launched")} ${ids.length}` });
    setMultiDone(`${t("launched")} ${ids.length} ${t("tasks_launched")}`);
    setRunning(false);
    onDone?.();           // refresh reports list (no specific report_id)
  }, [geoList, useMock, teamLead, onDone]);

  const handleRun = () => {
    if (isSingle) runSingle(geoList[0]);
    else runMulti();
  };

  const btnLabel = running
    ? t("running_btn")
    : isSingle
    ? `${t("run_btn")} ${geoList[0]}`
    : `${t("run_btn")} ${geoList.length} GEO`;

  return (
    <div className="card space-y-3">
      {/* ── Row 1: GEO + controls ── */}
      <div className="flex flex-wrap items-center gap-2">

        {/* GEO toggles */}
        <div className="flex gap-1.5 flex-wrap">
          {GEOS.map((g) => (
            <button
              key={g}
              onClick={() => toggleGeo(g)}
              disabled={running}
              className={`px-2.5 py-1.5 rounded-lg text-xs font-semibold border transition-all select-none flex items-center gap-1.5 ${
                selected.has(g)
                  ? GEO_SEL[g]
                  : "border-gray-700 text-gray-600 hover:text-sky-400 hover:border-sky-500/50 bg-transparent"
              }`}
            >
              <GeoFlag geo={g} size={16} />{g}
            </button>
          ))}
        </div>

        {/* "Select all" shortcut */}
        <button
          onClick={() => setSelected(new Set(GEOS))}
          disabled={running || selected.size === GEOS.length}
          className="text-[11px] text-gray-600 hover:text-gray-400 transition-colors disabled:opacity-30 flex items-center gap-1"
          title={t("all_filter")}
        >
          <CheckCheck size={12} /> {t("all_filter")}
        </button>

        <div className="flex-1" />

        {/* Demo toggle */}
        <label className="flex items-center gap-1.5 cursor-pointer select-none">
          <div
            onClick={() => !running && setUseMock(v => !v)}
            className={`w-7 h-3.5 rounded-full transition-colors relative ${useMock ? "bg-amber-500" : "bg-gray-700"} ${running ? "opacity-40" : "cursor-pointer"}`}
          >
            <div className={`absolute top-0.5 w-2.5 h-2.5 rounded-full bg-white transition-transform ${useMock ? "translate-x-3.5" : "translate-x-0.5"}`} />
          </div>
          <span className="text-xs text-gray-500 flex items-center gap-1">
            <FlaskConical size={10} /> Demo
          </span>
        </label>

        {/* Team lead toggle */}
        <button
          onClick={() => setShowLead(v => !v)}
          className={`btn-ghost py-1 px-2 flex items-center gap-1 text-xs ${showLead ? "text-sky-400" : ""}`}
        >
          <User size={11} />
          <ChevronDown size={10} className={`transition-transform ${showLead ? "rotate-180" : ""}`} />
        </button>

        {/* Run */}
        <button
          className="btn-primary flex items-center gap-1.5 py-2 px-4 text-sm"
          disabled={running}
          onClick={handleRun}
        >
          <Play size={12} className={running ? "animate-pulse" : ""} />
          {btnLabel}
        </button>
      </div>

      {/* ── Vertical + language row ── */}
      <div className="flex flex-wrap gap-2 pt-1 border-t border-gray-800">
        {/* Vertical selector */}
        <div className="flex items-center gap-1.5 flex-1 min-w-[180px]">
          <Tag size={12} className="text-violet-400 shrink-0" />
          <select
            value={vertical}
            onChange={e => { setVertical(e.target.value); setKeywords(""); }}
            disabled={running}
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs text-white focus:outline-none focus:border-sky-500 transition-colors"
          >
            {VERTICALS.map(v => (
              <option key={v.value} value={v.value}>{v.label}</option>
            ))}
          </select>
        </div>

        {/* Custom keywords */}
        {vertical === "custom" && (
          <input
            type="text"
            value={keywords}
            onChange={e => setKeywords(e.target.value)}
            placeholder={t("keywords_placeholder")}
            disabled={running}
            className="flex-1 min-w-[200px] bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-sky-500 transition-colors"
          />
        )}

        {/* Language override */}
        <div className="flex items-center gap-1.5">
          <Globe size={12} className="text-sky-400 shrink-0" />
          <select
            value={language}
            onChange={e => setLanguage(e.target.value)}
            disabled={running}
            className="bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-xs text-white focus:outline-none focus:border-sky-500 transition-colors"
          >
            <option value="">{t("lang_by_geo")}</option>
            <option value="русский">🇷🇺 Русский</option>
            <option value="украинский">🇺🇦 Украинский</option>
            <option value="English">🇬🇧 English</option>
            <option value="español">🇲🇽 Español</option>
            <option value="português">🇧🇷 Português</option>
            <option value="Deutsch">🇩🇪 Deutsch</option>
            <option value="polski">🇵🇱 Polski</option>
          </select>
        </div>
      </div>

      {/* ── Team lead input ── */}
      {showLead && (
        <div className="flex items-center gap-2 pt-1 border-t border-gray-800">
          <User size={12} className="text-gray-600 shrink-0" />
          <input
            type="text"
            value={teamLead}
            onChange={e => setTeamLead(e.target.value)}
            placeholder={t("teamlead_placeholder")}
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-sky-500 transition-colors"
          />
        </div>
      )}

      {/* ── Progress bar (single run) ── */}
      {running && progress && (
        <div className="space-y-1.5 pt-1 border-t border-gray-800">
          <div className="flex justify-between text-xs text-gray-500">
            <span>{progress.message}</span>
            <span className="tabular-nums">{progress.pct}%</span>
          </div>
          <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-sky-500 rounded-full transition-all duration-700"
              style={{ width: `${progress.pct}%` }}
            />
          </div>
        </div>
      )}

      {/* ── Success states ── */}
      {!running && progress?.pct === 100 && !multiDone && (
        <p className="text-xs text-emerald-400 pt-1 border-t border-gray-800">{t("report_ready")}</p>
      )}
      {multiDone && (
        <p className="text-xs text-sky-400 pt-1 border-t border-gray-800">{multiDone}</p>
      )}

      {/* ── Error ── */}
      {error && (
        <p className="text-xs text-red-400 bg-red-950/40 px-3 py-2 rounded-lg border border-red-900/30">
          ⚠ {error}
        </p>
      )}
    </div>
  );
}

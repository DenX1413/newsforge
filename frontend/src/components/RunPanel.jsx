import { useState, useCallback } from "react";
import { Play, FlaskConical, User, ChevronDown, CheckCheck } from "lucide-react";
import { triggerRun } from "../hooks/useApi.js";
import { GeoFlag } from "./ReportCard.jsx";

const GEOS = ["RU", "UA", "BY", "KZ", "DE", "PL"];

const GEO_SEL = {
  RU: "border-red-500/60 text-red-300 bg-red-500/15",
  UA: "border-yellow-500/60 text-yellow-300 bg-yellow-500/15",
  BY: "border-green-500/60 text-green-300 bg-green-500/15",
  KZ: "border-blue-500/60 text-blue-300 bg-blue-500/15",
  DE: "border-purple-500/60 text-purple-300 bg-purple-500/15",
  PL: "border-orange-500/60 text-orange-300 bg-orange-500/15",
};

export default function RunPanel({ onDone }) {
  const [selected, setSelected] = useState(new Set(["RU"]));
  const [useMock, setUseMock]   = useState(false);
  const [teamLead, setTeamLead] = useState("");
  const [showLead, setShowLead] = useState(false);

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
    setProgress({ pct: 5, message: "Инициализация…" });

    const { report_id } = await triggerRun(geo, useMock, teamLead);

    const STEPS = [
      "Парсинг RSS и Google News…",
      "Классификация статей (Haiku)…",
      "Генерация углов (Sonnet)…",
      "Генерация заголовков (Sonnet)…",
      "Оценка рисков и рекомендации…",
      "Формирование отчёта…",
    ];
    let stepIdx = 0;
    let pct = 10;

    const poll = setInterval(async () => {
      try {
        const r   = await fetch(`/api/reports/${report_id}`);
        const data = await r.json();

        if (data.status === "done") {
          clearInterval(poll);
          setProgress({ pct: 100, message: "Готово!" });
          setRunning(false);
          onDone?.(report_id);
          return;
        }
        if (data.status === "error") {
          clearInterval(poll);
          setError("Ошибка — смотри логи бэкенда");
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
    setProgress({ pct: 0, message: `Запускаю ${geoList.join(", ")}…` });

    const ids = [];
    for (const g of geoList) {
      try {
        const { report_id } = await triggerRun(g, useMock, teamLead);
        ids.push({ geo: g, id: report_id });
        await new Promise(r => setTimeout(r, 400));
      } catch (e) {
        console.error(e);
      }
    }

    setProgress({ pct: 100, message: `Запущено ${ids.length} задач` });
    setMultiDone(`🚀 Запущено ${ids.length} задач — следите во вкладке «Отчёты»`);
    setRunning(false);
    onDone?.();           // refresh reports list (no specific report_id)
  }, [geoList, useMock, teamLead, onDone]);

  const handleRun = () => {
    if (isSingle) runSingle(geoList[0]);
    else runMulti();
  };

  const btnLabel = running
    ? "Работает…"
    : isSingle
    ? `Запустить ${geoList[0]}`
    : `Запустить ${geoList.length} GEO`;

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
                  : "border-gray-700 text-gray-600 hover:text-gray-400 hover:border-gray-600 bg-transparent"
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
          title="Выбрать все GEO"
        >
          <CheckCheck size={12} /> Все
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

      {/* ── Team lead input ── */}
      {showLead && (
        <div className="flex items-center gap-2 pt-1 border-t border-gray-800">
          <User size={12} className="text-gray-600 shrink-0" />
          <input
            type="text"
            value={teamLead}
            onChange={e => setTeamLead(e.target.value)}
            placeholder="Имя тимлида (для уведомления)"
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
        <p className="text-xs text-emerald-400 pt-1 border-t border-gray-800">✓ Отчёт готов</p>
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

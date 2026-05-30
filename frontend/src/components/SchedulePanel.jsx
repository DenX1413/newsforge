import { useState } from "react";
import { CalendarClock, Clock, CheckCircle, RotateCw } from "lucide-react";
import { useSchedule, updateSchedule } from "../hooks/useApi.js";
import { GeoFlag } from "./ReportCard.jsx";

const INTERVAL_OPTIONS = [
  { label: "Каждые 5 минут",  value: 0.083 },   // 5/60 ≈ 0.083 h — for testing
  { label: "Каждый час",      value: 1 },
  { label: "Каждые 6 часов",  value: 6 },
  { label: "Каждые 12 часов", value: 12 },
  { label: "Раз в сутки",     value: 24 },
  { label: "Каждые 3 дня",    value: 72 },
  { label: "Каждые 4 дня",    value: 96 },
  { label: "Раз в неделю",    value: 168 },
];

const GEO_COLOR = {
  RU: "bg-red-500/20 text-red-400 border-red-500/30",
  UA: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  BY: "bg-green-500/20 text-green-400 border-green-500/30",
  KZ: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  DE: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  PL: "bg-orange-500/20 text-orange-400 border-orange-500/30",
};

function fmt(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("ru-RU", {
    day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
  });
}

function GeoRow({ item, onSave }) {
  const [interval, setInterval] = useState(item.interval_hours);
  const [enabled, setEnabled]   = useState(item.enabled);
  const [saving,  setSaving]    = useState(false);
  const [saved,   setSaved]     = useState(false);

  const handleSave = async () => {
    setSaving(true);
    await onSave(item.geo, { interval_hours: interval, enabled });
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const changed = interval !== item.interval_hours || enabled !== item.enabled;

  return (
    <div className={`flex flex-wrap items-center gap-4 px-4 py-3 rounded-xl border transition-colors ${
      enabled ? "border-gray-700 bg-gray-800/30" : "border-gray-800 bg-transparent"
    }`}>
      {/* GEO badge с флагом */}
      <div className={`w-12 h-12 rounded-xl flex flex-col items-center justify-center border shrink-0 gap-0.5 ${GEO_COLOR[item.geo] ?? "bg-gray-700 text-gray-300 border-gray-600"}`}>
        <GeoFlag geo={item.geo} size={20} />
        <span className="text-[10px] font-bold leading-none">{item.geo}</span>
      </div>

      {/* Interval select */}
      <div className="flex-1 min-w-[160px]">
        <label className="text-[10px] text-gray-600 uppercase tracking-wider block mb-1">Интервал</label>
        <select
          value={interval}
          onChange={e => setInterval(Number(e.target.value))}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2.5 py-1.5 text-sm text-white focus:outline-none focus:border-sky-500"
        >
          {INTERVAL_OPTIONS.map(o => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      {/* Last / Next run */}
      <div className="text-xs text-gray-500 space-y-0.5 min-w-[150px]">
        <p className="flex items-center gap-1">
          <Clock size={10} /> Последний: {fmt(item.last_run)}
        </p>
        <p className="flex items-center gap-1">
          <CalendarClock size={10} /> Следующий: {fmt(item.next_run)}
        </p>
      </div>

      {/* Enable toggle */}
      <label className="flex items-center gap-2 cursor-pointer select-none">
        <div
          onClick={() => setEnabled(v => !v)}
          className={`w-10 h-5 rounded-full transition-colors relative cursor-pointer ${enabled ? "bg-sky-600" : "bg-gray-700"}`}
        >
          <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform ${enabled ? "translate-x-5" : "translate-x-0.5"}`} />
        </div>
        <span className="text-xs text-gray-400 w-16">
          {enabled ? "Включён" : "Выключен"}
        </span>
      </label>

      {/* Save */}
      <button
        onClick={handleSave}
        disabled={!changed || saving}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
          saved    ? "bg-emerald-600/20 text-emerald-400" :
          changed  ? "bg-sky-600 text-white hover:bg-sky-500" :
                     "bg-gray-800 text-gray-600 cursor-not-allowed"
        }`}
      >
        {saving ? <RotateCw size={12} className="animate-spin" /> :
         saved  ? <CheckCircle size={12} /> : null}
        {saved ? "Сохранено" : "Сохранить"}
      </button>

      {/* No scheduler warning */}
      {!item.scheduler_available && enabled && (
        <p className="text-[10px] text-amber-500 w-full -mt-2">
          ⚠ APScheduler не установлен. Запустите: pip install apscheduler
        </p>
      )}
    </div>
  );
}

export default function SchedulePanel() {
  const { schedule, loading, refetch } = useSchedule();

  const handleSave = async (geo, data) => {
    await updateSchedule(geo, data);
    refetch();
  };

  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
          <CalendarClock size={14} className="text-sky-400" /> Расписание автозапуска
        </h2>
        <span className="text-xs text-gray-600">Пайплайн запускается автоматически</span>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => <div key={i} className="h-16 bg-gray-800/50 rounded-xl animate-pulse" />)}
        </div>
      ) : (
        <div className="space-y-2">
          {schedule.map(item => (
            <GeoRow key={item.geo} item={item} onSave={handleSave} />
          ))}
        </div>
      )}
    </div>
  );
}

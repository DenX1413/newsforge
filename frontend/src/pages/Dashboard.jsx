import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import RunPanel from "../components/RunPanel.jsx";
import ReportCard, { GeoFlag } from "../components/ReportCard.jsx";
import SchedulePanel from "../components/SchedulePanel.jsx";
import { useReports } from "../hooks/useApi.js";
import { CalendarClock, List, Star, RotateCw } from "lucide-react";

const GEOS = ["Все", "RU", "UA", "BY", "KZ", "IN", "BR", "MX", "DE", "PL"];

export default function Dashboard() {
  const navigate = useNavigate();
  const [geo,          setGeo]          = useState(null);
  const [tab,          setTab]          = useState("reports");
  const [onlyFavorite, setOnlyFavorite] = useState(false);
  const { reports, loading, refetch } = useReports(geo, onlyFavorite);

  const activeReports = useMemo(
    () => reports.filter(r => r.status === "pending" || r.status === "running"),
    [reports]
  );

  function handleDone(reportId) {
    refetch();
    if (reportId) navigate(`/report/${reportId}`);
  }

  return (
    <div className="space-y-5">

      {/* ── Run panel ── */}
      <RunPanel onDone={handleDone} />

      {/* ── Tabs: Reports / Schedule ── */}
      <div className="flex items-center justify-between border-b border-gray-800 pb-0 gap-4">
        <div className="flex gap-0">
          {[
            { id: "reports",  label: "Отчёты",    icon: List },
            { id: "schedule", label: "Расписание", icon: CalendarClock },
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px ${
                tab === id
                  ? "border-sky-500 text-white"
                  : "border-transparent text-gray-500 hover:text-gray-300"
              }`}
            >
              <Icon size={13} />
              {label}
              {id === "reports" && reports.length > 0 && (
                <span className="ml-1 text-[10px] bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded-full">
                  {reports.length}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* GEO + Favourite filter */}
        {tab === "reports" && (
          <div className="flex gap-1 pb-2 flex-wrap">
            {GEOS.map((g) => (
              <button
                key={g}
                onClick={() => { setGeo(g === "Все" ? null : g); setOnlyFavorite(false); }}
                className={`px-2.5 py-1 rounded-md text-xs transition-colors flex items-center gap-1.5 ${
                  !onlyFavorite && (geo ?? "Все") === g
                    ? "bg-gray-700 text-white"
                    : "text-gray-600 hover:text-gray-300"
                }`}
              >
                {g !== "Все" && <GeoFlag geo={g} size={14} />}
                {g}
              </button>
            ))}

            <div className="w-px bg-gray-800 mx-1" />

            <button
              onClick={() => { setOnlyFavorite(v => !v); setGeo(null); }}
              className={`px-2.5 py-1 rounded-md text-xs transition-colors flex items-center gap-1.5 ${
                onlyFavorite
                  ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                  : "text-gray-600 hover:text-amber-400"
              }`}
            >
              <Star size={12} fill={onlyFavorite ? "currentColor" : "none"} />
              Избранные
            </button>
          </div>
        )}
      </div>

      {/* ── Active reports polling indicator ── */}
      {tab === "reports" && activeReports.length > 0 && (
        <div className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-sky-950/30 border border-sky-800/30 text-xs text-sky-400">
          <RotateCw size={12} className="animate-spin shrink-0" />
          <span>
            {activeReports.length === 1
              ? `Отчёт #${activeReports[0].id} (${activeReports[0].geo}) генерируется...`
              : `${activeReports.length} отчёта генерируются...`
            }
            {" "}Страница обновится автоматически.
          </span>
        </div>
      )}

      {/* ── Reports ── */}
      {tab === "reports" && (
        loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => <div key={i} className="card animate-pulse h-[72px] bg-gray-800/50" />)}
          </div>
        ) : reports.length === 0 ? (
          <div className="card text-center py-16 text-gray-600">
            <div className="w-12 h-12 bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-3">
              <List size={20} className="text-gray-700" />
            </div>
            <p className="font-medium mb-1">Нет отчётов</p>
            <p className="text-sm">Выберите GEO выше и нажмите «Генерировать»</p>
          </div>
        ) : (
          <div className="space-y-2.5">
            {reports.map(r => (
              <ReportCard key={r.id} report={r} onDelete={refetch} onFavoriteToggle={refetch} />
            ))}
          </div>
        )
      )}

      {/* ── Schedule ── */}
      {tab === "schedule" && <SchedulePanel />}
    </div>
  );
}

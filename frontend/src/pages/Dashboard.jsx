import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import RunPanel from "../components/RunPanel.jsx";
import ReportCard, { GeoFlag } from "../components/ReportCard.jsx";
import SchedulePanel from "../components/SchedulePanel.jsx";
import { useReports } from "../hooks/useApi.js";
import { useLang } from "../hooks/useLang.js";
import { CalendarClock, List, Star, RotateCw } from "lucide-react";

const GEOS_LIST = ["RU", "UA", "BY", "KZ", "IN", "BR", "MX", "DE", "PL"];

export default function Dashboard() {
  const navigate = useNavigate();
  const { t } = useLang();
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

      {/* ── Tabs ── */}
      <div className="flex items-center justify-between border-b border-gray-800 pb-0 gap-4">
        <div className="flex gap-0">
          {[
            { id: "reports",  labelKey: "reports_tab",  icon: List },
            { id: "schedule", labelKey: "schedule_tab", icon: CalendarClock },
          ].map(({ id, labelKey, icon: Icon }) => (
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
              {t(labelKey)}
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
            <button
              key="all"
              onClick={() => { setGeo(null); setOnlyFavorite(false); }}
              className={`px-2.5 py-1 rounded-md text-xs transition-colors flex items-center gap-1.5 ${
                !onlyFavorite && geo === null
                  ? "bg-gray-700 text-white"
                  : "text-gray-600 hover:text-gray-300"
              }`}
            >
              {t("all_filter")}
            </button>
            {GEOS_LIST.map((g) => (
              <button
                key={g}
                onClick={() => { setGeo(g); setOnlyFavorite(false); }}
                className={`px-2.5 py-1 rounded-md text-xs transition-colors flex items-center gap-1.5 ${
                  !onlyFavorite && geo === g
                    ? "bg-gray-700 text-white"
                    : "text-gray-600 hover:text-gray-300"
                }`}
              >
                <GeoFlag geo={g} size={14} /> {g}
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
              {t("favorites_filter")}
            </button>
          </div>
        )}
      </div>

      {/* ── Active polling indicator ── */}
      {tab === "reports" && activeReports.length > 0 && (
        <div className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-sky-950/30 border border-sky-800/30 text-xs text-sky-400">
          <RotateCw size={12} className="animate-spin shrink-0" />
          <span>
            {activeReports.length === 1
              ? `#${activeReports[0].id} (${activeReports[0].geo}) ${t("generating")}`
              : `${activeReports.length} ${t("reports_generating")}`
            }
            {" "}{t("auto_refresh")}
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
            <p className="font-medium mb-1">{t("no_reports")}</p>
            <p className="text-sm">{t("no_reports_hint")}</p>
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

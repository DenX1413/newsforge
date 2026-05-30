import { Outlet, Link, useLocation } from "react-router-dom";
import { Zap, FileText, Lightbulb, Type, ThumbsUp, Settings } from "lucide-react";
import { useStats } from "../hooks/useApi.js";

function StatPill({ icon: Icon, value, label, color }) {
  if (value == null) return null;
  return (
    <div className="flex items-center gap-1.5 text-xs text-gray-400" title={label}>
      <Icon size={12} className={color} />
      <span className="font-semibold text-white tabular-nums">{value}</span>
      <span className="text-gray-600 hidden md:inline">{label}</span>
    </div>
  );
}

export default function Layout() {
  const stats    = useStats();
  const location = useLocation();
  const onSettings = location.pathname === "/settings";

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">

      {/* ── Sticky top bar ── */}
      <header className="sticky top-0 z-50 bg-gray-900/95 backdrop-blur border-b border-gray-800 shrink-0">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-12 flex items-center gap-4">

          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 shrink-0 group">
            <div className="w-6 h-6 bg-sky-600 rounded-md flex items-center justify-center group-hover:bg-sky-500 transition-colors">
              <Zap size={13} className="text-white" />
            </div>
            <span className="font-bold text-white text-sm tracking-tight">NewsForge</span>
          </Link>

          <div className="w-px h-4 bg-gray-800 shrink-0" />

          {/* Live stats */}
          <div className="flex items-center gap-4 flex-1">
            <StatPill icon={FileText}  value={stats?.total_reports}   label="отчётов"    color="text-sky-400" />
            <StatPill icon={Lightbulb} value={stats?.total_angles}    label="углов"      color="text-violet-400" />
            <StatPill icon={Type}      value={stats?.total_headlines} label="заголовков" color="text-emerald-400" />
            <StatPill icon={ThumbsUp}  value={stats?.liked_angles}    label="лайков"     color="text-amber-400" />
          </div>

          {/* Model badge */}
          <span className="text-[10px] text-gray-700 hidden lg:block font-mono shrink-0">
            Haiku 4.5 · Sonnet 4.6
          </span>

          {/* Settings link */}
          <Link
            to="/settings"
            className={`p-1.5 rounded-lg transition-colors ${
              onSettings
                ? "bg-gray-700 text-white"
                : "text-gray-600 hover:text-gray-300 hover:bg-gray-800"
            }`}
            title="Настройки"
          >
            <Settings size={15} />
          </Link>
        </div>
      </header>

      {/* ── Content ── */}
      <main className="flex-1 overflow-auto">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

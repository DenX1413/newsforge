import { FileText, Lightbulb, Type, ThumbsUp } from "lucide-react";
import { useStats } from "../hooks/useApi.js";

const Stat = ({ icon: Icon, label, value, color }) => (
  <div className="card flex items-center gap-4">
    <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${color}`}>
      <Icon size={18} className="text-white" />
    </div>
    <div>
      <p className="text-2xl font-bold text-white">{value ?? "—"}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  </div>
);

export default function StatsBar() {
  const stats = useStats();
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <Stat icon={FileText}  label="Отчётов"     value={stats?.total_reports}   color="bg-sky-600" />
      <Stat icon={Lightbulb} label="Углов"        value={stats?.total_angles}    color="bg-violet-600" />
      <Stat icon={Type}      label="Заголовков"   value={stats?.total_headlines} color="bg-emerald-600" />
      <Stat icon={ThumbsUp}  label="Лайков"       value={stats?.liked_angles}    color="bg-amber-500" />
    </div>
  );
}

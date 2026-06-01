import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  Clock, Newspaper, Lightbulb, Type, ChevronRight, Star,
  AlertCircle, Loader2, Trash2, Pencil, Check, X,
} from "lucide-react";
import { deleteReport, toggleFavorite, updateReportTitle } from "../hooks/useApi.js";
import { useLang } from "../hooks/useLang.js";

const STATUS_CLS = {
  done:    "bg-emerald-500/15 text-emerald-400",
  running: "bg-sky-500/15 text-sky-400",
  error:   "bg-red-500/15 text-red-400",
  pending: "bg-gray-500/15 text-gray-400",
};

const GEO_CC = { RU: "ru", UA: "ua", BY: "by", KZ: "kz", DE: "de", PL: "pl", IN: "in", BR: "br", MX: "mx" };

export function GeoFlag({ geo, size = 20 }) {
  const cc = GEO_CC[geo];
  if (!cc) return null;
  return (
    <img
      src={`https://flagcdn.com/w20/${cc}.png`}
      srcSet={`https://flagcdn.com/w40/${cc}.png 2x`}
      width={size}
      height={Math.round(size * 0.75)}
      alt={geo}
      className="rounded-sm inline-block shrink-0 object-cover"
    />
  );
}

const GEO_COLOR = {
  RU: "bg-red-500/15 text-red-400 border-red-500/25",
  UA: "bg-yellow-500/15 text-yellow-400 border-yellow-500/25",
  BY: "bg-green-500/15 text-green-400 border-green-500/25",
  KZ: "bg-blue-500/15 text-blue-400 border-blue-500/25",
  DE: "bg-purple-500/15 text-purple-400 border-purple-500/25",
  PL: "bg-orange-500/15 text-orange-400 border-orange-500/25",
};

function fmt(iso) {
  const d    = new Date(iso);
  const diff = Date.now() - d;
  if (diff < 60_000)     return "только что";
  if (diff < 3_600_000)  return `${Math.floor(diff / 60_000)} мин. назад`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)} ч. назад`;
  return d.toLocaleDateString("ru-RU", { day: "numeric", month: "short" });
}

/* ── Inline title editor ───────────────────────────────────────────── */
function TitleEditor({ reportId, initialTitle, onSaved }) {
  const [editing,  setEditing]  = useState(false);
  const [value,    setValue]    = useState(initialTitle);
  const [saving,   setSaving]   = useState(false);
  const inputRef = useRef(null);

  const open = (e) => {
    e.stopPropagation();
    setEditing(true);
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  const cancel = (e) => {
    e?.stopPropagation();
    setValue(initialTitle);
    setEditing(false);
  };

  const save = async (e) => {
    e?.stopPropagation();
    const trimmed = value.trim();
    setSaving(true);
    const res = await updateReportTitle(reportId, trimmed);
    setSaving(false);
    setEditing(false);
    onSaved?.(res.title);
  };

  const onKey = (e) => {
    e.stopPropagation();
    if (e.key === "Enter")  save(e);
    if (e.key === "Escape") cancel(e);
  };

  if (editing) {
    return (
      <div className="flex items-center gap-1.5 flex-1 min-w-0" onClick={e => e.stopPropagation()}>
        <input
          ref={inputRef}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={onKey}
          onBlur={save}
          maxLength={500}
          placeholder="Название отчёта…"
          className="flex-1 min-w-0 bg-gray-800 border border-sky-500/60 rounded-md px-2 py-0.5 text-sm text-white placeholder-gray-600 focus:outline-none"
        />
        <button
          onClick={save}
          disabled={saving}
          className="p-1 rounded text-emerald-400 hover:bg-emerald-500/10 transition-colors shrink-0"
        >
          <Check size={13} />
        </button>
        <button
          onClick={cancel}
          className="p-1 rounded text-gray-500 hover:bg-sky-500/10 hover:text-sky-400 transition-colors shrink-0"
        >
          <X size={13} />
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1.5 group/title min-w-0 flex-1">
      <span className={`text-sm font-medium truncate ${value ? "text-white" : "text-gray-600 italic"}`}>
        {value || "Без названия"}
      </span>
      <button
        onClick={open}
        className="p-1 rounded text-gray-700 hover:text-gray-400 opacity-0 group-hover/title:opacity-100 transition-all shrink-0"
        title="Переименовать"
      >
        <Pencil size={11} />
      </button>
    </div>
  );
}

/* ── Card ──────────────────────────────────────────────────────────── */
export default function ReportCard({ report, onDelete, onFavoriteToggle }) {
  const navigate = useNavigate();
  const { t } = useLang();
  const clickable = report.status === "done";
  const stCls = STATUS_CLS[report.status] ?? STATUS_CLS.pending;
  const stLabel = t(`status_${report.status}`) ?? report.status;

  const [confirm,    setConfirm]    = useState(false);
  const [deleting,   setDeleting]   = useState(false);
  const [favorite,   setFavorite]   = useState(!!report.is_favorite);
  const [favLoading, setFavLoading] = useState(false);

  const handleDelete = async (e) => {
    e.stopPropagation();
    setDeleting(true);
    await deleteReport(report.id);
    onDelete?.();
  };

  const handleFavorite = async (e) => {
    e.stopPropagation();
    setFavLoading(true);
    const res = await toggleFavorite(report.id);
    setFavorite(res.is_favorite);
    setFavLoading(false);
    onFavoriteToggle?.();
  };

  return (
    <div
      onClick={() => { if (clickable && !confirm) navigate(`/report/${report.id}`); }}
      className={`card flex flex-col gap-2 py-3 transition-all ${
        clickable && !confirm ? "cursor-pointer hover:border-sky-500/50 hover:bg-sky-500/5" : "opacity-90"
      }`}
    >
      {/* ── Top row ── */}
      <div className="flex items-center gap-3">
        {/* GEO badge */}
        <div className={`w-11 h-11 rounded-xl flex flex-col items-center justify-center border shrink-0 gap-0.5 ${GEO_COLOR[report.geo] ?? "bg-gray-700 text-gray-300 border-gray-600"}`}>
          <GeoFlag geo={report.geo} size={20} />
          <span className="text-[10px] font-bold leading-none">{report.geo}</span>
        </div>

        {/* Title + meta */}
        <div className="flex-1 min-w-0">
          {/* Editable title */}
          <TitleEditor
            reportId={report.id}
            initialTitle={report.title || ""}
            onSaved={() => {}}
          />

          {/* Status / time / teamlead */}
          <div className="flex items-center gap-2 mt-0.5">
            <span className={`badge text-[11px] py-0.5 ${stCls}`}>
              {report.status === "running" && <Loader2 size={10} className="animate-spin" />}
              {report.status === "error"   && <AlertCircle size={10} />}
              {stLabel}
            </span>
            <span className="text-xs text-gray-600 flex items-center gap-1">
              <Clock size={10} /> {fmt(report.created_at)}
            </span>
            {report.team_lead && (
              <span className="text-xs text-gray-700 flex items-center gap-1 hidden sm:flex">
                <Star size={10} /> {report.team_lead}
              </span>
            )}
          </div>
        </div>

        {/* Action buttons — обёртка блокирует всплытие к карточке */}
        <div className="flex items-center gap-0.5 shrink-0" onClick={e => e.stopPropagation()}>

          {/* Favourite */}
          <button
            onClick={handleFavorite}
            disabled={favLoading}
            className={`p-2 rounded-lg transition-all ${
              favorite
                ? "text-amber-400 bg-amber-500/10 hover:bg-amber-500/20"
                : "text-gray-500 hover:text-amber-400 hover:bg-amber-500/10"
            }`}
            title={favorite ? "Убрать из избранного" : "В избранное"}
          >
            <Star size={15} fill={favorite ? "currentColor" : "none"} />
          </button>

          {/* Delete / confirm */}
          {!confirm ? (
            <button
              onClick={() => setConfirm(true)}
              className="p-2 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
              title="Удалить отчёт"
            >
              <Trash2 size={15} />
            </button>
          ) : (
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-gray-400">Удалить?</span>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="text-xs px-2 py-1 rounded-md bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors font-medium"
              >
                {deleting ? "…" : "Да"}
              </button>
              <button
                onClick={() => setConfirm(false)}
                className="text-xs px-2 py-1 rounded-md bg-gray-800 text-gray-400 hover:bg-sky-500/15 hover:text-sky-400 transition-colors"
              >
                Нет
              </button>
            </div>
          )}

        </div>{/* /action buttons */}

        {/* Arrow */}
        {clickable && !confirm && <ChevronRight size={15} className="text-gray-700 shrink-0" />}
      </div>

      {/* ── Stats row ── */}
      <div className="flex gap-3 text-xs text-gray-500 pl-14">
        <span className="flex items-center gap-1" title="Новостей">
          <Newspaper size={11} className="text-gray-700" /> {report.total_news ?? 0}
        </span>
        <span className="flex items-center gap-1" title="Углов">
          <Lightbulb size={11} className="text-gray-700" /> {report.total_angles ?? 0}
        </span>
        <span className="flex items-center gap-1" title="Заголовков">
          <Type size={11} className="text-gray-700" /> {report.total_headlines ?? 0}
        </span>
      </div>
    </div>
  );
}

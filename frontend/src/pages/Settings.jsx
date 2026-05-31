import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Settings, Bell, Globe, Eye, EyeOff, CheckCircle,
  XCircle, Send, Save, RotateCw, AlertCircle, Link,
  FileText, ChevronDown, ChevronRight, ExternalLink, ArrowLeft,
  Sun, Moon, Monitor,
} from "lucide-react";
import { useSettings, saveSettings, testNotify } from "../hooks/useApi.js";
import { GeoFlag } from "../components/ReportCard.jsx";
import { useTheme } from "../hooks/useTheme.js";

const GEOS_ALL = ["RU", "UA", "BY", "KZ", "DE", "PL"];

function Section({ title, icon: Icon, children, badge }) {
  return (
    <div className="card space-y-4">
      <h2 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
        <Icon size={15} className="text-sky-400" /> {title}
        {badge && (
          <span className="ml-auto text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">
            {badge}
          </span>
        )}
      </h2>
      {children}
    </div>
  );
}

function Field({ label, hint, children }) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-medium text-gray-400">{label}</label>
      {children}
      {hint && <p className="text-[11px] text-gray-600">{hint}</p>}
    </div>
  );
}

function TokenInput({ value, onChange, placeholder, configured }) {
  const [show, setShow] = useState(false);
  return (
    <div className="relative">
      <input
        type={show ? "text" : "password"}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={configured ? "••••••••••••••••••• (уже задан)" : placeholder}
        className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-sky-500 transition-colors pr-10"
      />
      <button
        type="button"
        onClick={() => setShow(v => !v)}
        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-400"
      >
        {show ? <EyeOff size={14} /> : <Eye size={14} />}
      </button>
    </div>
  );
}

function StatusDot({ ok, label }) {
  return (
    <span className={`inline-flex items-center gap-1 text-xs ${ok ? "text-emerald-400" : "text-gray-600"}`}>
      {ok ? <CheckCircle size={12} /> : <XCircle size={12} />}
      {label}
    </span>
  );
}

function TestResult({ result, channel }) {
  if (!result) return null;
  const ok = result[channel];
  return (
    <div className={`text-xs px-3 py-2 rounded-lg flex items-center gap-2 ${
      ok ? "bg-emerald-950/40 text-emerald-400" : "bg-red-950/40 text-red-400"
    }`}>
      {ok
        ? <><CheckCircle size={12} /> Отправлено успешно!</>
        : <><XCircle size={12} /> Ошибка — проверь токен и ID</>}
    </div>
  );
}

function GuideStep({ num, children }) {
  return (
    <div className="flex gap-2.5 text-[11px] text-gray-500">
      <span className="shrink-0 w-4 h-4 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center text-[10px] font-bold text-gray-400">
        {num}
      </span>
      <span className="leading-relaxed">{children}</span>
    </div>
  );
}

function Collapsible({ label, children }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-gray-800 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(v => !v)}
        className="w-full flex items-center justify-between px-3 py-2 text-xs text-gray-500 hover:text-gray-400 hover:bg-gray-800/50 transition-colors"
      >
        <span>{label}</span>
        {open ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
      </button>
      {open && (
        <div className="px-3 pb-3 space-y-2.5 border-t border-gray-800 pt-2.5">
          {children}
        </div>
      )}
    </div>
  );
}

export default function SettingsPage() {
  const navigate = useNavigate();
  const { settings, loading, refetch } = useSettings();
  const { theme, setTheme } = useTheme();

  const [form, setForm] = useState({
    telegram_bot_token:          "",
    telegram_chat_id:            "",
    slack_bot_token:             "",
    slack_channel_id:            "",
    news_coverage_days:          7,
    default_geos:                "RU,UA,BY",
    app_url:                     "http://localhost:5173",
    google_credentials_json:     "",
    google_drive_folder_id:      "",
    google_oauth_client_id:      "",
    google_oauth_client_secret:  "",
    google_oauth_refresh_token:  "",
    telegram_channels_ru:        "",
    telegram_channels_ua:        "",
    telegram_channels_by:        "",
  });
  const [selectedGeos, setSelectedGeos] = useState(new Set(["RU", "UA", "BY"]));

  const [saving,     setSaving]     = useState(false);
  const [saved,      setSaved]      = useState(false);
  const [testing,    setTesting]    = useState(null);  // "telegram" | "slack" | null
  const [testResult, setTestResult] = useState(null);
  const [saveError,  setSaveError]  = useState(null);

  useEffect(() => {
    if (!settings) return;
    setForm(f => ({
      ...f,
      telegram_chat_id:            settings.telegram_chat_id            ?? "",
      slack_channel_id:            settings.slack_channel_id            ?? "",
      news_coverage_days:          settings.news_coverage_days           ?? 7,
      default_geos:                settings.default_geos                 ?? "RU,UA,BY",
      app_url:                     settings.app_url                      ?? "http://localhost:5173",
      google_credentials_json:     "",  // never pre-fill — secret
      google_drive_folder_id:      settings.google_drive_folder_id ?? "",
      google_oauth_client_id:      "",  // never pre-fill — secret
      google_oauth_client_secret:  "",  // never pre-fill — secret
      google_oauth_refresh_token:  "",  // never pre-fill — secret
    }));
    const geos = (settings.default_geos ?? "RU,UA,BY").split(",").map(g => g.trim());
    setSelectedGeos(new Set(geos));
  }, [settings]);

  const set = (key, val) => setForm(f => ({ ...f, [key]: val }));

  const toggleGeo = (g) => {
    setSelectedGeos(prev => {
      const next = new Set(prev);
      if (next.has(g) && next.size > 1) next.delete(g);
      else next.add(g);
      return next;
    });
  };

  const handleSave = async () => {
    setSaving(true); setSaved(false); setSaveError(null);
    try {
      const payload = { ...form };
      payload.default_geos = [...selectedGeos].join(",");
      if (!payload.telegram_bot_token)    delete payload.telegram_bot_token;
      if (!payload.slack_bot_token)       delete payload.slack_bot_token;
      if (!payload.google_credentials_json?.trim())   delete payload.google_credentials_json;
      if (!payload.google_drive_folder_id?.trim())    delete payload.google_drive_folder_id;
      if (!payload.google_oauth_client_id?.trim())    delete payload.google_oauth_client_id;
      if (!payload.google_oauth_client_secret?.trim()) delete payload.google_oauth_client_secret;
      if (!payload.google_oauth_refresh_token?.trim()) delete payload.google_oauth_refresh_token;
      if (!payload.telegram_channels_ru?.trim())    delete payload.telegram_channels_ru;
      if (!payload.telegram_channels_ua?.trim())    delete payload.telegram_channels_ua;
      if (!payload.telegram_channels_by?.trim())    delete payload.telegram_channels_by;
      await saveSettings(payload);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
      refetch();
    } catch (e) {
      setSaveError("Ошибка сохранения: " + e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async (channel) => {
    setTesting(channel); setTestResult(null);
    const res = await testNotify();
    setTestResult(res);
    setTesting(null);
  };

  if (loading) return (
    <div className="space-y-4 max-w-2xl mx-auto">
      {[1, 2, 3].map(i => <div key={i} className="card animate-pulse h-32 bg-gray-800/50" />)}
    </div>
  );

  return (
    <div className="space-y-5 max-w-2xl mx-auto">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate(-1)}
          className="p-1.5 rounded-lg text-gray-500 hover:text-white hover:bg-gray-800 transition-colors"
        >
          <ArrowLeft size={18} />
        </button>
        <h1 className="text-lg font-bold text-white flex items-center gap-2">
          <Settings size={18} className="text-gray-400" /> Настройки
        </h1>
        <p className="text-sm text-gray-600 mt-1">
          Уведомления, источники и параметры пайплайна
        </p>
      </div>

      {/* ── Telegram ── */}
      <Section title="Telegram уведомления" icon={Bell}
               badge={settings?.telegram_configured ? "подключён" : undefined}>
        <div className="flex items-center justify-between">
          <div className="flex gap-3">
            <StatusDot ok={settings?.telegram_configured} label="Bot Token" />
            <StatusDot ok={!!form.telegram_chat_id || !!settings?.telegram_chat_id} label="Chat ID" />
          </div>
          <button
            onClick={() => handleTest("telegram")}
            disabled={!!testing || !settings?.telegram_configured}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 disabled:opacity-40 transition-colors"
          >
            {testing === "telegram"
              ? <RotateCw size={12} className="animate-spin" />
              : <Send size={12} />}
            Тест
          </button>
        </div>

        <TestResult result={testResult} channel="telegram" />

        <Collapsible label="📋 Как подключить Telegram — пошаговая инструкция">
          <GuideStep num="1">
            Открой Telegram и найди бота{" "}
            <b className="text-gray-400">@BotFather</b> → напиши{" "}
            <code className="text-amber-400 bg-gray-900 px-1 rounded">/newbot</code>
          </GuideStep>
          <GuideStep num="2">
            Придумай имя бота (например, <b className="text-gray-400">NewsForge Notify</b>) и
            username (например, <b className="text-gray-400">newsforge_notify_bot</b>)
          </GuideStep>
          <GuideStep num="3">
            BotFather пришлёт <b className="text-gray-400">Bot Token</b> вида{" "}
            <code className="text-amber-400 bg-gray-900 px-1 rounded text-[10px]">1234567890:ABCdefGhi...</code>
            → вставь его в поле ниже
          </GuideStep>
          <GuideStep num="4">
            Напиши своему боту{" "}
            <code className="text-amber-400 bg-gray-900 px-1 rounded">/start</code>
            {" "}— это активирует чат
          </GuideStep>
          <GuideStep num="5">
            Узнай свой Chat ID: напиши боту{" "}
            <a href="https://t.me/userinfobot" target="_blank" rel="noreferrer"
               className="text-sky-400 underline inline-flex items-center gap-0.5">
              @userinfobot <ExternalLink size={10} />
            </a>
            {" "}— он пришлёт твой ID → вставь в поле Chat ID
          </GuideStep>
          <GuideStep num="6">
            Нажми <b className="text-gray-400">Сохранить</b> → затем <b className="text-gray-400">Тест</b> —
            бот пришлёт тестовое сообщение
          </GuideStep>
        </Collapsible>

        <Field label="Bot Token"
               hint="Получи у @BotFather → /newbot. Оставь пустым, чтобы не менять.">
          <TokenInput
            value={form.telegram_bot_token}
            onChange={v => set("telegram_bot_token", v)}
            placeholder="1234567890:ABCdefGhi..."
            configured={settings?.telegram_configured}
          />
        </Field>

        <Field label="Chat ID"
               hint="ID чата или пользователя. Напиши боту /start — получи ID через @userinfobot.">
          <input
            type="text"
            value={form.telegram_chat_id}
            onChange={e => set("telegram_chat_id", e.target.value)}
            placeholder="486069801"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-sky-500 transition-colors"
          />
        </Field>
      </Section>

      {/* ── Slack ── */}
      <Section title="Slack уведомления" icon={Bell}
               badge={settings?.slack_configured ? "подключён" : undefined}>
        <div className="flex items-center justify-between">
          <div className="flex gap-3">
            <StatusDot ok={settings?.slack_configured} label="Bot Token" />
            <StatusDot ok={!!form.slack_channel_id || !!settings?.slack_channel_id} label="Channel" />
          </div>
          <button
            onClick={() => handleTest("slack")}
            disabled={!!testing || !settings?.slack_configured}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 disabled:opacity-40 transition-colors"
          >
            {testing === "slack"
              ? <RotateCw size={12} className="animate-spin" />
              : <Send size={12} />}
            Тест
          </button>
        </div>

        <TestResult result={testResult} channel="slack" />

        <Collapsible label="📋 Как подключить Slack — пошаговая инструкция">
          <GuideStep num="1">
            Перейди на{" "}
            <a href="https://api.slack.com/apps" target="_blank" rel="noreferrer"
               className="text-sky-400 underline inline-flex items-center gap-0.5">
              api.slack.com/apps <ExternalLink size={10} />
            </a>
            {" "}→ <b className="text-gray-400">Create New App</b> → <b className="text-gray-400">From scratch</b>
          </GuideStep>
          <GuideStep num="2">
            Введи название (<b className="text-gray-400">NewsForge</b>) и выбери свой Workspace
          </GuideStep>
          <GuideStep num="3">
            В меню: <b className="text-gray-400">OAuth & Permissions</b> →
            раздел <b className="text-gray-400">Bot Token Scopes</b> →
            добавь <code className="text-amber-400 bg-gray-900 px-1 rounded">chat:write</code>
          </GuideStep>
          <GuideStep num="4">
            Наверху страницы → <b className="text-gray-400">Install to Workspace</b> → <b className="text-gray-400">Allow</b>
          </GuideStep>
          <GuideStep num="5">
            Скопируй <b className="text-gray-400">Bot User OAuth Token</b>{" "}
            (начинается с <code className="text-amber-400 bg-gray-900 px-1 rounded">xoxb-</code>) → вставь ниже
          </GuideStep>
          <GuideStep num="6">
            В нужном канале Slack напиши:{" "}
            <code className="text-amber-400 bg-gray-900 px-1 rounded">/invite @NewsForge</code>
            {" "}— иначе бот не сможет писать
          </GuideStep>
          <GuideStep num="7">
            Channel ID: правый клик на канал → <b className="text-gray-400">Copy link</b> →
            последняя часть URL (например, <code className="text-amber-400 bg-gray-900 px-1 rounded">C0123ABCDEF</code>)
          </GuideStep>
        </Collapsible>

        <Field label="Bot OAuth Token"
               hint="Slack App → OAuth & Permissions → Bot User OAuth Token. Оставь пустым, чтобы не менять.">
          <TokenInput
            value={form.slack_bot_token}
            onChange={v => set("slack_bot_token", v)}
            placeholder="xoxb-..."
            configured={settings?.slack_configured}
          />
        </Field>

        <Field label="Channel ID"
               hint="Правой кнопкой на канал → Copy link → последняя часть URL.">
          <input
            type="text"
            value={form.slack_channel_id}
            onChange={e => set("slack_channel_id", e.target.value)}
            placeholder="C0123ABCDEF"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-sky-500 transition-colors"
          />
        </Field>
      </Section>

      {/* ── Telegram каналы ── */}
      <Section title="Telegram-каналы (источник новостей)" icon={Bell} badge="активен">
        <p className="text-xs text-gray-500">
          Автоматически читает публичные Telegram-каналы через RSS — без ключей и авторизации.
          Укажи каналы для нужных GEO или оставь пустым для дефолтных.
        </p>
        <div className="text-xs text-emerald-400 flex items-center gap-1.5">
          <CheckCircle size={12} /> Работает без настройки — каналы по умолчанию уже заданы
        </div>
        <div className="space-y-2">
          <p className="text-xs font-medium text-gray-400">
            Каналы по GEO{" "}
            <span className="text-gray-600 font-normal">(через запятую, без @)</span>
          </p>
          {[
            ["RU", "telegram_channels_ru", "rian_ru, tass_agency, rbc_news, mash, readovkaru"],
            ["UA", "telegram_channels_ua", "ukrpravda_news, suspilne_ua, unian_news"],
            ["BY", "telegram_channels_by", "nexta_tv, zerkalo_io"],
          ].map(([geo, key, ph]) => (
            <div key={geo} className="flex items-center gap-2">
              <span className="text-xs font-bold text-gray-400 w-8 shrink-0">{geo}</span>
              <input type="text" value={form[key]}
                onChange={e => set(key, e.target.value)}
                placeholder={`По умолчанию: ${ph}`}
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-sky-500 transition-colors" />
            </div>
          ))}
        </div>
      </Section>

      {/* ── Google Docs ── */}
      <Section title="Google Docs экспорт" icon={FileText}
               badge={
                 settings?.gdocs_oauth_configured && settings?.gdocs_folder_configured ? "OAuth ✓" :
                 settings?.gdocs_configured && settings?.gdocs_folder_configured ? "SA ✓" :
                 settings?.gdocs_configured || settings?.gdocs_oauth_configured ? "ключ есть" : undefined
               }>

        {/* Auth mode status */}
        <div className="flex flex-col gap-2">
          <div className="flex gap-4 flex-wrap">
            <StatusDot ok={settings?.gdocs_oauth_configured} label="OAuth (личный аккаунт)" />
            <StatusDot ok={settings?.gdocs_configured}       label="Service Account" />
            <StatusDot ok={settings?.gdocs_folder_configured} label="Drive папка" />
          </div>
          {settings?.gdocs_oauth_configured && settings?.gdocs_folder_configured && (
            <p className="text-xs text-emerald-400">
              ✓ OAuth подключён — документы создаются от имени вашего аккаунта
            </p>
          )}
          {!settings?.gdocs_oauth_configured && settings?.gdocs_configured && settings?.gdocs_folder_configured && (
            <div className="text-xs text-amber-400 bg-amber-950/20 border border-amber-800/30 rounded-lg px-3 py-2">
              ⚠ Service Account не может создавать файлы в личном Drive (квота = 0 байт).
              Добавь OAuth токен ниже для полноценной работы.
            </div>
          )}
        </div>

        {/* SA email */}
        {settings?.gdocs_configured && settings?.sa_email && (
          <div className="bg-gray-800/60 border border-gray-700 rounded-lg px-3 py-2.5 space-y-1">
            <p className="text-[11px] text-gray-500">Email сервисного аккаунта (добавь как Editor в папку Drive):</p>
            <p className="text-xs font-mono text-amber-300 select-all break-all">{settings.sa_email}</p>
          </div>
        )}

        {/* ── OAuth section (recommended for personal Gmail) ── */}
        <Collapsible label="🔑 OAuth2 (рекомендуется для личного Gmail) — пошаговая инструкция">
          <div className="text-[11px] text-amber-400/80 bg-amber-950/20 border border-amber-800/30 rounded px-2 py-1.5 mb-1">
            Используй OAuth если у тебя личный Gmail-аккаунт. Service Account не имеет своего Drive-пространства.
          </div>
          <GuideStep num="1">
            <a href="https://console.cloud.google.com/apis/credentials" target="_blank" rel="noreferrer"
               className="text-sky-400 underline inline-flex items-center gap-0.5">
              GCP Console → Credentials <ExternalLink size={10} />
            </a>
            {" "}→ <b className="text-gray-400">Create Credentials → OAuth 2.0 Client ID</b>
          </GuideStep>
          <GuideStep num="2">
            Тип: <b className="text-gray-400">Desktop App</b> → скопируй{" "}
            <b className="text-gray-400">Client ID</b> и <b className="text-gray-400">Client Secret</b>
          </GuideStep>
          <GuideStep num="3">
            Убедись что добавлены scopes:{" "}
            <code className="text-amber-400 bg-gray-900 px-1 rounded text-[10px]">drive</code>{" "}и{" "}
            <code className="text-amber-400 bg-gray-900 px-1 rounded text-[10px]">documents</code>
          </GuideStep>
          <GuideStep num="4">
            Запусти скрипт авторизации:{" "}
            <code className="text-amber-400 bg-gray-900 px-1 rounded text-[10px]">python setup_google_oauth.py</code>
            {" "}— он откроет браузер и вернёт refresh_token
          </GuideStep>
          <GuideStep num="5">
            Вставь Client ID, Client Secret и Refresh Token в поля ниже → Сохранить
          </GuideStep>
        </Collapsible>

        <Field label="OAuth Client ID"
               hint={settings?.gdocs_oauth_configured ? "OAuth уже настроен. Оставь пустым чтобы не менять." : "Из GCP Console → Credentials → OAuth 2.0 Client ID"}>
          <TokenInput
            value={form.google_oauth_client_id}
            onChange={v => set("google_oauth_client_id", v)}
            placeholder="123456789-abc.apps.googleusercontent.com"
            configured={settings?.gdocs_oauth_configured}
          />
        </Field>

        <Field label="OAuth Client Secret"
               hint="Из GCP Console → OAuth 2.0 Client ID → Client Secret">
          <TokenInput
            value={form.google_oauth_client_secret}
            onChange={v => set("google_oauth_client_secret", v)}
            placeholder="GOCSPX-..."
            configured={settings?.gdocs_oauth_configured}
          />
        </Field>

        <Field label="OAuth Refresh Token"
               hint="Получи запустив: python setup_google_oauth.py">
          <TokenInput
            value={form.google_oauth_refresh_token}
            onChange={v => set("google_oauth_refresh_token", v)}
            placeholder="1//0gXx..."
            configured={settings?.gdocs_oauth_configured}
          />
        </Field>

        {/* ── Service Account (legacy / alternative) ── */}
        <Collapsible label="⚙ Service Account (альтернатива / Google Workspace)">
          <div className="space-y-3">
            <GuideStep num="1">
              <a href="https://console.cloud.google.com/" target="_blank" rel="noreferrer"
                 className="text-sky-400 underline inline-flex items-center gap-0.5">
                Google Cloud Console <ExternalLink size={10} />
              </a>
              {" "}→ включи <b className="text-gray-400">Google Docs API</b> и <b className="text-gray-400">Google Drive API</b>
            </GuideStep>
            <GuideStep num="2">
              <b className="text-gray-400">Credentials → Create Credentials → Service Account</b> →
              скачай JSON-ключ → вставь содержимое ниже
            </GuideStep>
            <GuideStep num="3">
              Поделись папкой Drive с email сервисного аккаунта (роль Editor)
            </GuideStep>

            <Field label="Service Account JSON"
                   hint={settings?.gdocs_configured ? "Ключ уже настроен. Вставь новый JSON только если хочешь заменить." : "Открой скачанный JSON-файл, выдели всё (Ctrl+A) и вставь сюда."}>
              <textarea
                rows={3}
                value={form.google_credentials_json}
                onChange={e => set("google_credentials_json", e.target.value)}
                placeholder={settings?.gdocs_configured
                  ? '{ "type": "service_account", ... }  ← уже настроен, оставь пустым'
                  : '{ "type": "service_account", "project_id": "...", "private_key": "-----BEGIN RSA...", ... }'}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-sky-500 transition-colors font-mono resize-none"
              />
            </Field>
          </div>
        </Collapsible>

        <Field label="ID папки в Google Drive"
               hint="Последняя часть URL открытой папки: drive.google.com/drive/folders/ВОТ_ЭТО">
          <input
            type="text"
            value={form.google_drive_folder_id}
            onChange={e => set("google_drive_folder_id", e.target.value)}
            placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-sky-500 transition-colors font-mono text-xs"
          />
        </Field>
      </Section>

      {/* ── Pipeline ── */}
      <Section title="Параметры пайплайна" icon={Globe}>
        <Field label="URL приложения"
               hint="Используется в ссылках Telegram/Slack уведомлений. При деплое замени на реальный домен.">
          <div className="relative">
            <Link size={12} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-600" />
            <input
              type="text"
              value={form.app_url}
              onChange={e => set("app_url", e.target.value)}
              placeholder="http://localhost:5173"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-8 pr-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-sky-500 transition-colors"
            />
          </div>
        </Field>

        <Field label="Период покрытия новостей"
               hint="Статьи старше этого срока игнорируются. Рекомендовано: 5–7 дней.">
          <div className="space-y-3">
            {/* Presets */}
            <div className="grid grid-cols-5 gap-1.5">
              {[
                { days: 1,  label: "1 д",   hint: "Сегодня"   },
                { days: 3,  label: "3 дня",  hint: "Трендово"  },
                { days: 7,  label: "7 дней", hint: "Рекомендуем", rec: true },
                { days: 14, label: "2 нед",  hint: "Широко"    },
                { days: 30, label: "30 дней",hint: "Архивно"   },
              ].map(({ days, label, hint, rec }) => (
                <button
                  key={days}
                  type="button"
                  onClick={() => set("news_coverage_days", days)}
                  className={`relative flex flex-col items-center gap-0.5 px-2 py-2.5 rounded-lg border text-xs font-medium transition-all ${
                    form.news_coverage_days === days
                      ? "border-sky-500 bg-sky-500/15 text-sky-300"
                      : "border-gray-700 text-gray-500 hover:border-gray-600 hover:text-gray-400"
                  }`}
                >
                  {rec && (
                    <span className="absolute -top-1.5 left-1/2 -translate-x-1/2 text-[9px] bg-sky-500 text-white px-1 rounded-full leading-tight">
                      ★
                    </span>
                  )}
                  <span className={`text-sm font-bold tabular-nums ${form.news_coverage_days === days ? "text-sky-300" : "text-gray-400"}`}>
                    {days}
                  </span>
                  <span className="text-[10px] text-gray-600 font-normal">{hint}</span>
                </button>
              ))}
            </div>
            {/* Custom slider for non-preset values */}
            <div className="flex items-center gap-3">
              <input
                type="range"
                min={1} max={30} step={1}
                value={form.news_coverage_days}
                onChange={e => set("news_coverage_days", Number(e.target.value))}
                className="flex-1 slider"
                style={{ "--val": form.news_coverage_days }}
              />
              <span className="text-sm font-bold text-white w-16 text-right tabular-nums shrink-0">
                {form.news_coverage_days} {form.news_coverage_days === 1 ? "день" : form.news_coverage_days < 5 ? "дня" : "дней"}
              </span>
            </div>
          </div>
        </Field>

        <Field label="GEO по умолчанию"
               hint="Используются для автозапуска по расписанию.">
          <div className="flex gap-2 flex-wrap">
            {GEOS_ALL.map(g => (
              <button
                key={g}
                onClick={() => toggleGeo(g)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all flex items-center gap-1.5 ${
                  selectedGeos.has(g)
                    ? "border-sky-500/60 bg-sky-500/15 text-sky-300"
                    : "border-gray-700 text-gray-600 hover:border-gray-600 hover:text-gray-400"
                }`}
              >
                <GeoFlag geo={g} size={16} />{g}
              </button>
            ))}
          </div>
        </Field>
      </Section>

      {/* ── Anthropic status ── */}
      <div className="card flex items-center gap-3 py-3">
        <StatusDot ok={settings?.anthropic_configured} label="Anthropic API Key" />
        {!settings?.anthropic_configured && (
          <span className="text-xs text-amber-400 flex items-center gap-1">
            <AlertCircle size={12} /> Добавь ANTHROPIC_API_KEY в .env
          </span>
        )}
        {settings?.anthropic_configured && (
          <span className="text-xs text-gray-600">Ключ задан в .env — не меняется через UI</span>
        )}
      </div>

      {/* ── Тема ── */}
      <div className="card space-y-3">
        <h2 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
          <Sun size={15} className="text-amber-400" /> Тема оформления
        </h2>
        <div className="grid grid-cols-3 gap-2">
          {[
            { value: "system", icon: Monitor, label: "Системная", hint: "Как в ОС" },
            { value: "light",  icon: Sun,     label: "Светлая",   hint: "Молочная" },
            { value: "dark",   icon: Moon,    label: "Тёмная",    hint: "По умолчанию" },
          ].map(({ value, icon: Icon, label, hint }) => (
            <button
              key={value}
              type="button"
              onClick={() => setTheme(value)}
              className={`flex flex-col items-center gap-1.5 py-3 px-2 rounded-xl border text-xs font-medium transition-all ${
                theme === value
                  ? "border-sky-500 bg-sky-500/15 text-sky-300"
                  : "border-gray-700 text-gray-500 hover:border-gray-600 hover:text-gray-400"
              }`}
            >
              <Icon size={18} className={theme === value ? "text-sky-400" : "text-gray-500"} />
              <span className="font-semibold">{label}</span>
              <span className="text-[10px] font-normal text-gray-600">{hint}</span>
            </button>
          ))}
        </div>
      </div>

      {/* ── Save button ── */}
      {saveError && (
        <p className="text-xs text-red-400 bg-red-950/40 px-3 py-2 rounded-lg border border-red-900/30">
          ⚠ {saveError}
        </p>
      )}

      <button
        onClick={handleSave}
        disabled={saving}
        className={`btn-primary w-full flex items-center justify-center gap-2 py-2.5 ${
          saved ? "bg-emerald-600 hover:bg-emerald-600" : ""
        }`}
      >
        {saving  ? <><RotateCw size={14} className="animate-spin" /> Сохранение…</> :
         saved   ? <><CheckCircle size={14} /> Сохранено</> :
                   <><Save size={14} /> Сохранить настройки</>}
      </button>
    </div>
  );
}

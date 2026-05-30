import { useState, useRef, useCallback } from "react";
import { triggerRun } from "./useApi.js";

export default function usePipeline(onDone) {
  const [running, setRunning]   = useState(false);
  const [progress, setProgress] = useState(null);
  const [error, setError]       = useState(null);
  const wsRef = useRef(null);

  const run = useCallback(async (geo, useMock = false, teamLead = "") => {
    setError(null);
    setRunning(true);
    setProgress({ step: "start", pct: 0, message: "Инициализация…" });

    try {
      const { report_id, client_id } = await triggerRun(geo, useMock, teamLead);

      // Poll for completion every 5 seconds (WS optional for live progress)
      const poll = setInterval(async () => {
        try {
          const r = await fetch(`/api/reports/${report_id}`);
          const data = await r.json();
          if (data.status === "done") {
            clearInterval(poll);
            setProgress({ step: "done", pct: 100, message: "Готово!" });
            setRunning(false);
            onDone?.(report_id);
          } else if (data.status === "error") {
            clearInterval(poll);
            setError("Ошибка пайплайна — смотри логи бэкенда");
            setRunning(false);
          } else if (data.status === "running") {
            // Animate progress bar while running
            setProgress((prev) => {
              const pct = Math.min((prev?.pct ?? 10) + 3, 90);
              const messages = [
                "Парсинг RSS лент…",
                "Google News…",
                "Классификация (Haiku)…",
                "Генерация углов (Sonnet)…",
                "Генерация заголовков (Sonnet)…",
                "Оценка рисков (Sonnet)…",
                "Рекомендации (Sonnet)…",
                "Формирование отчёта…",
              ];
              const msg = messages[Math.floor(pct / 12)] ?? "Обработка…";
              return { step: "running", pct, message: msg };
            });
          }
        } catch (e) {
          // ignore transient errors
        }
      }, 5000);

      // Safety timeout — stop polling after 10 min
      setTimeout(() => {
        clearInterval(poll);
        if (running) {
          setError("Превышено время ожидания (10 мин)");
          setRunning(false);
        }
      }, 600000);

    } catch (e) {
      setError(e.message);
      setRunning(false);
    }
  }, [onDone]);

  return { run, running, progress, error };
}

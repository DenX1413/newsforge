import { useState, useEffect, useCallback, useRef } from "react";

const BASE = "/api";

const ACTIVE = new Set(["pending", "running"]);
const POLL_MS = 3000;

export function useReports(geo, onlyFavorite = false) {
  const [reports, setReports]   = useState([]);
  const [loading, setLoading]   = useState(true);
  const timerRef                = useRef(null);

  const fetch_ = useCallback(() => {
    const params = new URLSearchParams();
    if (geo)          params.set("geo", geo);
    if (onlyFavorite) params.set("favorite", "true");
    const url = `${BASE}/reports${params.toString() ? "?" + params.toString() : ""}`;

    fetch(url)
      .then(r => r.json())
      .then(data => {
        setReports(data);
        setLoading(false);

        const hasActive = data.some(r => ACTIVE.has(r.status));
        clearTimeout(timerRef.current);
        if (hasActive) {
          timerRef.current = setTimeout(fetch_, POLL_MS);
        }
      })
      .catch(() => { setReports([]); setLoading(false); });
  }, [geo, onlyFavorite]);

  useEffect(() => {
    setLoading(true);
    fetch_();
    return () => clearTimeout(timerRef.current);
  }, [fetch_]);

  return { reports, loading, refetch: fetch_ };
}

export function useReport(id) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const timerRef = useRef(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);

    const poll = () => {
      fetch(`${BASE}/reports/${id}`)
        .then(r => r.json())
        .then(data => {
          setReport(data);
          setLoading(false);
          clearTimeout(timerRef.current);
          if (ACTIVE.has(data.status)) {
            timerRef.current = setTimeout(poll, POLL_MS);
          }
        })
        .catch(() => setLoading(false));
    };

    poll();
    return () => clearTimeout(timerRef.current);
  }, [id]);

  return { report, loading };
}

export function useStats() {
  const [stats, setStats] = useState(null);

  const refetch = useCallback(() => {
    fetch(`${BASE}/stats`).then(r => r.json()).then(setStats).catch(() => {});
  }, []);

  useEffect(() => {
    refetch();
    window.addEventListener("nf:feedback", refetch);
    return () => window.removeEventListener("nf:feedback", refetch);
  }, [refetch]);

  return stats;
}



export function useSchedule() {
  const [schedule, setSchedule] = useState([]);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(() => {
    setLoading(true);
    fetch(`${BASE}/schedule`).then(r => r.json()).then(setSchedule)
      .catch(() => setSchedule([])).finally(() => setLoading(false));
  }, []);

  useEffect(() => { refetch(); }, [refetch]);
  return { schedule, loading, refetch };
}

export function useSettings() {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);

  const refetch = useCallback(() => {
    setLoading(true);
    fetch(`${BASE}/settings`).then(r => r.json()).then(setSettings)
      .catch(() => {}).finally(() => setLoading(false));
  }, []);

  useEffect(() => { refetch(); }, [refetch]);
  return { settings, loading, refetch };
}

export async function saveSettings(data) {
  const res = await fetch(`${BASE}/settings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function testNotify() {
  const res = await fetch(`${BASE}/settings/test-notify`, { method: "POST" });
  return res.json();
}

export async function updateSchedule(geo, data) {
  const res = await fetch(`${BASE}/schedule/${geo}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function triggerRun(geo, useMock = false, teamLead = "", vertical = "", keywords = "", outputLanguage = "") {
  const res = await fetch(`${BASE}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      geo,
      use_mock: useMock,
      team_lead: teamLead,
      vertical,
      keywords,
      output_language: outputLanguage,
    }),
  });
  return res.json();
}

export async function deleteReport(id) {
  await fetch(`${BASE}/reports/${id}`, { method: "DELETE" });
}

export async function toggleFavorite(id) {
  const res = await fetch(`${BASE}/reports/${id}/favorite`, { method: "PATCH" });
  return res.json();
}

export async function updateReportTitle(id, title) {
  const res = await fetch(`${BASE}/reports/${id}/title`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  return res.json();
}

export async function setFeedback(angleId, feedback) {
  await fetch(`${BASE}/angles/${angleId}/feedback`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ feedback }),
  });
  window.dispatchEvent(new CustomEvent("nf:feedback"));
}

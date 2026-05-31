/**
 * useTheme — управление темой приложения.
 * Значения: "system" | "dark" | "light"
 * Хранится в localStorage под ключом "nf-theme".
 *
 * Применяет класс "light" или "dark" на <html>,
 * CSS переменные подхватывают его.
 */
import { useState, useEffect } from "react";

const KEY = "nf-theme";

function applyTheme(theme) {
  const root = document.documentElement;
  if (theme === "light") {
    root.classList.add("light");
    root.classList.remove("dark");
  } else if (theme === "dark") {
    root.classList.add("dark");
    root.classList.remove("light");
  } else {
    // system — убираем оба класса, работает media query
    root.classList.remove("light", "dark");
  }
}

export function useTheme() {
  const [theme, setTheme] = useState(() => localStorage.getItem(KEY) || "system");

  useEffect(() => {
    applyTheme(theme);
    localStorage.setItem(KEY, theme);
  }, [theme]);

  return { theme, setTheme };
}

// Вызвать при старте приложения (до рендера) чтобы не мигало
export function initTheme() {
  const saved = localStorage.getItem(KEY) || "system";
  applyTheme(saved);
}

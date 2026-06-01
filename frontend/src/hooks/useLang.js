import { useState, useEffect, createContext, useContext } from "react";
import { TRANSLATIONS } from "../i18n/translations.js";

const LANG_KEY = "nf-lang";

export const LangContext = createContext(null);

export function useLang() {
  return useContext(LangContext);
}

export function useLangState() {
  const [lang, setLangState] = useState(() => localStorage.getItem(LANG_KEY) || "ru");

  const setLang = (l) => {
    setLangState(l);
    localStorage.setItem(LANG_KEY, l);
  };

  // t(key) — перевод строки
  const t = (key) => TRANSLATIONS[lang]?.[key] ?? TRANSLATIONS["ru"]?.[key] ?? key;

  return { lang, setLang, t };
}

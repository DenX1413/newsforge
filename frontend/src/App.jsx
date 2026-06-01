import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import ReportDetail from "./pages/ReportDetail.jsx";
import Settings from "./pages/Settings.jsx";
import { LangContext, useLangState } from "./hooks/useLang.js";

export default function App() {
  const langState = useLangState();
  return (
    <LangContext.Provider value={langState}>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="report/:id" element={<ReportDetail />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </LangContext.Provider>
  );
}

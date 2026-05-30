import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import ReportDetail from "./pages/ReportDetail.jsx";
import Settings from "./pages/Settings.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="report/:id" element={<ReportDetail />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}

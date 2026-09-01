import { BrowserRouter, Routes, Route } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import AnalyzeImagePage from "./pages/AnalyzeImagePage";
import AnalyzeVideoPage from "./pages/AnalyzeVideoPage";
import AppLayout from "./components/layout/AppLayout";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/analyze/image" element={<AnalyzeImagePage />} />
          <Route path="/analyze/video" element={<AnalyzeVideoPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;

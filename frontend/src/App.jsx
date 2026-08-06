import { BrowserRouter, Routes, Route } from "react-router-dom";
import Sidebar from "./components/layout/Sidebar";
import DashboardPage from "./pages/DashboardPage";
import AnalyzeImagePage from "./pages/AnalyzeImagePage";
import AnalyzeVideoPage from "./pages/AnalyzeVideoPage";

function App() {
  return (
    <BrowserRouter>
      <div style={{ display: "flex" }}>
        <Sidebar />
        <div style={{ flex: 1, padding: "24px" }}>
          <h1>safEYE 안전 관제 대시보드</h1>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/analyze/image" element={<AnalyzeImagePage />} />
            <Route path="/analyze/video" element={<AnalyzeVideoPage />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;

//<BrowserRouter>: 이 안에서는 주소(URL) 기반으로 화면이 바뀐다고 선언하는 태그
//<Routes>: <Route> 중, 지금 주소랑 맞는 것 딱 하나만 골라서 보여주는 상자
//<Route path="/analyze/image" element={<AnalyzeImagePage />} />:
// 주소가 /analyze/image이면 AnalyzeImagePage를 보여줌

import { useState } from "react";

import PhotoUploadForm from "./components/PhotoUploadForm";
import ResultList from "./components/ResultList";
import StatsSummary from "./components/StatsSummary";
import Sidebar from "./components/Sidebar";

function App() {
  const [currentPage, setCurrentPage] = useState("photo-upload");

  return (
    <div style={{ display: "flex" }}>
      <Sidebar currentPage={currentPage} onNavigate={setCurrentPage} />
      <div style={{ flex: 1, padding: "24px" }}>
        <h1>safEYE 안전 관제 대시보드</h1>
        {currentPage === "photo-upload" && (
          <>
            <PhotoUploadForm />
            <ResultList />
          </>
        )}
        {currentPage === "stats" && <StatsSummary />}
      </div>
    </div>
  );
}

export default App;

import UploadForm from "./components/UploadForm";
import ResultList from "./components/ResultList";
import StatsSummary from "./components/StatsSummary";

function App() {
  return (
    <div>
      <h1>safEYE 안전 관제 대시보드</h1>
      <StatsSummary />
      <UploadForm />
      <ResultList />
    </div>
  );
}

export default App;

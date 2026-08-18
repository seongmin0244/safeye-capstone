import StatsSummary from "../components/StatsSummary";
import ResultList from "../components/ResultList";

function DashboardPage() {
  return (
    <div>
      <StatsSummary />

      <div className="bg-white border border-border rounded-[14px] p-6">
        <ResultList />
      </div>
    </div>
  );
}

export default DashboardPage;

import StatsSummary from "../components/StatsSummary";
import ResultList from "../components/ResultList";
import { useDangerAlerts } from "../hooks/useDangerAlerts";

function DashboardPage() {
  const { alerts, connected } = useDangerAlerts();
  console.log("연결:", connected, "경보:", alerts);

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

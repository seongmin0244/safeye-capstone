import { useState, useEffect } from "react";

function StatsSummary() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const response = await fetch(
          `$import.meta.env.VITE_API_URL}/api/results`,
        );
        const data = await response.json();
        setResults(data);
      } catch (err) {
        setError("통계를 불러오는 데 실패했습니다.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, []);

  if (loading)
    return (
      <div style={{ padding: "16px", color: "#666" }}>통계 불러오는 중...</div>
    );
  if (error)
    return <div style={{ padding: "16px", color: "#c00" }}>{error}</div>;

  const total = results.length;
  const dangerCount = results.filter((item) => item.is_danger).length;
  const safeCount = total - dangerCount;
  const dangerRate = total === 0 ? 0 : Math.round((dangerCount / total) * 100);

  return (
    <div style={{ display: "flex", gap: "12px", marginBottom: "16px" }}>
      <StatCard label="전체 건수" value={total} />
      <StatCard label="위험 감지" value={dangerCount} color="#c00" />
      <StatCard label="안전" value={safeCount} color="#2a7a2a" />
      <StatCard label="위험 비율" value={`${dangerRate}%`} color="#c00" />
    </div>
  );
}

function StatCard({ label, value, color = "#333" }) {
  return (
    <div
      style={{
        flex: 1,
        padding: "16px",
        backgroundColor: "#fafafa",
        border: "1px solid #eee",
        borderRadius: "8px",
        textAlign: "center",
      }}
    >
      <p style={{ fontSize: "13px", color: "#888", marginBottom: "4px" }}>
        {label}
      </p>
      <p style={{ fontSize: "24px", fontWeight: "bold", color }}>{value}</p>
    </div>
  );
}

export default StatsSummary;

import { useState, useEffect } from "react";

function ResultList() {
  const [result, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_URL}/api/results`,
        );
        const data = await response.json();
        setResults(data);
      } catch (err) {
        setError("결과를 불러오지 못 했습니다.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, []);

  if (loading) {
    return (
      <div className="p-4 text-center text-muted bg-[oklch(0.97_0.004_265)] rounded-lg">
        불러오는 중...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-center text-danger font-semibold bg-danger-bg border border-danger rounded-lg">
        {error}
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-[14.5px] font-bold mb-4">판단 결과 목록</h2>
      {results.length === 0 ? (
        <p className="text-muted text-sm">아직 결과가 없습니다.</p>
      ) : (
        result.map((item) => (
          <div
            key={item.id}
            className={`border rounded-lg p-3 mb-2.5 ${item.is_danger ? "border-danger bg-danger-bg" : "border-border bg-white"}`}
          >
            <p
              className={`font-bold mb-1 ${item.is_danger ? "text-danger" : "text-safe"}`}
            >
              {item.is_danger ? "⚠️위험" : "✅안전"}
            </p>
            <p className="text-sm text-ink mb-1">심각도: {item.severity}</p>
            <p className="text-sm text-ink mb-1">
              설명: {item.vlm_description}
            </p>
            <p className="text-sm text-ink">
              위반 규정: {item.violated_regulation || "없음"}
            </p>
          </div>
        ))
      )}
    </div>
  );
}

export default ResultList;

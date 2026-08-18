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
      <div
        style={{
          padding: "16px",
          textAlign: "center",
          color: "#666",
          backgroundColor: "#f5f5f5",
          borderRadius: "8px",
        }}
      >
        불러오는 중...
      </div>
    );
  }

  if (error) {
    return (
      <div
        style={{
          padding: "16px",
          textAlign: "center",
          color: "#c00",
          backgroundColor: "#fdecea",
          border: "1px solid #f5c6cb",
          borderRadius: "8px",
        }}
      >
        {error}
      </div>
    );
  }

  return (
    <div>
      <h2>판단 결과 목록</h2>
      {results.length === 0 ? (
        <p style={{ color: "#888" }}>아직 결과가 없습니다.</p>
      ) : (
        result.map((item) => (
          <div
            key={item.id}
            style={{
              border: `1px solid ${item.is_danger ? "#f5a3a3" : "#ddd"}`,
              backgroundColor: item.is_danger ? "#fff5f5" : "#fff",
              borderRadius: "8px",
              padding: "12px",
              marginBottom: "10px",
            }}
          >
            <p
              style={{
                fontWeight: "bold",
                color: item.is_danger ? "#c00" : "#2a7a2a",
              }}
            >
              {item.is_danger ? "⚠️위험" : "✅안전"}
            </p>
            <p>심각도: {item.severity}</p>
            <p>설명: {item.vlm_description}</p>
            <p>위반 규정: {item.violated_regulation || "없음"}</p>
          </div>
        ))
      )}
    </div>
  );
}

export default ResultList;

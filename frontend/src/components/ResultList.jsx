//key={item.id}:React가 각 항목을 구분하기 위해 필요한 고유값 (없으면 에러)
//item.is_danger ? "위험" : "안전": 삼항 연산자로, item.is_danger가 true면 위험, false면 안전

import { useState, useEffect } from "react";

// const mockData = [
//     {id: 1, is_danger: true, severity: "high", vlm_description: "안전모 미착용 감지", violated_regulation: "제5조"},
//     {id: 2, is_danger: false, severity: "low", vlm_description: "이상 없음", violated_regulation: null},

// ];

function ResultList() {
  const [result, setResults] = useState([]); // 서버에서 받은 데이터
  const [loading, setLoading] = useState(true); // 데이터를 불러오는 중 확인
  const [error, setError] = useState(null); // 에러 여부

  useEffect(() => {
    // 실행할 함수 fetchResults, 빈 배열: 화면이 처음 나타날 때 한 번만 실행하도록
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
        setLoading(false); // 로딩 끝
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

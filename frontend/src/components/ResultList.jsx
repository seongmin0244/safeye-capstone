import { useState, useEffect } from "react";
import { Link } from "react-router-dom";

const SEVERITY_STYLE = {
  CRITICAL: {label: "심각", box:"border-dange bg-danger-bg", text: "text-danger"},
  WARNING: {label:"주의", box:"border-warn bg-warn-bg", text: "text-warn"},
  INFO: {label:"안전", box: "border-border bg-white", text:"text-safe"},
};

function ResultList() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_URL}/api/results`,
        );
        const json = await response.json();
        setResults(json.data ?? []);
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
      <div className="p-4 text-center text-muted">
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
        results.map((item, index) => {
          const style = SEVERITY_STYLE[item.severity] ?? SEVERITY_STYLE.INFO;

          return (
            <div
            key={item.id ?? index}
            className={`border rounded-lg p-3 mb-2.5 ${style.box}`}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className={`font-bold ${style.text}`}>{style.label}</span>
              {item.zoneName && (<span className="text-xs text-muted">· {item.zoneName}</span>)}
            </div>
            
            <p className="text-sm text-ink mb-1">{item.vlmDescription}</p>
            
            {item.violatedRegulation && (<p className="text-sm text-muted mb-1">위반 규정: {item.violatedRegulation}</p>)}

            {item.actionGuide && (<p className="text-sm text-ink mt-2 p-2.5 bg-white/60 rounder-md">조치 방법: {item.actionGuide}</p>)}

            {item.id && (<Link to={`/history/${item.id}`} className="inline-block mt-2 text-xs font-semibold text-accent no-underline">상세 보기 ➡️</Link>)}

          </div>
          )
        })
      )}
    </div>
  );
}

export default ResultList;

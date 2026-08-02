//mockData: 가짜 데이터 (이후 실제 조회 API 응답으로 교체)
//mockData.map((item) => ...): 배열안의 항목 각각을 화면 요소로 변환 (결과마다 카드 하나씩)
//key={item.id}:React가 각 항목을 구분하기 위해 필요한 고유값 (없으면 에러)
//item.is_danger ? "위험" : "안전": 삼항 연산자로, item.is_danger가 true면 위험, false면 안전

const mockData = [
    {id: 1, is_danger: true, severity: "high", vlm_description: "안전모 미착용 감지", violated_regulation: "제5조"},
    {id: 2, is_danger: false, severity: "low", vlm_description: "이상 없음", violated_regulation: null},

];

function ResultList() {
    return (
        <div>
            <h2>판단 결과 목록</h2>
            {mockData.map((item) => (
                <div key={item.id} style={{ border: "1px solid gray", padding: "8px", marginBottom: "8px"}}>
                    <p>위험 여부: {item.is_danger ? "위험" : "안전"}</p>
                    <p>심각도: {item.severity}</p>
                    <p>설명: {item.vlm_description}</p>
                    <p>위반 규정: {item.violated_regulation || "없음"}</p>
                </div>
            ))}
        </div>
    );
}

export default ResultList;
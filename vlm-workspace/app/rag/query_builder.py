from typing import Any


# ============================================================
# 지원하는 위험 유형
# ============================================================

VALID_RISK_TYPES = {
    "NO_HELMET",
    "FALL_HAZARD",
    "BLOCKED_PATH",
}


# ============================================================
# 위험 유형별 RAG 검색 기본 문장
# ============================================================

SEARCH_QUERY_MAP = {

    "NO_HELMET": (
        "산업현장에서 근로자가 안전모를 착용하지 않고 "
        "작업하는 상황과 관련된 보호구 및 안전모 착용 기준"
    ),

    "FALL_HAZARD": (
        "산업현장에서 근로자가 높은 장소에서 작업하며 "
        "추락 위험이 존재하는 상황과 관련된 "
        "안전난간, 작업발판, 안전대 및 추락 방지 기준"
    ),

    "BLOCKED_PATH": (
        "산업현장 작업 통로에 자재 또는 장애물이 있어 "
        "근로자의 통행을 방해하는 상황과 관련된 "
        "작업장 통로 확보 및 정리정돈 기준"
    ),
}


# ============================================================
# risk_type 정규화
# ============================================================

def split_risk_types(
    risk_type: str,
) -> list[str]:
    """
    모델이 실수로 아래처럼 출력해도 처리한다.

    NO_HELMET | FALL_HAZARD | BLOCKED_PATH
    """

    if not risk_type:
        return []

    values = (
        risk_type
        .replace(",", "|")
        .split("|")
    )

    result = []

    for value in values:

        value = value.strip()

        if value in VALID_RISK_TYPES:
            result.append(
                value
            )

    return result


# ============================================================
# 프레임 분석 결과 정규화
# ============================================================

def normalize_vlm_analysis(
    analysis: dict[str, Any],
) -> dict[str, Any]:
    """
    VLM의 분석 결과를 Aggregator가 안정적으로 사용할 수 있도록
    정규화한다.

    주요 기능:
    1. 합쳐진 risk_type 분리
    2. 잘못된 위험 유형 제거
    3. workers의 NOT_WEARING 결과를 NO_HELMET으로 보완
    """

    normalized_hazards = []

    # --------------------------------------------------------
    # 1. 기존 hazards 정규화
    # --------------------------------------------------------

    for hazard in analysis.get(
        "hazards",
        []
    ):

        raw_risk_type = hazard.get(
            "risk_type",
            ""
        )

        risk_types = split_risk_types(
            raw_risk_type
        )

        detected = bool(
            hazard.get(
                "detected",
                False
            )
        )

        confidence = (
            hazard.get(
                "confidence",
                "LOW"
            )
        )

        if confidence not in {
            "LOW",
            "MEDIUM",
            "HIGH",
        }:
            confidence = "LOW"

        evidence = (
            hazard.get(
                "evidence",
                ""
            )
            or ""
        )

        for risk_type in risk_types:

            normalized_hazards.append(
                {
                    "risk_type":
                        risk_type,

                    "detected":
                        detected,

                    "confidence":
                        confidence,

                    "evidence":
                        evidence,
                }
            )

    # --------------------------------------------------------
    # 2. 작업자 PPE 결과에서 NO_HELMET 보완
    # --------------------------------------------------------

    for worker in analysis.get(
        "workers",
        []
    ):

        helmet = worker.get(
            "helmet"
        )

        if helmet != "NOT_WEARING":
            continue

        worker_id = worker.get(
            "worker_id",
            "unknown"
        )

        evidence = (
            f"작업자 {worker_id}가 "
            f"안전모를 착용하지 않은 것으로 분석됨"
        )

        normalized_hazards.append(
            {
                "risk_type":
                    "NO_HELMET",

                "detected":
                    True,

                "confidence":
                    "HIGH",

                "evidence":
                    evidence,
            }
        )

    # --------------------------------------------------------
    # 3. 중복 제거
    # --------------------------------------------------------

    unique_hazards = []

    seen = set()

    for hazard in normalized_hazards:

        key = (
            hazard["risk_type"],
            hazard["detected"],
            hazard["evidence"],
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        unique_hazards.append(
            hazard
        )

    analysis["hazards"] = (
        unique_hazards
    )

    return analysis


# ============================================================
# Aggregator 결과 → RAG 검색문
# ============================================================

def build_search_query(
    hazard: dict[str, Any],
) -> str:
    """
    Aggregator 결과를 RAG 검색에 적합한 한국어 문장으로 만든다.
    """

    risk_type = hazard.get(
        "risk_type",
        ""
    )

    base_query = (
        SEARCH_QUERY_MAP.get(
            risk_type,
            ""
        )
    )

    evidence = hazard.get(
        "evidence",
        []
    )

    if isinstance(
        evidence,
        str
    ):
        evidence_list = [
            evidence
        ]

    else:
        evidence_list = (
            evidence
            if isinstance(
                evidence,
                list
            )
            else []
        )

    evidence_text = " ".join(
        str(item)
        for item in evidence_list[:3]
        if item
    )

    if evidence_text:

        return (
            f"{base_query}. "
            f"현장 관찰 근거: "
            f"{evidence_text}"
        )

    return base_query
from typing import Any


# ============================================================
# 지원 위험 유형
# ============================================================

VALID_RISK_TYPES = {
    "NO_HELMET",
    "FALL_HAZARD",
    "BLOCKED_PATH",
}


# ============================================================
# 위험 유형별 RAG 검색문
# ============================================================

SEARCH_QUERY_MAP = {

    "NO_HELMET": (
        "산업현장에서 근로자가 안전모를 착용하지 않은 상황. "
        "안전모, 보호구의 지급, 보호구 착용, "
        "머리 보호 및 낙하·비래 위험에 관한 안전기준"
    ),

    "FALL_HAZARD": (
        "산업현장에서 근로자의 추락 위험이 존재하는 상황. "
        "추락의 방지, 작업발판, 안전난간, 개구부, "
        "추락방호망, 안전대 및 고소작업에 관한 안전기준"
    ),

    "BLOCKED_PATH": (
        "산업현장에서 작업자의 통행 경로 또는 작업장 통로가 "
        "자재, 장비 또는 장애물로 방해되는 상황. "
        "통로의 설치, 안전한 통행, 작업장 출입구, "
        "통로 유지 및 장애물 제거에 관한 안전기준"
    ),
}


# ============================================================
# risk_type 정규화
# ============================================================

def split_risk_types(
    risk_type: str,
) -> list[str]:
    """
    VLM이 다음과 같이 잘못 출력한 경우에도 처리한다.

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
# VLM 분석 결과 정규화
# ============================================================

def normalize_vlm_analysis(
    analysis: dict[str, Any],
) -> dict[str, Any]:
    """
    VLM 결과를 Aggregator가 안정적으로
    처리할 수 있도록 정규화한다.

    주요 기능
    1. 합쳐진 risk_type 분리
    2. confidence 값 정리
    3. workers의 NOT_WEARING을
       NO_HELMET 위험으로 보완
    """

    normalized_hazards = []

    # --------------------------------------------------------
    # 기존 hazards 정규화
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

        if not risk_types:
            continue

        detected = bool(
            hazard.get(
                "detected",
                False
            )
        )

        confidence = hazard.get(
            "confidence",
            "LOW"
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
    # worker 정보로 NO_HELMET 보완
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
    # 중복 제거
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
    위험 결과를 법령 검색용 문장으로 변환한다.

    [RISK_TYPE=...] 마커는 regulation_retriever가
    위험 유형을 정확하게 식별하기 위한 내부 값이다.

    실제 임베딩 생성 전에는 자동 제거된다.
    """

    risk_type = hazard.get(
        "risk_type",
        ""
    )

    if risk_type not in VALID_RISK_TYPES:
        return ""

    base_query = SEARCH_QUERY_MAP.get(
        risk_type,
        ""
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

    elif isinstance(
        evidence,
        list
    ):
        evidence_list = evidence

    else:
        evidence_list = []

    evidence_text = " ".join(
        str(item).strip()
        for item in evidence_list[:3]
        if str(item).strip()
    )

    # regulation_retriever에서 이 마커로
    # 위험 유형을 정확하게 알아낸다.
    marker = (
        f"[RISK_TYPE={risk_type}]"
    )

    if evidence_text:

        return (
            f"{marker} "
            f"{base_query}. "
            f"현장 관찰 근거: "
            f"{evidence_text}"
        )

    return (
        f"{marker} "
        f"{base_query}"
    )
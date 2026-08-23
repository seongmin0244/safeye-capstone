from typing import Any


VALID_RISK_TYPES = {
    "NO_HELMET",
    "UNFASTENED_SAFETY_HARNESS",
    "FALL_HAZARD",
    "BLOCKED_PATH",
}


SEARCH_QUERY_MAP = {
    "NO_HELMET": (
        "산업현장에서 근로자가 안전모를 착용하지 않은 상황. "
        "안전모, 보호구의 지급, 보호구 착용, "
        "머리 보호 및 낙하·비래 위험 관련 안전기준"
    ),

    "UNFASTENED_SAFETY_HARNESS": (
        "고소작업 중 근로자가 안전대를 착용하지 않았거나 "
        "안전고리를 부착설비에 체결하지 않은 상황. "
        "안전대 착용, 안전대 부착설비, 추락의 방지, "
        "추락방호망 및 고소작업 안전기준"
    ),

    "FALL_HAZARD": (
        "산업현장에서 근로자의 추락 위험이 존재하는 상황. "
        "추락의 방지, 작업발판, 안전난간, 개구부, "
        "추락방호망, 안전대 및 고소작업 관련 안전기준"
    ),

    "BLOCKED_PATH": (
        "산업현장에서 작업자의 통행 경로 또는 작업장 통로가 "
        "자재, 장비 또는 장애물에 의해 방해되는 상황. "
        "통로의 설치, 안전한 통행, 작업장 출입구, "
        "통로 유지 및 장애물 제거 관련 안전기준"
    ),
}


CONFIDENCE_RANK = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
}


def split_risk_types(
    risk_type: str,
) -> list[str]:

    if not risk_type:
        return []

    values = (
        risk_type
        .replace(",", "|")
        .split("|")
    )

    return [
        value.strip()
        for value in values
        if value.strip()
        in VALID_RISK_TYPES
    ]


def normalize_vlm_analysis(
    analysis: dict[str, Any],
) -> dict[str, Any]:

    normalized_hazards = []

    for hazard in analysis.get(
        "hazards",
        []
    ):
        risk_types = split_risk_types(
            hazard.get(
                "risk_type",
                ""
            )
        )

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

        if confidence not in CONFIDENCE_RANK:
            confidence = "LOW"

        proximity = hazard.get(
            "proximity",
            "UNCERTAIN"
        )

        if proximity not in {
            "IMMEDIATE",
            "NEAR",
            "NOT_NEAR",
            "UNCERTAIN",
        }:
            proximity = "UNCERTAIN"

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

                    "proximity":
                        proximity,

                    "evidence":
                        evidence,
                }
            )

    # --------------------------------------------------------
    # worker 정보 기반 안전모 보완
    # --------------------------------------------------------

    for worker in analysis.get(
        "workers",
        []
    ):

        worker_id = worker.get(
            "worker_id",
            "unknown"
        )

        if (
            worker.get("helmet")
            == "NOT_WEARING"
        ):
            normalized_hazards.append(
                {
                    "risk_type":
                        "NO_HELMET",

                    "detected":
                        True,

                    "confidence":
                        "HIGH",

                    "proximity":
                        "UNCERTAIN",

                    "evidence":
                        (
                            f"작업자 {worker_id}가 "
                            "안전모를 착용하지 않은 "
                            "것으로 분석됨"
                        ),
                }
            )

        # ----------------------------------------------------
        # 고소작업 안전대 미체결 보완
        # ----------------------------------------------------

        work_level = worker.get(
            "work_level"
        )

        harness = worker.get(
            "harness"
        )

        if (
            work_level == "ELEVATED"
            and harness in {
                "NOT_WEARING",
                "WORN_NOT_CONNECTED",
            }
        ):

            if harness == "NOT_WEARING":
                evidence = (
                    f"작업자 {worker_id}가 "
                    "고소작업 중 안전대를 "
                    "착용하지 않은 것으로 분석됨"
                )

            else:
                evidence = (
                    f"작업자 {worker_id}가 "
                    "고소작업 중 안전대를 착용했으나 "
                    "안전고리를 체결하지 않은 것으로 분석됨"
                )

            normalized_hazards.append(
                {
                    "risk_type":
                        "UNFASTENED_SAFETY_HARNESS",

                    "detected":
                        True,

                    "confidence":
                        "HIGH",

                    "proximity":
                        "IMMEDIATE",

                    "evidence":
                        evidence,
                }
            )

    # --------------------------------------------------------
    # 완전 동일한 결과 중복 제거
    # --------------------------------------------------------

    unique = []
    seen = set()

    for hazard in normalized_hazards:

        key = (
            hazard["risk_type"],
            hazard["detected"],
            hazard["evidence"],
        )

        if key in seen:
            continue

        seen.add(key)

        unique.append(
            hazard
        )

    analysis["hazards"] = unique

    return analysis


def build_search_query(
    hazard: dict[str, Any],
) -> str:

    risk_type = hazard.get(
        "risk_type",
        ""
    )

    if risk_type not in VALID_RISK_TYPES:
        return ""

    base_query = SEARCH_QUERY_MAP[
        risk_type
    ]

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

    # 안전대 미체결은 기존 FALL_HAZARD Reranking 재사용
    rag_risk_type = risk_type

    if (
        risk_type
        == "UNFASTENED_SAFETY_HARNESS"
    ):
        rag_risk_type = "FALL_HAZARD"

    marker = (
        f"[RISK_TYPE={rag_risk_type}]"
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
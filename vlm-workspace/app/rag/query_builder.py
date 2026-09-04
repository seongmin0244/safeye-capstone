from typing import Any


# ============================================================
# 지원하는 위험 유형
# ============================================================

VALID_RISK_TYPES = {
    "NO_HELMET",
    "UNFASTENED_SAFETY_HARNESS",
    "FALL_HAZARD",
    "BLOCKED_PATH",
}


# ============================================================
# 위험 유형별 RAG 기본 검색문
# ============================================================

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
        "추락방호망 및 고소작업 관련 안전기준"
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


# ============================================================
# Confidence
# ============================================================

CONFIDENCE_RANK = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
}


# ============================================================
# Proximity
# ============================================================

VALID_PROXIMITY = {
    "IMMEDIATE",
    "NEAR",
    "NOT_NEAR",
    "UNCERTAIN",
}


# ============================================================
# 명확한 지상 작업 표현
#
# worker의 work_level과 position/observations가 서로
# 모순될 때 사용한다.
# ============================================================

GROUND_KEYWORDS = (
    "지상 작업",
    "지상에서 작업",
    "지면에서 작업",
    "지면에 서",
    "바닥에서 작업",
    "바닥에 서",
    "ground level",
    "on the ground",
    "standing on the ground",
    "working on the ground",
)


# ============================================================
# FALL_HAZARD를 인정할 수 있는 구체적인 추락 위험 근거
#
# 단순히 '높은 곳', '고소작업'만으로는 인정하지 않는다.
# ============================================================

FALL_HAZARD_STRONG_KEYWORDS = (
    # 개구부 / 구멍
    "개구부",
    "열린 구멍",
    "바닥 구멍",
    "작업발판의 구멍",

    # 단부 / 가장자리
    "단부",
    "가장자리",
    "발판 끝",
    "작업발판 끝",
    "보호되지 않은 가장자리",

    # 난간
    "안전난간 미설치",
    "안전난간이 없음",
    "안전난간 없음",
    "난간이 없음",
    "난간 미설치",
    "난간이 설치되지",

    # 발판
    "작업발판 미설치",
    "작업발판이 없음",
    "발판 미설치",

    # 추락 방호
    "추락방호망 미설치",
    "추락방호망이 없음",
    "추락 방호조치 없음",
    "추락방호조치 없음",
    "추락 방호조치 미흡",
    "추락방호조치 미흡",

    # 안전대
    "안전대 미착용",
    "안전대 미체결",
    "안전고리 미체결",
    "안전고리를 체결하지",

    # 영어가 혹시 남은 경우도 방어
    "unprotected edge",
    "open hole",
    "floor opening",
    "missing guardrail",
    "no guardrail",
    "missing fall protection",
    "no fall protection",
    "without fall protection",
)


# ============================================================
# 불확실성을 나타내는 표현
# ============================================================

UNCERTAINTY_KEYWORDS = (
    "불분명",
    "확인하기 어려",
    "확인할 수 없",
    "판단하기 어려",
    "판단할 수 없",
    "정보가 부족",
    "명확하지 않",
    "불확실",
    "uncertain",
    "unclear",
    "cannot determine",
)


# ============================================================
# 텍스트 Utility
# ============================================================

def contains_any_keyword(
    text: str,
    keywords: tuple[str, ...],
) -> bool:

    if not text:
        return False

    normalized = text.lower()

    return any(
        keyword.lower() in normalized
        for keyword in keywords
    )


def worker_natural_text(
    worker: dict[str, Any],
) -> str:

    parts = [
        str(
            worker.get(
                "position",
                "",
            )
        )
    ]

    observations = worker.get(
        "observations",
        [],
    )

    if isinstance(
        observations,
        list,
    ):
        parts.extend(
            str(item)
            for item in observations
        )

    return " ".join(
        part.strip()
        for part in parts
        if part.strip()
    )


# ============================================================
# Risk Type 문자열 정리
# ============================================================

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
        if value.strip() in VALID_RISK_TYPES
    ]


# ============================================================
# Worker ID 등은 ollama_client.py에서 이미 정규화됨.
#
# 여기서는 worker의 의미적 일관성을 정리한다.
# ============================================================

def normalize_workers(
    analysis: dict[str, Any],
) -> None:
    """
    VLM이 서로 모순되는 worker 상태를 생성했을 때
    명확한 경우에 한해서 논리적으로 보정한다.

    규칙:
    1. GROUND → harness=NOT_APPLICABLE
    2. position/observations에 명확한 지상 작업 표현이 있으면
       GROUND로 보정
    3. ELEVATED / UNCERTAIN은 근거 없이 임의 변경하지 않는다.
    """

    workers = analysis.get(
        "workers",
        [],
    )

    for worker in workers:

        work_level = worker.get(
            "work_level",
            "UNCERTAIN",
        )

        worker_text = worker_natural_text(
            worker
        )

        # ----------------------------------------------------
        # worker 자체 설명에 명확하게 지상이라고 나오는 경우
        #
        # 예:
        # work_level = ELEVATED
        # position = "지상 작업 위치"
        #
        # → GROUND가 더 논리적으로 일관됨
        # ----------------------------------------------------

        if contains_any_keyword(
            worker_text,
            GROUND_KEYWORDS,
        ):

            worker[
                "work_level"
            ] = "GROUND"

            worker[
                "harness"
            ] = "NOT_APPLICABLE"

            continue

        # ----------------------------------------------------
        # 이미 GROUND라면 안전대는 평가 대상이 아님
        # ----------------------------------------------------

        if work_level == "GROUND":

            worker[
                "harness"
            ] = "NOT_APPLICABLE"


# ============================================================
# 안전대 위반 작업자 확인
# ============================================================

def get_harness_violation_workers(
    analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    다음 두 조건을 모두 만족할 때만
    안전대 위반으로 확정한다.

    1. ELEVATED
    2. NOT_WEARING 또는 WORN_NOT_CONNECTED

    UNCERTAIN은 위험으로 확정하지 않는다.
    """

    result = []

    for worker in analysis.get(
        "workers",
        [],
    ):

        work_level = worker.get(
            "work_level",
            "UNCERTAIN",
        )

        harness = worker.get(
            "harness",
            "UNCERTAIN",
        )

        if (
            work_level == "ELEVATED"
            and harness in {
                "NOT_WEARING",
                "WORN_NOT_CONNECTED",
            }
        ):

            result.append(
                worker
            )

    return result


# ============================================================
# FALL_HAZARD 판단에 사용할 전체 자연어 Context
# ============================================================

def build_fall_context(
    analysis: dict[str, Any],
    hazard: dict[str, Any],
) -> str:

    parts = []

    evidence = hazard.get(
        "evidence",
        "",
    )

    if evidence:
        parts.append(
            str(evidence)
        )

    scene_description = analysis.get(
        "scene_description",
        "",
    )

    if scene_description:
        parts.append(
            str(scene_description)
        )

    for worker in analysis.get(
        "workers",
        [],
    ):

        worker_text = worker_natural_text(
            worker
        )

        if worker_text:
            parts.append(
                worker_text
            )

    return " ".join(
        part.strip()
        for part in parts
        if part.strip()
    )


# ============================================================
# 명확한 FALL_HAZARD인지 검증
# ============================================================

def is_valid_fall_hazard(
    analysis: dict[str, Any],
    hazard: dict[str, Any],
    has_harness_violation: bool,
) -> bool:
    """
    FALL_HAZARD를 그대로 신뢰하지 않고
    실제 추락 위험 근거가 있는지 다시 확인한다.

    FALL_HAZARD 인정 조건:
    - 개구부 / 단부 / 난간 미설치 / 방호조치 미설치 등
      명확한 추락 위험 표현이 존재
      또는
    - 실제 ELEVATED 작업자에게 안전대 위반이 확인됨

    단순히:
    - 높은 위치
    - 고소작업
    - 높은 구조물 존재

    정도만으로는 FALL_HAZARD를 확정하지 않는다.
    """

    context = build_fall_context(
        analysis,
        hazard,
    )

    explicit_fall_condition = (
        contains_any_keyword(
            context,
            FALL_HAZARD_STRONG_KEYWORDS,
        )
    )

    if explicit_fall_condition:
        return True

    # 안전대 위반이 실제 worker 상태에서 확인되면
    # 추락 위험을 유지할 근거가 있음
    if has_harness_violation:
        return True

    # 불확실성 표현까지 존재하는 경우
    # FALL_HAZARD를 특히 확정하면 안 됨
    if contains_any_keyword(
        context,
        UNCERTAINTY_KEYWORDS,
    ):
        return False

    # 단순 고소/높은 위치만으로는 인정하지 않음
    return False


# ============================================================
# VLM 분석 결과 정규화
# ============================================================

def normalize_vlm_analysis(
    analysis: dict[str, Any],
) -> dict[str, Any]:
    """
    VLM 분석 결과 후처리.

    1. worker 상태 정규화
    2. 위험 유형 정규화
    3. 안전대 위험 검증
    4. FALL_HAZARD 검증
    5. worker 기반 안전모 위험 보완
    6. worker 기반 안전대 위험 보완
    7. 중복 위험 제거
    """

    # ========================================================
    # 1. Worker 상태 정규화
    # ========================================================

    normalize_workers(
        analysis
    )

    # ========================================================
    # 2. 실제 안전대 위반 작업자 확인
    # ========================================================

    harness_violation_workers = (
        get_harness_violation_workers(
            analysis
        )
    )

    has_harness_violation = bool(
        harness_violation_workers
    )

    normalized_hazards = []

    # ========================================================
    # 3. VLM이 직접 생성한 hazard 정규화
    # ========================================================

    for hazard in analysis.get(
        "hazards",
        [],
    ):

        risk_types = split_risk_types(
            hazard.get(
                "risk_type",
                "",
            )
        )

        original_detected = bool(
            hazard.get(
                "detected",
                False,
            )
        )

        original_confidence = hazard.get(
            "confidence",
            "LOW",
        )

        if (
            original_confidence
            not in CONFIDENCE_RANK
        ):

            original_confidence = "LOW"

        original_proximity = hazard.get(
            "proximity",
            "UNCERTAIN",
        )

        if (
            original_proximity
            not in VALID_PROXIMITY
        ):

            original_proximity = (
                "UNCERTAIN"
            )

        original_evidence = (
            hazard.get(
                "evidence",
                "",
            )
            or ""
        ).strip()

        for risk_type in risk_types:

            # risk_type마다 별도 값을 사용해서
            # 하나의 보정이 다른 위험에 영향을 주지 않게 한다.
            detected = original_detected
            confidence = original_confidence
            proximity = original_proximity
            evidence = original_evidence

            # =================================================
            # 안전대 위험 검증
            # =================================================

            if (
                risk_type
                == "UNFASTENED_SAFETY_HARNESS"
                and detected
                and not has_harness_violation
            ):

                detected = False
                confidence = "LOW"
                proximity = "UNCERTAIN"

                evidence = (
                    "고소작업 중 안전대 미착용 또는 "
                    "미체결 상태가 명확하게 확인되지 않음"
                )

            # =================================================
            # 추락 위험 검증
            # =================================================

            if (
                risk_type
                == "FALL_HAZARD"
                and detected
            ):

                valid_fall_hazard = (
                    is_valid_fall_hazard(
                        analysis=analysis,
                        hazard=hazard,
                        has_harness_violation=(
                            has_harness_violation
                        ),
                    )
                )

                if not valid_fall_hazard:

                    detected = False
                    confidence = "LOW"
                    proximity = "UNCERTAIN"

                    evidence = (
                        "개구부, 단부, 안전난간 미설치 등 "
                        "명확한 추락 위험 근거가 "
                        "확인되지 않음"
                    )

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

    # ========================================================
    # 4. Worker 정보 기반 위험 보완
    # ========================================================

    for worker in analysis.get(
        "workers",
        [],
    ):

        worker_id = worker.get(
            "worker_id",
            "unknown",
        )

        helmet = worker.get(
            "helmet",
            "UNCERTAIN",
        )

        work_level = worker.get(
            "work_level",
            "UNCERTAIN",
        )

        harness = worker.get(
            "harness",
            "UNCERTAIN",
        )

        # ----------------------------------------------------
        # 안전모 미착용
        # ----------------------------------------------------

        if helmet == "NOT_WEARING":

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
        # 안전대 미착용 / 미체결
        #
        # 반드시 ELEVATED여야 함.
        # ----------------------------------------------------

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
                    "안전고리를 부착설비에 "
                    "체결하지 않은 것으로 분석됨"
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

    # ========================================================
    # 5. Hazard 중복 제거
    # ========================================================

    unique_hazards = []

    seen = set()

    for hazard in normalized_hazards:

        key = (
            hazard.get(
                "risk_type"
            ),
            hazard.get(
                "detected"
            ),
            hazard.get(
                "evidence"
            ),
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        unique_hazards.append(
            hazard
        )

    analysis[
        "hazards"
    ] = unique_hazards

    return analysis


# ============================================================
# RAG 검색 Query 생성
# ============================================================

def build_search_query(
    hazard: dict[str, Any],
) -> str:

    risk_type = hazard.get(
        "risk_type",
        "",
    )

    if risk_type not in VALID_RISK_TYPES:
        return ""

    base_query = SEARCH_QUERY_MAP[
        risk_type
    ]

    evidence = hazard.get(
        "evidence",
        [],
    )

    # ========================================================
    # evidence 형식 통일
    # ========================================================

    if isinstance(
        evidence,
        str,
    ):

        evidence_list = [
            evidence
        ]

    elif isinstance(
        evidence,
        list,
    ):

        evidence_list = evidence

    else:

        evidence_list = []

    evidence_text = " ".join(
        str(item).strip()
        for item in evidence_list[:3]
        if str(item).strip()
    )

    # ========================================================
    # 안전대 위험은 기존 FALL_HAZARD Reranking 활용
    # ========================================================

    rag_risk_type = risk_type

    if (
        risk_type
        == "UNFASTENED_SAFETY_HARNESS"
    ):

        rag_risk_type = (
            "FALL_HAZARD"
        )

    marker = (
        f"[RISK_TYPE={rag_risk_type}]"
    )

    # ========================================================
    # 최종 Query
    # ========================================================

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
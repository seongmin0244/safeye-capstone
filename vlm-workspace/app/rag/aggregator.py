from collections import defaultdict
from typing import Any


# ============================================================
# 위험 유형 설정
# ============================================================

VALID_RISK_TYPES = {
    "NO_HELMET",
    "UNFASTENED_SAFETY_HARNESS",
    "FALL_HAZARD",
    "BLOCKED_PATH",
}


CONFIDENCE_SCORE = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
}


MIN_DETECTION_COUNT = {
    "NO_HELMET": 2,
    "UNFASTENED_SAFETY_HARNESS": 2,
    "FALL_HAZARD": 2,
    "BLOCKED_PATH": 2,
}


# ============================================================
# Utility
# ============================================================

def unique_strings(
    values: list[str],
) -> list[str]:
    """
    순서를 유지하면서 문자열 중복 제거
    """

    return list(
        dict.fromkeys(values)
    )


def normalize_risk_types(
    risk_type: str,
) -> list[str]:
    """
    VLM이 다음처럼 여러 위험 유형을 한 문자열로 반환한 경우 대응:

    FALL_HAZARD | BLOCKED_PATH

    각각의 위험 유형으로 분리한다.
    """

    if not risk_type:
        return []

    values = (
        risk_type
        .replace(",", "|")
        .split("|")
    )

    normalized = []

    for value in values:

        value = value.strip()

        if value in VALID_RISK_TYPES:
            normalized.append(
                value
            )

    return normalized


# ============================================================
# 여러 프레임 위험 통합
# ============================================================

def aggregate_frame_results(
    frame_results: list[dict[str, Any]],
    min_detection_count: int = 2,
) -> list[dict[str, Any]]:
    """
    여러 프레임의 hazard 결과를 위험 유형별로 통합한다.

    동일 위험이 일정 개수 이상의 서로 다른 프레임에서
    반복적으로 탐지된 경우에만 최종 위험으로 확정한다.
    """

    buckets = defaultdict(
        lambda: {
            "frames": [],
            "evidence": [],
            "confidence_scores": [],
        }
    )

    # ========================================================
    # 1. 프레임별 hazard 수집
    # ========================================================

    for frame_result in frame_results:

        frame_name = frame_result.get(
            "frame",
            "unknown",
        )

        hazards = frame_result.get(
            "hazards",
            [],
        )

        print(
            f"[Aggregator] "
            f"{frame_name}: "
            f"{len(hazards)}개 hazard"
        )

        for hazard in hazards:

            detected = hazard.get(
                "detected",
                False,
            )

            if not detected:
                continue

            raw_risk_type = hazard.get(
                "risk_type",
                "",
            )

            risk_types = normalize_risk_types(
                raw_risk_type
            )

            if not risk_types:

                print(
                    "[Aggregator 경고] "
                    f"잘못된 risk_type: "
                    f"{raw_risk_type}"
                )

                continue

            confidence = hazard.get(
                "confidence",
                "LOW",
            )

            evidence = hazard.get(
                "evidence",
                "",
            )

            for risk_type in risk_types:

                buckets[
                    risk_type
                ]["frames"].append(
                    frame_name
                )

                if evidence:

                    buckets[
                        risk_type
                    ]["evidence"].append(
                        evidence
                    )

                buckets[
                    risk_type
                ][
                    "confidence_scores"
                ].append(
                    CONFIDENCE_SCORE.get(
                        confidence,
                        1,
                    )
                )

    # ========================================================
    # 2. 위험 유형별 최종 통합
    # ========================================================

    aggregated_results = []

    for risk_type, data in buckets.items():

        evidence_frames = unique_strings(
            data["frames"]
        )

        detection_count = len(
            evidence_frames
        )

        required_count = (
            MIN_DETECTION_COUNT.get(
                risk_type,
                min_detection_count,
            )
        )

        detected = (
            detection_count
            >= required_count
        )

        scores = data[
            "confidence_scores"
        ]

        if scores:

            average_score = (
                sum(scores)
                / len(scores)
            )

        else:

            average_score = 1

        # ----------------------------------------------------
        # 최종 confidence 계산
        # ----------------------------------------------------

        if (
            detection_count >= 3
            and average_score >= 2
        ):

            final_confidence = "HIGH"

        elif (
            detection_count >= 2
            and average_score >= 1.5
        ):

            final_confidence = "MEDIUM"

        else:

            final_confidence = "LOW"

        aggregated_results.append(
            {
                "risk_type":
                    risk_type,

                "detected":
                    detected,

                "confidence":
                    final_confidence,

                "detection_count":
                    detection_count,

                "required_count":
                    required_count,

                "evidence_frames":
                    evidence_frames,

                "evidence":
                    unique_strings(
                        data["evidence"]
                    ),
            }
        )

    return aggregated_results
from collections import defaultdict

from src.schemas import AggregatedHazard, FrameResult
# TODO: 기존 VLM 프로젝트의 app.schemas와 통합 필요
# 현재 RAG 프로토타입의 schema 기준으로 작성된 코드


RISK_FIELD_MAP = {
    "NO_HELMET": "no_helmet",
    "FALL_HAZARD": "fall_hazard",
    "BLOCKED_PATH": "blocked_path",
}

CERTAINTY_SCORE = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
}


def unique_strings(values: list[str]) -> list[str]:
    """순서를 유지하면서 중복 문자열을 제거한다."""

    return list(dict.fromkeys(values))


def aggregate_frame_results(
    frame_results: list[FrameResult],
) -> list[AggregatedHazard]:
    """프레임별 판단을 위험 유형별로 통합한다."""

    buckets = defaultdict(
        lambda: {
            "timestamps": [],
            "evidence": [],
            "scores": [],
        }
    )

    for frame_result in frame_results:
        for risk_type, field_name in RISK_FIELD_MAP.items():
            judgement = getattr(
                frame_result.analysis,
                field_name,
            )

            if not judgement.detected:
                continue

            buckets[risk_type]["timestamps"].append(
                frame_result.timestamp_seconds
            )
            buckets[risk_type]["evidence"].append(
                judgement.evidence
            )
            buckets[risk_type]["scores"].append(
                CERTAINTY_SCORE[judgement.certainty]
            )

    aggregated: list[AggregatedHazard] = []

    for risk_type, data in buckets.items():
        timestamps = data["timestamps"]
        scores = data["scores"]

        detected_count = len(timestamps)
        average_score = sum(scores) / detected_count
        maximum_score = max(scores)

        # 프로토타입용 위험 확정 조건
        confirmed = (
            detected_count >= 2
            or maximum_score == CERTAINTY_SCORE["HIGH"]
        )

        if average_score >= 2.5:
            certainty = "HIGH"
        elif average_score >= 1.5:
            certainty = "MEDIUM"
        else:
            certainty = "LOW"

        aggregated.append(
            AggregatedHazard(
                risk_type=risk_type,
                confirmed=confirmed,
                first_detected_at=min(timestamps),
                last_detected_at=max(timestamps),
                detected_frame_count=detected_count,
                certainty=certainty,
                evidence=unique_strings(
                    data["evidence"]
                )[:3],
            )
        )

    return aggregated
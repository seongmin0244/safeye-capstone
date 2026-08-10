"""내부 분석 결과를 백엔드 응답으로 바꾸는 후처리 계층."""

from app.schemas import VLMInternal, VLMResponse


def verify(internal: VLMInternal) -> tuple[VLMInternal, list[str]]:
    """관찰 목록에 없는 물체가 reasoning에 튀어나오면 신뢰도를 낮춘다."""
    observed = {o.name for o in internal.observed_objects}
    hallucinated: list[str] = []

    # 지금은 YOLO 같은 별도 검출기가 없으니, 자주 생기는 과잉 묘사만 가볍게 잡는다.
    for keyword in ("소화기", "안전난간", "방호덮개", "유도선", "감시자"):
        if keyword in internal.reasoning and keyword not in observed:
            hallucinated.append(keyword)

    if hallucinated:
        internal.confidence *= 0.5
    return internal, hallucinated


def to_response(internal: VLMInternal) -> VLMResponse:
    """내부 스키마를 Spring 쪽에서 쓰는 4개 필드 응답으로 접는다."""
    desc = internal.reasoning.strip()
    if internal.recommended_actions:
        desc += " 조치: " + " / ".join(
            f"{i}. {action}" for i, action in enumerate(internal.recommended_actions, 1)
        )
    if internal.uncertain:
        desc += f" (확인 필요: {', '.join(internal.uncertain)})"

    regulation = " · ".join(internal.references) if internal.references else "해당 없음"

    return VLMResponse(
        is_danger=internal.hazard_detected,
        severity=internal.severity,
        vlm_description=desc or "분석 결과를 생성하지 못했습니다.",
        violated_regulation=regulation,
    )

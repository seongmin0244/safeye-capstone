from ollama import chat

from src.config import PROMPTS_DIR, VLM_MODEL
from src.schemas import (
    AggregatedHazard,
    GeneratedAssessment,
    RegulationResult,
)
# TODO: 기존 VLM 프로젝트의 app.schemas와 통합 필요
# 현재 RAG 프로토타입의 schema 기준으로 작성된 코드



FINAL_PROMPT_PATH = (
    PROMPTS_DIR / "final_response.txt"
)


def load_final_prompt() -> str:
    if not FINAL_PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"최종 프롬프트를 찾을 수 없습니다: "
            f"{FINAL_PROMPT_PATH}"
        )

    return FINAL_PROMPT_PATH.read_text(
        encoding="utf-8"
    )


def format_regulations(
    regulations: list[RegulationResult],
) -> str:
    if not regulations:
        return "검색된 규정 없음"

    lines: list[str] = []

    for index, regulation in enumerate(
        regulations,
        start=1,
    ):
        lines.append(
            f"{index}. 문서명: "
            f"{regulation.document_name}\n"
            f"   조항: {regulation.article} "
            f"{regulation.article_title}\n"
            f"   내용: {regulation.content}"
        )

    return "\n".join(lines)


def generate_assessment(
    hazard: AggregatedHazard,
    regulations: list[RegulationResult],
) -> GeneratedAssessment:
    template = load_final_prompt()

    prompt = template.format(
        risk_type=hazard.risk_type,
        evidence="\n".join(
            f"- {item}"
            for item in hazard.evidence
        ),
        regulations=format_regulations(regulations),
    )

    try:
        response = chat(
            model=VLM_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            format=GeneratedAssessment.model_json_schema(),
            options={
                "temperature": 0,
            },
        )

        return GeneratedAssessment.model_validate_json(
            response.message.content
        )

    except Exception:
        # 생성 실패 시 안전한 기본 응답
        return GeneratedAssessment(
            reason="; ".join(hazard.evidence),
            recommended_action=(
                "해당 작업을 중지하고 안전관리자가 "
                "현장을 직접 확인해야 합니다."
            ),
        )
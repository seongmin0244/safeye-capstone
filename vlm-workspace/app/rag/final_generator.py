from pathlib import Path

from ollama import chat

from .config import PROMPTS_DIR, VLM_MODEL
from .schemas import (
    AggregatedHazard,
    GeneratedAssessment,
    RegulationResult,
)


BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"

# TODO[RAG-VLM]: 기존 app/local 설정과 통합 예정
VLM_MODEL = "qwen2.5vl:7b"



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
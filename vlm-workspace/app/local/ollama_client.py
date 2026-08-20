import base64
import json
import time
from pathlib import Path

import requests

from app.local.config import (
    FRAME_DIR,
    VLM_MODEL,
)


# ============================================================
# 기본 경로
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    .parent
)

PROMPT_PATH = (
    BASE_DIR
    / "prompts"
    / "video_analysis.txt"
)

OLLAMA_URL = (
    "http://127.0.0.1:11434/api/generate"
)


# ============================================================
# JSON Schema
# ============================================================

VLM_SCHEMA = {
    "type": "object",
    "properties": {

        "workers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {

                    "worker_id": {
                        "type": "integer"
                    },

                    "helmet": {
                        "type": "string",
                        "enum": [
                            "WEARING",
                            "NOT_WEARING",
                            "UNCERTAIN",
                        ],
                    },

                    "vest": {
                        "type": "string",
                        "enum": [
                            "WEARING",
                            "NOT_WEARING",
                            "UNCERTAIN",
                        ],
                    },

                    "position": {
                        "type": "string"
                    },

                    "observations": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                    },
                },

                "required": [
                    "worker_id",
                    "helmet",
                    "vest",
                    "position",
                    "observations",
                ],

                "additionalProperties": False,
            },
        },

        "hazards": {
            "type": "array",

            "items": {
                "type": "object",

                "properties": {

                    "risk_type": {
                        "type": "string",
                        "enum": [
                            "NO_HELMET",
                            "FALL_HAZARD",
                            "BLOCKED_PATH",
                        ],
                    },

                    "detected": {
                        "type": "boolean"
                    },

                    "confidence": {
                        "type": "string",
                        "enum": [
                            "LOW",
                            "MEDIUM",
                            "HIGH",
                        ],
                    },

                    "evidence": {
                        "type": "string"
                    },
                },

                "required": [
                    "risk_type",
                    "detected",
                    "confidence",
                    "evidence",
                ],

                "additionalProperties": False,
            },
        },

        "scene_description": {
            "type": "string"
        },
    },

    "required": [
        "workers",
        "hazards",
        "scene_description",
    ],

    "additionalProperties": False,
}


# ============================================================
# 프롬프트 로드
# ============================================================

def load_video_prompt() -> str:
    """
    video_analysis.txt 파일을 읽는다.
    """

    if not PROMPT_PATH.exists():
        raise FileNotFoundError(
            "영상 분석 프롬프트를 찾을 수 없습니다.\n"
            f"경로: {PROMPT_PATH}"
        )

    prompt = PROMPT_PATH.read_text(
        encoding="utf-8"
    ).strip()

    if not prompt:
        raise ValueError(
            "video_analysis.txt가 비어 있습니다."
        )

    return prompt


# ============================================================
# 이미지 검증
# ============================================================

def validate_image(
    image_path: str | Path,
) -> Path:
    """
    이미지가 실제로 존재하는지 확인한다.
    """

    image_path = Path(
        image_path
    )

    if not image_path.exists():
        raise FileNotFoundError(
            f"이미지를 찾을 수 없습니다: "
            f"{image_path}"
        )

    if not image_path.is_file():
        raise ValueError(
            f"이미지 파일이 아닙니다: "
            f"{image_path}"
        )

    if image_path.suffix.lower() not in {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }:
        raise ValueError(
            "지원하지 않는 이미지 형식입니다: "
            f"{image_path.suffix}"
        )

    return image_path.resolve()


# ============================================================
# 이미지 Base64 변환
# ============================================================

def image_to_base64(
    image_path: Path,
) -> str:
    """
    Ollama REST API 전달용 Base64 문자열 생성.
    """

    with image_path.open(
        "rb"
    ) as file:

        image_bytes = file.read()

    return base64.b64encode(
        image_bytes
    ).decode(
        "utf-8"
    )


# ============================================================
# JSON 검사
# ============================================================

def parse_json_response(
    content: str,
) -> dict:
    """
    Ollama 응답이 정상 JSON인지 확인한다.
    """

    content = content.strip()

    if content.startswith("```"):

        lines = content.splitlines()

        if lines:
            lines = lines[1:]

        if (
            lines
            and lines[-1].strip() == "```"
        ):
            lines = lines[:-1]

        content = "\n".join(
            lines
        ).strip()

    try:

        return json.loads(
            content
        )

    except json.JSONDecodeError as error:

        print()
        print(
            "=== JSON 파싱 실패 ==="
        )

        print(
            f"오류 위치: "
            f"line={error.lineno}, "
            f"column={error.colno}, "
            f"char={error.pos}"
        )

        print()
        print(
            "=== 응답 마지막 500자 ==="
        )

        print(
            content[-500:]
        )

        raise


# ============================================================
# 이미지 분석
# ============================================================

def analyze_image(
    image_path: str | Path,
    prompt: str | None = None,
    max_retries: int = 3,
) -> str:
    """
    산업현장 프레임 하나를
    Qwen2.5-VL로 분석한다.

    반환값:
        JSON 문자열
    """

    image_path = validate_image(
        image_path
    )

    if prompt is None:
        prompt = load_video_prompt()

    image_base64 = (
        image_to_base64(
            image_path
        )
    )

    # ========================================================
    # REST API 요청 데이터
    # ========================================================

    payload = {

        "model":
            VLM_MODEL,

        "prompt":
            prompt,

        "images": [
            image_base64
        ],

        # JSON Schema로 출력 구조 강제
        "format":
            VLM_SCHEMA,

        "stream":
            False,

        "keep_alive":
            "10m",

        "options": {

            # 결과 일관성
            "temperature":
                0,

            # 기존 512에서는 긴 JSON이
            # 잘릴 가능성이 있으므로 증가
            "num_predict":
                2048,
        },
    }

    last_error = None

    # ========================================================
    # 재시도
    # ========================================================

    for attempt in range(
        1,
        max_retries + 1,
    ):

        try:

            response = requests.post(
                OLLAMA_URL,
                json=payload,
                timeout=300,
            )

            response.raise_for_status()

            data = response.json()

            # ------------------------------------------------
            # 상태 확인
            # ------------------------------------------------

            done = data.get(
                "done"
            )

            done_reason = data.get(
                "done_reason"
            )

            model = data.get(
                "model"
            )

            eval_count = data.get(
                "eval_count"
            )

            print(
                f"[Ollama] "
                f"{image_path.name} "
                f"status={response.status_code}, "
                f"done={done}, "
                f"reason={done_reason}, "
                f"tokens={eval_count}, "
                f"model={model}"
            )

            # ------------------------------------------------
            # 응답 가져오기
            # ------------------------------------------------

            content = data.get(
                "response",
                ""
            )

            if not content:

                raise RuntimeError(
                    "Ollama가 빈 응답을 반환했습니다.\n"
                    f"전체 응답: {data}"
                )

            # ------------------------------------------------
            # JSON 검증
            # ------------------------------------------------

            parsed = (
                parse_json_response(
                    content
                )
            )

            # ------------------------------------------------
            # 정상 JSON 반환
            # ------------------------------------------------

            return json.dumps(
                parsed,
                ensure_ascii=False,
                indent=2,
            )

        except Exception as error:

            last_error = error

            print()
            print(
                f"[재시도] "
                f"{image_path.name} "
                f"{attempt}/{max_retries}"
            )

            print(
                f"원인: {error}"
            )

            if attempt < max_retries:

                print(
                    "3초 후 다시 시도합니다..."
                )

                time.sleep(3)

    # ========================================================
    # 모든 요청 실패
    # ========================================================

    raise RuntimeError(
        f"{image_path.name} "
        "VLM 분석 최종 실패"
    ) from last_error


# ============================================================
# 단일 이미지 테스트
# ============================================================

def main() -> None:

    image_path = (
        FRAME_DIR
        / "frame_0000.00.jpg"
    )

    print()
    print("=" * 60)
    print("VLM 단일 이미지 테스트")
    print("=" * 60)

    print(
        f"모델: {VLM_MODEL}"
    )

    print(
        f"이미지: {image_path}"
    )

    try:

        result = analyze_image(
            image_path
        )

        print()
        print("=" * 60)
        print("VLM 분석 결과")
        print("=" * 60)

        print(
            result
        )

    except Exception as error:

        print()
        print("=" * 60)
        print("VLM 분석 실패")
        print("=" * 60)

        print(
            f"{type(error).__name__}: "
            f"{error}"
        )


if __name__ == "__main__":
    main()
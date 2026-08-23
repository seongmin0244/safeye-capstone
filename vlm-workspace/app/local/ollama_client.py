import base64
import json
import re
import time
from pathlib import Path

import cv2
import requests

from app.local.config import (
    FRAME_DIR,
    VLM_MODEL,
)


# ============================================================
# 기본 경로 / 설정
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

MAX_IMAGE_SIDE = 1280
JPEG_QUALITY = 90


# ============================================================
# 기본 출력 제약
# ============================================================

OUTPUT_CONSTRAINTS = """
[출력 규칙]

- 반드시 하나의 유효한 JSON 객체만 반환하세요.
- JSON 외부에 설명을 작성하지 마세요.
- Markdown을 사용하지 마세요.
- 동일한 문장이나 표현을 반복해서 생성하지 마세요.

[출력 언어]

- position, observations, evidence, scene_description 등
  모든 자연어 설명은 반드시 한국어로 작성하세요.
- 자연어 설명에 영어 또는 중국어를 사용하거나
  여러 언어를 혼용하지 마세요.
- JSON key와 enum 값은 지정된 형식을 그대로 유지하세요.
- 이 규칙은 출력 언어에만 적용하며,
  기존 분석 내용과 판단 근거의 상세도를
  생략하거나 축약하지 마세요.
"""


# ============================================================
# 언어 검증 실패 시 재시도용 추가 지시
# ============================================================

LANGUAGE_RETRY_INSTRUCTION = """
[언어 검증 실패 - 재출력 지시]

이전 응답의 자연어 필드에 영어 또는 중국어가 포함되었습니다.

이미지에 대한 분석 기준과 판단 내용의 상세도는 그대로 유지하세요.
분석 내용을 축약하거나 단순화하지 마세요.

단, 다음 자연어 필드만 반드시 한국어로 작성하세요.

- position
- observations
- evidence
- scene_description

JSON key와 enum 값은 기존 영어 형식을 그대로 유지하세요.

예:
"position": "고소 작업발판 가장자리에서 작업 중"

잘못된 예:
"position": "WORKING_ON_HIGH_STRUCTURE"

JSON 객체 하나만 다시 반환하세요.
"""


# ============================================================
# VLM JSON Schema
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

                    "harness": {

                        "type": "string",

                        "enum": [
                            "CONNECTED",
                            "WORN_NOT_CONNECTED",
                            "NOT_WEARING",
                            "UNCERTAIN",
                            "NOT_APPLICABLE",
                        ],
                    },

                    "work_level": {

                        "type": "string",

                        "enum": [
                            "GROUND",
                            "ELEVATED",
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
                    "harness",
                    "work_level",
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
                            "UNFASTENED_SAFETY_HARNESS",
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

                    "proximity": {

                        "type": "string",

                        "enum": [
                            "IMMEDIATE",
                            "NEAR",
                            "NOT_NEAR",
                            "UNCERTAIN",
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
                    "proximity",
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
# 언어 검증 전용 예외
# ============================================================

class LanguageValidationError(
    RuntimeError
):
    pass


# ============================================================
# Prompt 로드
# ============================================================

def load_video_prompt() -> str:

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

    return (
        prompt
        + "\n\n"
        + OUTPUT_CONSTRAINTS
    )


# ============================================================
# 이미지 파일 검증
# ============================================================

def validate_image(
    image_path: str | Path,
) -> Path:

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
# 이미지 전처리
# ============================================================

def prepare_image_base64(
    image_path: Path,
) -> str:

    image = cv2.imread(
        str(image_path)
    )

    if image is None:

        raise RuntimeError(
            f"이미지를 읽을 수 없습니다: "
            f"{image_path}"
        )

    height, width = (
        image.shape[:2]
    )

    max_side = max(
        width,
        height,
    )

    if max_side > MAX_IMAGE_SIDE:

        scale = (
            MAX_IMAGE_SIDE
            / max_side
        )

        new_width = max(
            1,
            int(
                width
                * scale
            )
        )

        new_height = max(
            1,
            int(
                height
                * scale
            )
        )

        image = cv2.resize(
            image,
            (
                new_width,
                new_height,
            ),
            interpolation=cv2.INTER_AREA,
        )

        print(
            f"[이미지 전처리] "
            f"{image_path.name}: "
            f"{width}x{height} "
            f"→ "
            f"{new_width}x{new_height}"
        )

    success, encoded = (
        cv2.imencode(
            ".jpg",
            image,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                JPEG_QUALITY,
            ],
        )
    )

    if not success:

        raise RuntimeError(
            f"JPEG 인코딩 실패: "
            f"{image_path}"
        )

    return base64.b64encode(
        encoded.tobytes()
    ).decode(
        "utf-8"
    )


# ============================================================
# Markdown Fence 제거
# ============================================================

def remove_markdown_fence(
    content: str,
) -> str:

    content = content.strip()

    if not content.startswith(
        "```"
    ):

        return content

    lines = content.splitlines()

    if lines:
        lines = lines[1:]

    if (
        lines
        and lines[-1].strip()
        == "```"
    ):

        lines = lines[:-1]

    return "\n".join(
        lines
    ).strip()


# ============================================================
# JSON Parsing
# ============================================================

def parse_json_response(
    content: str,
) -> dict:

    content = (
        remove_markdown_fence(
            content
        )
    )

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
# Worker ID 정규화
#
# VLM이 임의의 큰 숫자를 생성하더라도
# 작업자 배열 순서대로 1, 2, 3...으로 재부여한다.
# ============================================================

def normalize_worker_ids(
    analysis: dict,
) -> dict:

    workers = analysis.get(
        "workers",
        []
    )

    for worker_id, worker in enumerate(
        workers,
        start=1,
    ):

        worker[
            "worker_id"
        ] = worker_id

    return analysis


# ============================================================
# 자연어 필드 추출
# ============================================================

def collect_natural_language_fields(
    analysis: dict,
) -> list[
    tuple[str, str]
]:

    fields = []

    scene_description = analysis.get(
        "scene_description",
        ""
    )

    if scene_description:

        fields.append(
            (
                "scene_description",
                str(
                    scene_description
                ),
            )
        )

    for index, worker in enumerate(
        analysis.get(
            "workers",
            []
        )
    ):

        position = worker.get(
            "position",
            ""
        )

        if position:

            fields.append(
                (
                    f"workers[{index}].position",
                    str(
                        position
                    ),
                )
            )

        observations = worker.get(
            "observations",
            []
        )

        for (
            obs_index,
            observation,
        ) in enumerate(
            observations
        ):

            if observation:

                fields.append(
                    (
                        (
                            f"workers[{index}]"
                            f".observations[{obs_index}]"
                        ),
                        str(
                            observation
                        ),
                    )
                )

    for index, hazard in enumerate(
        analysis.get(
            "hazards",
            []
        )
    ):

        evidence = hazard.get(
            "evidence",
            ""
        )

        if evidence:

            fields.append(
                (
                    f"hazards[{index}].evidence",
                    str(
                        evidence
                    ),
                )
            )

    return fields


# ============================================================
# 자연어 언어 검사
# ============================================================

def is_invalid_natural_language(
    text: str,
) -> bool:

    text = str(
        text
    ).strip()

    if not text:

        return False

    # 중국어 / 한자
    if re.search(
        r"[\u4e00-\u9fff]",
        text,
    ):

        return True

    # WORKING_ON_HIGH_STRUCTURE 같은
    # 영어 enum 스타일 표현
    if re.search(
        r"\b[A-Z]{2,}"
        r"(?:_[A-Z]{2,})+\b",
        text,
    ):

        return True

    english_words = re.findall(
        r"\b[A-Za-z]{2,}\b",
        text,
    )

    hangul_chars = re.findall(
        r"[가-힣]",
        text,
    )

    # 한글이 전혀 없고 영단어가 2개 이상
    if (
        len(hangul_chars) == 0
        and len(english_words) >= 2
    ):

        return True

    # 한글 문장에 긴 영어 문장이 섞임
    if len(english_words) >= 4:

        return True

    return False


# ============================================================
# 한국어 출력 검증
# ============================================================

def validate_korean_output(
    analysis: dict,
) -> None:

    invalid_fields = []

    fields = (
        collect_natural_language_fields(
            analysis
        )
    )

    for (
        field_name,
        text,
    ) in fields:

        if is_invalid_natural_language(
            text
        ):

            invalid_fields.append(
                (
                    field_name,
                    text,
                )
            )

    if not invalid_fields:

        return

    print()
    print(
        "=== 출력 언어 검증 실패 ==="
    )

    for (
        field_name,
        text,
    ) in invalid_fields:

        print(
            f"- {field_name}: "
            f"{text[:120]}"
        )

    raise LanguageValidationError(
        "자연어 필드에 영어 또는 중국어가 "
        "포함되어 있습니다."
    )


# ============================================================
# Ollama 요청
# ============================================================

def request_ollama(
    image_path: Path,
    image_base64: str,
    prompt: str,
    attempt: int,
) -> dict:

    repeat_penalty = (
        1.15
        + (
            attempt - 1
        )
        * 0.05
    )

    temperature = min(
        0.10
        + (
            attempt - 1
        )
        * 0.05,
        0.20,
    )

    payload = {

        "model":
            VLM_MODEL,

        "prompt":
            prompt,

        "images": [
            image_base64
        ],

        "format":
            VLM_SCHEMA,

        "stream":
            False,

        "keep_alive":
            "10m",

        "options": {

            "temperature":
                temperature,

            "num_predict":
                1200,

            "repeat_penalty":
                repeat_penalty,

            "repeat_last_n":
                256,

            "top_p":
                0.90,
        },
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=300,
    )

    response.raise_for_status()

    data = response.json()

    print(
        f"[Ollama] "
        f"{image_path.name} "
        f"status={response.status_code}, "
        f"done={data.get('done')}, "
        f"reason={data.get('done_reason')}, "
        f"tokens={data.get('eval_count')}, "
        f"model={data.get('model')}"
    )

    return data


# ============================================================
# 이미지 분석
# ============================================================

def analyze_image(
    image_path: str | Path,
    prompt: str | None = None,
    max_retries: int = 3,
) -> str:

    image_path = (
        validate_image(
            image_path
        )
    )

    if prompt is None:

        prompt = (
            load_video_prompt()
        )

    image_base64 = (
        prepare_image_base64(
            image_path
        )
    )

    last_error = None

    language_retry_required = False

    for attempt in range(
        1,
        max_retries + 1,
    ):

        try:

            request_prompt = prompt

            if language_retry_required:

                request_prompt = (
                    prompt
                    + "\n\n"
                    + LANGUAGE_RETRY_INSTRUCTION
                )

                print(
                    "[언어 재시도] "
                    "분석 내용은 유지하고 "
                    "자연어 필드만 한국어로 재생성합니다."
                )

            data = request_ollama(
                image_path=image_path,
                image_base64=image_base64,
                prompt=request_prompt,
                attempt=attempt,
            )

            done = data.get(
                "done",
                False
            )

            done_reason = data.get(
                "done_reason"
            )

            model = data.get(
                "model",
                ""
            )

            content = data.get(
                "response",
                ""
            )

            # ------------------------------------------------
            # 빈 응답 검사
            # ------------------------------------------------

            if (
                not model
                or not content
            ):

                raise RuntimeError(
                    "Ollama가 빈 응답을 반환했습니다.\n"
                    f"전체 응답: {data}"
                )

            # ------------------------------------------------
            # 정상 종료 검사
            # ------------------------------------------------

            if not done:

                raise RuntimeError(
                    "Ollama 추론이 정상적으로 "
                    "완료되지 않았습니다.\n"
                    f"전체 응답: {data}"
                )

            # ------------------------------------------------
            # 출력 길이 제한
            # ------------------------------------------------

            if done_reason == "length":

                raise RuntimeError(
                    "VLM 응답이 출력 길이 제한에 "
                    "도달했습니다."
                )

            # ------------------------------------------------
            # JSON Parsing
            # ------------------------------------------------

            parsed = (
                parse_json_response(
                    content
                )
            )

            # ------------------------------------------------
            # Worker ID 정규화
            #
            # 모델이 생성한 worker_id는 신뢰하지 않고
            # 배열 순서대로 1부터 다시 부여한다.
            # ------------------------------------------------

            parsed = (
                normalize_worker_ids(
                    parsed
                )
            )

            # ------------------------------------------------
            # 자연어 한국어 검증
            # ------------------------------------------------

            validate_korean_output(
                parsed
            )

            # ------------------------------------------------
            # 정상 결과 반환
            # ------------------------------------------------

            return json.dumps(
                parsed,
                ensure_ascii=False,
                indent=2,
            )

        except LanguageValidationError as error:

            last_error = error

            language_retry_required = True

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
                    "한국어 출력 규칙을 강화하여 "
                    "3초 후 다시 시도합니다..."
                )

                time.sleep(3)

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
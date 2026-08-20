import base64
import json
import time
from pathlib import Path

import cv2
import requests

from app.local.config import (
    FRAME_DIR,
    VLM_MODEL,
)


# ============================================================
# 기본 설정
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


# VLM에 전달할 이미지의 최대 한 변
MAX_IMAGE_SIDE = 1280

JPEG_QUALITY = 90


# ============================================================
# 추가 출력 제한 프롬프트
# ============================================================

OUTPUT_CONSTRAINTS = """
[출력 언어 규칙]

- 모든 자연어 설명은 반드시 한국어로 작성하세요.
- position은 한국어로 작성하세요.
- observations는 한국어로 작성하세요.
- evidence는 한국어로 작성하세요.
- scene_description은 한국어로 작성하세요.
- 자연어 설명을 영어 또는 중국어로 작성하지 마세요.
- 여러 언어를 혼용하지 마세요.

다음 JSON enum 값은 반드시 영어 원문 그대로 유지하세요:
- WEARING
- NOT_WEARING
- UNCERTAIN
- NO_HELMET
- FALL_HAZARD
- BLOCKED_PATH
- LOW
- MEDIUM
- HIGH

중요:
- 위 언어 규칙 외에는 기존 분석 내용, 판단 기준, 설명 수준을 변경하지 마세요.
- 기존 프롬프트에서 요구하는 정보를 생략하거나 축약하지 마세요.
"""


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
# 이미지 검증
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
# VLM 입력용 이미지 전처리
# ============================================================

def prepare_image_base64(
    image_path: Path,
) -> str:
    """
    원본 프레임을 직접 전송하지 않고
    OpenCV로 다시 읽어서 VLM용 JPEG로 변환한다.

    큰 이미지는 최대 1280px까지 자동 축소한다.
    원본 프레임 파일 자체는 변경하지 않는다.
    """

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

    # --------------------------------------------------------
    # 이미지 크기 축소
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # JPEG 재인코딩
    # --------------------------------------------------------

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
# JSON 파싱
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
# Ollama 요청
# ============================================================

def request_ollama(
    image_path: Path,
    image_base64: str,
    prompt: str,
    attempt: int,
) -> dict:
    """
    재시도 횟수에 따라 repeat_penalty를
    조금씩 증가시켜 반복 생성 가능성을 낮춘다.
    """

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

            # 정상적인 JSON이면 충분한 크기.
            # 무한 반복을 2048까지 허용하지 않는다.
            "num_predict":
                1200,

            # 반복 억제
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

    # --------------------------------------------------------
    # 이미지 리사이즈 + JPEG 재인코딩
    #
    # 모든 retry에서 동일한 전처리 이미지를 사용
    # --------------------------------------------------------

    image_base64 = (
        prepare_image_base64(
            image_path
        )
    )

    last_error = None

    # ========================================================
    # 재시도
    # ========================================================

    for attempt in range(
        1,
        max_retries + 1,
    ):

        try:

            data = request_ollama(
                image_path=image_path,
                image_base64=image_base64,
                prompt=prompt,
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
            # Ollama 비정상 빈 응답
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
            # 정상 종료되지 않음
            # ------------------------------------------------

            if not done:

                raise RuntimeError(
                    "Ollama 추론이 정상적으로 "
                    "완료되지 않았습니다.\n"
                    f"전체 응답: {data}"
                )

            # ------------------------------------------------
            # 출력 길이 한도 도달
            # ------------------------------------------------

            if done_reason == "length":

                print()
                print(
                    "[경고] 모델 출력이 "
                    "길이 제한에 도달했습니다."
                )

                print(
                    "응답 마지막 300자:"
                )

                print(
                    content[-300:]
                )

                raise RuntimeError(
                    "VLM 응답이 반복되거나 "
                    "너무 길어 출력 제한에 도달했습니다."
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
            # 정상 반환
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
    # 모든 재시도 실패
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
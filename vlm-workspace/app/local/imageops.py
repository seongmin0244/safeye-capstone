"""로컬 VLM 노드에서 사용하는 이미지 검증 및 축소 유틸리티.

이미지 파일의 존재 여부와 확장자를 검증하고,
업로드 이미지가 너무 큰 경우 VLM의 vision token 및 VRAM 사용량을
줄이기 위해 로컬 노드에서 미리 축소한다.
"""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image


# ============================================================
# Supported Image Formats
# ============================================================

SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


# ============================================================
# Image Path Validation
# ============================================================

def validate_image(image_path: str | Path) -> Path:
    """
    이미지 파일 존재 여부와 확장자를 검사한다.

    Args:
        image_path:
            검사할 이미지 파일 경로.

    Returns:
        검증된 이미지의 절대 경로.

    Raises:
        FileNotFoundError:
            이미지 파일이 존재하지 않는 경우.

        ValueError:
            경로가 파일이 아니거나 지원하지 않는 확장자인 경우.
    """

    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(
            f"이미지 파일을 찾을 수 없습니다: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"파일이 아닙니다: {path}"
        )

    if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        raise ValueError(
            f"지원하지 않는 이미지 형식입니다: {path.suffix}"
        )

    return path.resolve()


# ============================================================
# Image Resize / Optimization
# ============================================================

def clamp(
    raw: bytes,
    max_edge: int,
    quality: int = 88,
) -> tuple[bytes, dict]:
    """
    이미지의 긴 변이 max_edge를 넘으면 JPEG로 축소한다.

    VLM 입력 이미지가 지나치게 큰 경우 vision token과
    VRAM 사용량이 증가할 수 있으므로 로컬 노드에서 미리 축소한다.

    Args:
        raw:
            원본 이미지 bytes.

        max_edge:
            허용할 최대 긴 변 길이.

        quality:
            JPEG 저장 품질.

    Returns:
        축소된 이미지 bytes와 이미지 메타데이터.
    """

    img = Image.open(io.BytesIO(raw))

    ow, oh = img.size

    # 이미 충분히 작고 RGB인 경우 원본 유지
    if max(ow, oh) <= max_edge and img.mode == "RGB":
        return raw, {
            "w": ow,
            "h": oh,
            "orig_w": ow,
            "orig_h": oh,
            "resized": False,
            "bytes": len(raw),
        }

    # JPEG 저장을 위해 RGB 변환
    if img.mode != "RGB":
        img = img.convert("RGB")

    # 긴 변 기준 축소
    if max(ow, oh) > max_edge:
        scale = max_edge / max(ow, oh)

        img = img.resize(
            (
                max(1, int(ow * scale)),
                max(1, int(oh * scale)),
            ),
            Image.LANCZOS,
        )

    buf = io.BytesIO()

    img.save(
        buf,
        format="JPEG",
        quality=quality,
    )

    out = buf.getvalue()

    return out, {
        "w": img.size[0],
        "h": img.size[1],
        "orig_w": ow,
        "orig_h": oh,
        "resized": True,
        "bytes": len(out),
    }


def to_edge(
    raw: bytes,
    edge: int,
    quality: int = 88,
) -> bytes:
    """
    벤치마크용 이미지 리사이즈.

    작은 이미지는 확대하지 않고,
    긴 변이 edge를 초과하는 경우에만 축소한다.
    """

    img = Image.open(io.BytesIO(raw))

    if img.mode != "RGB":
        img = img.convert("RGB")

    w, h = img.size

    scale = edge / max(w, h)

    if scale < 1:
        img = img.resize(
            (
                max(1, int(w * scale)),
                max(1, int(h * scale)),
            ),
            Image.LANCZOS,
        )

    buf = io.BytesIO()

    img.save(
        buf,
        format="JPEG",
        quality=quality,
    )

    return buf.getvalue()


def dims(raw: bytes) -> tuple[int, int]:
    """
    이미지 bytes에서 원본 이미지 크기를 반환한다.

    Returns:
        (width, height)
    """

    with Image.open(io.BytesIO(raw)) as img:
        return img.size

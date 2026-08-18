"""로컬 노드에서 쓰는 이미지 축소 유틸.

업로드가 너무 크면 VLM의 vision token과 VRAM 사용량이 튈 수 있음.
로컬 노드 측에서 미리 축소해두면 VLM이 안정적으로 동작함.
"""

from __future__ import annotations

import io

from PIL import Image


def clamp(raw: bytes, max_edge: int, quality: int = 88) -> tuple[bytes, dict]:
    """긴 변이 `max_edge`를 넘으면 JPEG로 줄이고, 함께 기록할 메타데이터를 돌려준다."""
    img = Image.open(io.BytesIO(raw))
    ow, oh = img.size

    if max(ow, oh) <= max_edge and img.mode == "RGB":
        return raw, {
            "w": ow,
            "h": oh,
            "orig_w": ow,
            "orig_h": oh,
            "resized": False,
            "bytes": len(raw),
        }

    if img.mode != "RGB":
        img = img.convert("RGB")
    if max(ow, oh) > max_edge:
        scale = max_edge / max(ow, oh)
        img = img.resize(
            (max(1, int(ow * scale)), max(1, int(oh * scale))),
            Image.LANCZOS,
        )

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    out = buf.getvalue()
    return out, {
        "w": img.size[0],
        "h": img.size[1],
        "orig_w": ow,
        "orig_h": oh,
        "resized": True,
        "bytes": len(out),
    }


def to_edge(raw: bytes, edge: int, quality: int = 88) -> bytes:
    """벤치마크용 리사이즈. 작은 이미지는 키우지 않고 큰 이미지만 줄인다."""
    img = Image.open(io.BytesIO(raw))
    if img.mode != "RGB":
        img = img.convert("RGB")
    w, h = img.size
    scale = edge / max(w, h)
    if scale < 1:
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def dims(raw: bytes) -> tuple[int, int]:
    with Image.open(io.BytesIO(raw)) as img:
        return img.size

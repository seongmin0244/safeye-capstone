from pathlib import Path


SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def validate_image(image_path: str | Path) -> Path:
    """
    이미지 파일 존재 여부와 확장자를 검사한다.
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
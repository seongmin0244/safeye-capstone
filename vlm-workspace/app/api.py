from pathlib import Path
from uuid import uuid4

from fastapi import (
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)

from starlette.concurrency import (
    run_in_threadpool,
)

from app.api_schemas import (
    AIAnalysisResponse,
)

from app.image_pipeline import (
    analyze_image_for_api,
)


app = FastAPI(
    title="safEYE AI API",
    version="1.0.0",
)


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

UPLOAD_DIR = (
    BASE_DIR
    / "data"
    / "uploads"
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


@app.get(
    "/health"
)
async def health():

    return {
        "status": "ok"
    }


@app.post(
    "/api/vlm/analyze",
    response_model=AIAnalysisResponse,
)
async def analyze_image_endpoint(
    image: UploadFile = File(...),
):

    if (
        image.content_type
        not in ALLOWED_CONTENT_TYPES
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "지원하지 않는 이미지 형식입니다. "
                "JPEG, PNG, WEBP만 지원합니다."
            ),
        )

    suffix_map = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }

    suffix = suffix_map[
        image.content_type
    ]

    temp_path = (
        UPLOAD_DIR
        / f"{uuid4().hex}{suffix}"
    )

    try:
        content = await image.read()

        if not content:
            raise HTTPException(
                status_code=400,
                detail="빈 이미지 파일입니다.",
            )

        temp_path.write_bytes(
            content
        )

        result = await run_in_threadpool(
            analyze_image_for_api,
            temp_path,
        )

        return result

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "AI 이미지 분석 중 오류가 "
                f"발생했습니다: {error}"
            ),
        ) from error

    finally:

        if temp_path.exists():

            try:
                temp_path.unlink()

            except OSError:
                pass
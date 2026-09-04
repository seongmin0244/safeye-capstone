import json
from pathlib import Path

from app.local.config import (
    FRAME_DIR,
    FRAME_INTERVAL_SEC,
    VIDEO_DIR,
)

from app.local.ollama_client import (
    analyze_image,
)

from app.local.video_processor import (
    clear_frames,
    extract_frames,
)

from app.rag.aggregator import (
    aggregate_frame_results,
)

from app.rag.query_builder import (
    build_search_query,
    normalize_vlm_analysis,
)

from app.rag.regulation_retriever import (
    search_regulations,
)


# ============================================================
# 결과 저장 경로
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

RESULT_DIR = (
    BASE_DIR
    / "data"
    / "results"
)


# ============================================================
# VLM JSON 파싱
# ============================================================

def parse_vlm_json(
    raw_response: str,
) -> dict:
    """
    Ollama가 반환한 JSON 문자열을
    Python dict로 변환한다.
    """

    raw_response = (
        raw_response.strip()
    )

    # ```json ... ``` 형태 대응
    if raw_response.startswith(
        "```"
    ):

        lines = (
            raw_response.splitlines()
        )

        if lines:
            lines = lines[1:]

        if (
            lines
            and lines[-1].strip()
            == "```"
        ):
            lines = lines[:-1]

        raw_response = "\n".join(
            lines
        )

    try:

        return json.loads(
            raw_response
        )

    except json.JSONDecodeError as error:

        raise ValueError(
            "VLM 응답이 올바른 JSON 형식이 아닙니다.\n"
            f"{raw_response}"
        ) from error


# ============================================================
# 프레임 한 장 분석
# ============================================================

def analyze_frame(
    frame_path,
) -> dict:
    """
    프레임 하나를 VLM으로 분석하고
    Aggregator가 사용할 수 있는 형태로 정규화한다.
    """

    raw_response = analyze_image(
        frame_path
    )

    analysis = parse_vlm_json(
        raw_response
    )

    analysis = (
        normalize_vlm_analysis(
            analysis
        )
    )

    analysis["frame"] = (
        frame_path.name
    )

    return analysis


# ============================================================
# 프레임 분석 결과 간단 출력
# ============================================================

def print_frame_summary(
    analysis: dict,
) -> None:
    """
    프레임 전체 JSON 대신
    터미널에는 핵심 정보만 출력한다.
    """

    frame_name = analysis.get(
        "frame",
        "unknown"
    )

    workers = analysis.get(
        "workers",
        []
    )

    hazards = analysis.get(
        "hazards",
        []
    )

    detected_hazards = [
        hazard
        for hazard in hazards
        if hazard.get(
            "detected",
            False
        )
    ]

    print(
        f"[분석 완료] {frame_name}"
    )

    print(
        f"  작업자 수: "
        f"{len(workers)}"
    )

    if not detected_hazards:

        print(
            "  탐지 위험: 없음"
        )

        return

    print(
        "  탐지 위험:"
    )

    for hazard in detected_hazards:

        risk_type = hazard.get(
            "risk_type",
            "UNKNOWN"
        )

        confidence = hazard.get(
            "confidence",
            "LOW"
        )

        evidence = hazard.get(
            "evidence",
            ""
        )

        print(
            f"    - {risk_type} "
            f"({confidence})"
        )

        if evidence:

            print(
                f"      근거: "
                f"{evidence}"
            )


# ============================================================
# 위험에 RAG 결과 연결
# ============================================================

def attach_regulations(
    aggregated_hazards: list[dict],
) -> list[dict]:
    """
    최종적으로 detected=true인 위험에 대해서만
    관련 산업안전 법령을 검색한다.
    """

    results = []

    for hazard in aggregated_hazards:

        if not hazard.get(
            "detected",
            False
        ):
            continue

        risk_type = hazard.get(
            "risk_type",
            "UNKNOWN"
        )

        query = build_search_query(
            hazard
        )

        print()
        print(
            f"[RAG 검색] {risk_type}"
        )

        print(
            f"  검색문: {query}"
        )

        try:

            regulations = (
                search_regulations(
                    query=query,
                    final_top_k=5,
                    per_collection_k=3,
                )
            )

        except Exception as error:

            print(
                f"  RAG 검색 실패: "
                f"{error}"
            )

            regulations = []

        print(
            f"  검색된 법령: "
            f"{len(regulations)}개"
        )

        results.append(
            {
                **hazard,

                "search_query":
                    query,

                "regulations":
                    regulations,
            }
        )

    return results


# ============================================================
# 법령 이름 추출
# ============================================================

def get_regulation_name(
    regulation: dict,
) -> str:
    """
    metadata 구조가 조금 달라도
    가능한 법령명을 찾아 반환한다.
    """

    metadata = regulation.get(
        "metadata",
        {}
    )

    return (
        metadata.get(
            "law_name"
        )
        or metadata.get(
            "document_name"
        )
        or metadata.get(
            "document_title"
        )
        or regulation.get(
            "collection"
        )
        or "법령명 없음"
    )


# ============================================================
# 법령 조항 추출
# ============================================================

def get_article(
    regulation: dict,
) -> str:

    metadata = regulation.get(
        "metadata",
        {}
    )

    article = (
        metadata.get(
            "article"
        )
        or metadata.get(
            "article_number"
        )
        or ""
    )

    article_title = (
        metadata.get(
            "article_title"
        )
        or metadata.get(
            "title"
        )
        or ""
    )

    if article and article_title:

        return (
            f"{article} "
            f"{article_title}"
        )

    if article:
        return article

    if article_title:
        return article_title

    return "조항 정보 없음"


# ============================================================
# 통합 위험 간단 출력
# ============================================================

def print_aggregated_summary(
    aggregated_hazards: list[dict],
) -> None:

    print()
    print("=" * 60)
    print("프레임 통합 위험 분석")
    print("=" * 60)

    detected = [
        hazard
        for hazard in aggregated_hazards
        if hazard.get(
            "detected",
            False
        )
    ]

    if not detected:

        print(
            "최종적으로 확인된 위험이 없습니다."
        )

        return

    for index, hazard in enumerate(
        detected,
        start=1,
    ):

        print()

        print(
            f"[위험 {index}]"
        )

        print(
            f"유형: "
            f"{hazard.get('risk_type')}"
        )

        print(
            f"신뢰도: "
            f"{hazard.get('confidence')}"
        )

        print(
            f"검출 프레임 수: "
            f"{hazard.get('detection_count', 0)}"
        )

        frames = hazard.get(
            "evidence_frames",
            []
        )

        if frames:

            print(
                "검출 프레임: "
                + ", ".join(frames)
            )


# ============================================================
# 최종 결과 간단 출력
# ============================================================

def print_final_summary(
    result: dict,
) -> None:

    print()
    print("=" * 60)
    print("최종 분석 결과")
    print("=" * 60)

    print(
        f"영상: "
        f"{result.get('video')}"
    )

    print(
        f"전체 프레임: "
        f"{result.get('total_frames')}"
    )

    print(
        f"분석 성공: "
        f"{result.get('analyzed_frames')}"
    )

    print(
        f"분석 실패: "
        f"{result.get('failed_frames')}"
    )

    hazards = result.get(
        "hazards",
        []
    )

    if not hazards:

        print()
        print(
            "최종 확인된 위험이 없습니다."
        )

        return

    for index, hazard in enumerate(
        hazards,
        start=1,
    ):

        print()
        print("-" * 60)

        print(
            f"[위험 {index}]"
        )

        print(
            f"위험 유형: "
            f"{hazard.get('risk_type')}"
        )

        print(
            f"신뢰도: "
            f"{hazard.get('confidence')}"
        )

        print(
            f"검출 프레임 수: "
            f"{hazard.get('detection_count', 0)}"
        )

        evidence = hazard.get(
            "evidence",
            []
        )

        if evidence:

            print(
                "판단 근거:"
            )

            for item in evidence[:3]:

                print(
                    f"  - {item}"
                )

        regulations = hazard.get(
            "regulations",
            []
        )

        print()
        print(
            f"관련 법령 "
            f"(상위 {min(3, len(regulations))}개):"
        )

        for law_index, regulation in enumerate(
            regulations[:3],
            start=1,
        ):

            law_name = (
                get_regulation_name(
                    regulation
                )
            )

            article = get_article(
                regulation
            )

            distance = regulation.get(
                "distance"
            )

            print(
                f"  {law_index}. "
                f"{law_name}"
            )

            print(
                f"     {article}"
            )

            if distance is not None:

                print(
                    f"     distance: "
                    f"{distance:.4f}"
                )


# ============================================================
# 전체 JSON 저장
# ============================================================

def save_result(
    result: dict,
) -> Path:
    """
    터미널에는 요약만 출력하고,
    전체 JSON은 파일로 저장한다.
    """

    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    video_name = (
        Path(
            result.get(
                "video",
                "analysis"
            )
        )
        .stem
    )

    output_path = (
        RESULT_DIR
        / f"{video_name}_analysis.json"
    )

    output_path.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return output_path


# ============================================================
# 전체 영상 분석 Pipeline
# ============================================================

def analyze_video(
    video_name: str,
) -> dict:

    video_path = (
        VIDEO_DIR
        / video_name
    )

    if not video_path.exists():

        raise FileNotFoundError(
            f"영상 파일을 찾을 수 없습니다: "
            f"{video_path}"
        )

    print()
    print("=" * 60)
    print("영상 분석 시작")
    print("=" * 60)

    print(
        f"영상: {video_path}"
    )

    # --------------------------------------------------------
    # 기존 프레임 제거
    # --------------------------------------------------------

    clear_frames(
        FRAME_DIR
    )

    # --------------------------------------------------------
    # 영상에서 프레임 추출
    # --------------------------------------------------------

    frames = extract_frames(
        video_path=video_path,
        output_dir=FRAME_DIR,
        interval_sec=FRAME_INTERVAL_SEC,
    )

    print()
    print(
        f"총 {len(frames)}개 "
        f"프레임 추출 완료"
    )

    if not frames:

        raise RuntimeError(
            "영상에서 프레임을 "
            "추출하지 못했습니다."
        )

    # --------------------------------------------------------
    # 프레임 분석
    # --------------------------------------------------------

    frame_results = []

    failed_frame_names = []

    for index, frame_path in enumerate(
        frames,
        start=1,
    ):

        print()
        print(
            f"[{index}/{len(frames)}] "
            f"{frame_path.name} 분석 중..."
        )

        try:

            analysis = analyze_frame(
                frame_path
            )

            frame_results.append(
                analysis
            )

            # 전체 JSON 대신 요약 출력
            print_frame_summary(
                analysis
            )

        except Exception as error:

            failed_frame_names.append(
                frame_path.name
            )

            print(
                f"[프레임 분석 실패] "
                f"{frame_path.name}"
            )

            print(
                f"오류: {error}"
            )

    # --------------------------------------------------------
    # 프레임 결과 통합
    # --------------------------------------------------------

    aggregated_hazards = (
        aggregate_frame_results(
            frame_results,
            min_detection_count=2,
        )
    )

    print_aggregated_summary(
        aggregated_hazards
    )

    # --------------------------------------------------------
    # RAG 연결
    # --------------------------------------------------------

    hazards_with_regulations = (
        attach_regulations(
            aggregated_hazards
        )
    )

    # --------------------------------------------------------
    # 최종 데이터
    # --------------------------------------------------------

    result = {

        "video":
            video_name,

        "total_frames":
            len(frames),

        "analyzed_frames":
            len(frame_results),

        "failed_frames":
            len(failed_frame_names),

        "failed_frame_names":
            failed_frame_names,

        # 전체 데이터는 유지
        "frames":
            frame_results,

        "aggregated_hazards":
            aggregated_hazards,

        "hazards":
            hazards_with_regulations,
    }

    return result


# ============================================================
# 실행
# ============================================================

if __name__ == "__main__":

    result = analyze_video(
        "test.mp4"
    )

    # 전체 JSON 파일 저장
    output_path = save_result(
        result
    )

    # 터미널에는 요약 결과만 출력
    print_final_summary(
        result
    )

    print()
    print(
        f"전체 JSON 저장 위치: "
        f"{output_path}"
    )
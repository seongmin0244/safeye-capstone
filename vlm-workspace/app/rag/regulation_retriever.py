import re
from pathlib import Path
from typing import Any

import chromadb

from sentence_transformers import (
    SentenceTransformer,
)


# ============================================================
# 프로젝트 경로
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    .parent
)

CHROMA_PATH = (
    BASE_DIR
    / "data"
    / "rag"
    / "chroma_db"
)


# ============================================================
# 임베딩 모델
# ============================================================

EMBEDDING_MODEL = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)


# ============================================================
# ChromaDB Collection
# ============================================================

COLLECTION_NAMES = [
    "osh_law",
    "osh_decree",
    "osh_enforcement_rule",
    "osh_safety_rule",
]


# ============================================================
# 위험 유형
# ============================================================

VALID_RISK_TYPES = {
    "NO_HELMET",
    "FALL_HAZARD",
    "BLOCKED_PATH",
}


# ============================================================
# 위험 유형별 기본 규칙
# ============================================================

RISK_RULES = {

    # --------------------------------------------------------
    # 안전모 미착용
    # --------------------------------------------------------

    "NO_HELMET": {

        "positive_keywords": [
            "안전모",
            "보호구",
            "보호구의 지급",
            "보호구 착용",
            "착용",
            "머리",
            "낙하",
            "비래",
        ],

        "strong_keywords": [
            "안전모",
            "보호구의 지급",
        ],

        "priority_targets": [
            {
                "collection": "osh_safety_rule",
                "article": "제32조",
            },
        ],

        "negative_keywords": [
            "밀폐공간",
            "금형",
            "프레스",
            "터널",
            "공정안전보고서",
            "출입구의 임의잠김",
        ],
    },


    # --------------------------------------------------------
    # 추락 위험
    # --------------------------------------------------------

    "FALL_HAZARD": {

        "positive_keywords": [
            "추락",
            "작업발판",
            "안전난간",
            "개구부",
            "덮개",
            "안전대",
            "추락방호망",
            "부착설비",
            "고소작업",
            "높은 장소",
        ],

        "strong_keywords": [
            "추락의 방지",
            "개구부",
            "안전난간",
            "안전대",
            "부착설비",
            "작업발판",
            "추락방호망",
        ],

        "priority_targets": [
            {
                "collection": "osh_safety_rule",
                "article": "제42조",
            },
            {
                "collection": "osh_safety_rule",
                "article": "제43조",
            },
            {
                "collection": "osh_safety_rule",
                "article": "제44조",
            },
        ],

        "negative_keywords": [
            "금형조정",
            "금형",
            "프레스",
            "밀폐공간",
            "공정안전보고서",
            "낙반",
            "출수",
        ],
    },


    # --------------------------------------------------------
    # 통로 장애
    # --------------------------------------------------------

    "BLOCKED_PATH": {

        "positive_keywords": [
            "통로",
            "통로의 설치",
            "통행",
            "작업장 통로",
            "장애물",
            "출입구",
            "작업장의 출입구",
            "이동",
        ],

        "strong_keywords": [
            "통로의 설치",
            "작업장의 출입구",
            "통로",
            "통행",
        ],

        "priority_targets": [
            {
                "collection": "osh_safety_rule",
                "article": "제22조",
            },
            {
                "collection": "osh_safety_rule",
                "article": "제11조",
            },
        ],

        "negative_keywords": [
            "밀폐공간",
            "임의잠김",
            "인원의 점검",
            "금형",
            "프레스",
            "터널",
            "잠김 방지",
        ],
    },
}


# ============================================================
# 세부 상황별 조항 규칙
#
# 같은 FALL_HAZARD라도
# 실제 상황에 따라 가장 직접적인 조항을 구분한다.
# ============================================================

SCENARIO_RULES = {

    "FALL_HAZARD": [

        # ----------------------------------------------------
        # 제43조
        # 개구부 / 난간 / 덮개
        # ----------------------------------------------------

        {
            "name": "OPENING_GUARD",

            "query_keywords": [
                "개구부",
                "안전난간",
                "난간",
                "덮개",
                "작업발판 끝",
            ],

            "targets": [
                {
                    "collection": "osh_safety_rule",
                    "article": "제43조",
                },
            ],

            "bonus": 4.0,
        },


        # ----------------------------------------------------
        # 제44조
        # 안전대 부착설비
        # ----------------------------------------------------

        {
            "name": "SAFETY_BELT_ANCHOR",

            "query_keywords": [
                "안전대",
                "부착설비",
                "걸이",
                "걸 곳",
                "안전대 부착",
            ],

            "targets": [
                {
                    "collection": "osh_safety_rule",
                    "article": "제44조",
                },
            ],

            "bonus": 4.0,
        },


        # ----------------------------------------------------
        # 제42조
        # 일반 추락 / 작업발판 / 추락방호망
        # ----------------------------------------------------

        {
            "name": "GENERAL_FALL_PREVENTION",

            "query_keywords": [
                "작업발판",
                "추락방호망",
                "방호망",
                "높은 장소",
                "고소작업",
            ],

            "targets": [
                {
                    "collection": "osh_safety_rule",
                    "article": "제42조",
                },
            ],

            # 제43 / 제44보다 조금 낮게 설정
            # 세부 상황이 명확하면 더 구체적인 조항을 우선하기 위함
            "bonus": 2.0,
        },
    ],


    "BLOCKED_PATH": [

        {
            "name": "PASSAGE_OBSTRUCTION",

            "query_keywords": [
                "통로",
                "통행",
                "장애물",
                "적치",
                "자재",
                "막혀",
                "방해",
            ],

            "targets": [
                {
                    "collection": "osh_safety_rule",
                    "article": "제22조",
                },
            ],

            "bonus": 4.0,
        },


        {
            "name": "WORKPLACE_ENTRANCE",

            "query_keywords": [
                "출입구",
                "출입문",
                "출입",
            ],

            "targets": [
                {
                    "collection": "osh_safety_rule",
                    "article": "제11조",
                },
            ],

            "bonus": 3.0,
        },
    ],


    "NO_HELMET": [

        {
            "name": "NO_SAFETY_HELMET",

            "query_keywords": [
                "안전모",
                "헬멧",
                "머리 보호",
                "미착용",
                "착용하지",
            ],

            "targets": [
                {
                    "collection": "osh_safety_rule",
                    "article": "제32조",
                },
            ],

            "bonus": 4.0,
        },
    ],
}


# ============================================================
# Risk Type 마커
# ============================================================

RISK_MARKER_PATTERN = re.compile(
    r"\[RISK_TYPE="
    r"(NO_HELMET|FALL_HAZARD|BLOCKED_PATH)"
    r"\]"
)


# ============================================================
# 임베딩 모델
# ============================================================

print(
    f"[RAG] 임베딩 모델 로딩: "
    f"{EMBEDDING_MODEL}"
)

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL
)


# ============================================================
# ChromaDB
# ============================================================

if not CHROMA_PATH.exists():

    raise FileNotFoundError(
        "ChromaDB를 찾을 수 없습니다.\n"
        f"경로: {CHROMA_PATH}"
    )


client = chromadb.PersistentClient(
    path=str(CHROMA_PATH)
)


# ============================================================
# Collection 목록
# ============================================================

def get_available_collections() -> list[str]:

    return [
        collection.name
        for collection
        in client.list_collections()
    ]


# ============================================================
# Risk Type 추출
# ============================================================

def extract_risk_type(
    query: str,
) -> tuple[str | None, str]:

    match = RISK_MARKER_PATTERN.search(
        query
    )

    if not match:

        return (
            None,
            query.strip(),
        )

    risk_type = match.group(1)

    clean_query = (
        RISK_MARKER_PATTERN.sub(
            "",
            query
        )
        .strip()
    )

    return (
        risk_type,
        clean_query,
    )


# ============================================================
# Query 임베딩
# ============================================================

def embed_query(
    query: str,
) -> list[float]:

    embedding = embedding_model.encode(
        query,
        normalize_embeddings=True,
    )

    return embedding.tolist()


# ============================================================
# Document 임베딩
# ============================================================

def embed_document(
    document: str,
) -> list[float]:

    embedding = embedding_model.encode(
        document,
        normalize_embeddings=True,
    )

    return embedding.tolist()


# ============================================================
# Cosine Distance
# ============================================================

def cosine_distance(
    vector_a: list[float],
    vector_b: list[float],
) -> float:

    similarity = sum(
        a * b
        for a, b
        in zip(
            vector_a,
            vector_b,
        )
    )

    return (
        1.0
        - similarity
    )


# ============================================================
# Vector Search
# ============================================================

def search_collection(
    collection_name: str,
    query_embedding: list[float],
    top_k: int = 12,
) -> list[dict[str, Any]]:

    collection = client.get_collection(
        name=collection_name
    )

    count = collection.count()

    if count == 0:

        return []

    result = collection.query(

        query_embeddings=[
            query_embedding
        ],

        n_results=min(
            top_k,
            count,
        ),

        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    ids = result.get(
        "ids",
        [[]]
    )[0] or []

    documents = result.get(
        "documents",
        [[]]
    )[0] or []

    metadatas = result.get(
        "metadatas",
        [[]]
    )[0] or []

    distances = result.get(
        "distances",
        [[]]
    )[0] or []

    results = []

    for index, item_id in enumerate(ids):

        results.append(
            {
                "id":
                    item_id,

                "collection":
                    collection_name,

                "document":
                    documents[index],

                "metadata":
                    metadatas[index] or {},

                "distance":
                    float(
                        distances[index]
                    ),

                "candidate_source":
                    "vector",
            }
        )

    return results


# ============================================================
# Priority Candidate 직접 추가
# ============================================================

def fetch_priority_candidates(
    risk_type: str | None,
    query_embedding: list[float],
) -> list[dict[str, Any]]:

    if risk_type not in RISK_RULES:

        return []

    results = []

    for target in (
        RISK_RULES[
            risk_type
        ]["priority_targets"]
    ):

        collection_name = target[
            "collection"
        ]

        article = target[
            "article"
        ]

        collection = client.get_collection(
            name=collection_name
        )

        response = collection.get(

            where={
                "article": article
            },

            include=[
                "documents",
                "metadatas",
            ],
        )

        ids = response.get(
            "ids",
            []
        ) or []

        documents = response.get(
            "documents",
            []
        ) or []

        metadatas = response.get(
            "metadatas",
            []
        ) or []

        for index, item_id in enumerate(ids):

            document = documents[index]

            document_embedding = (
                embed_document(
                    document
                )
            )

            distance = cosine_distance(
                query_embedding,
                document_embedding,
            )

            results.append(
                {
                    "id":
                        item_id,

                    "collection":
                        collection_name,

                    "document":
                        document,

                    "metadata":
                        metadatas[index] or {},

                    "distance":
                        float(distance),

                    "candidate_source":
                        "priority",
                }
            )

    return results


# ============================================================
# Candidate 병합
# ============================================================

def merge_candidates(
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    merged = {}

    for candidate in candidates:

        key = (
            candidate.get(
                "collection"
            ),
            candidate.get(
                "id"
            ),
        )

        if key not in merged:

            merged[key] = candidate

            continue

        # priority 경로로도 발견된 경우 표시
        if (
            candidate.get(
                "candidate_source"
            )
            == "priority"
        ):

            merged[
                key
            ][
                "candidate_source"
            ] = "priority"

    return list(
        merged.values()
    )


# ============================================================
# Candidate 전체 텍스트
# ============================================================

def build_candidate_text(
    candidate: dict[str, Any],
) -> str:

    metadata = candidate.get(
        "metadata",
        {}
    )

    return (
        f"{metadata.get('law_name', '')} "
        f"{metadata.get('article', '')} "
        f"{metadata.get('article_title', '')} "
        f"{candidate.get('document', '')}"
    ).lower()


# ============================================================
# Vector Score
# ============================================================

def distance_to_score(
    distance: float | None,
) -> float:

    if distance is None:

        return 0.0

    return (
        1.0
        / (
            1.0
            + max(
                distance,
                0
            )
        )
    )


# ============================================================
# 정확한 Priority Target 확인
# ============================================================

def is_priority_target(
    candidate: dict[str, Any],
    risk_type: str,
) -> bool:

    collection = candidate.get(
        "collection"
    )

    article = (
        candidate
        .get(
            "metadata",
            {}
        )
        .get(
            "article"
        )
    )

    for target in (
        RISK_RULES[
            risk_type
        ][
            "priority_targets"
        ]
    ):

        if (
            target["collection"]
            == collection

            and

            target["article"]
            == article
        ):

            return True

    return False


# ============================================================
# 세부 Scenario Score 계산
# ============================================================

def calculate_scenario_bonus(
    candidate: dict[str, Any],
    risk_type: str | None,
    query_text: str,
) -> tuple[float, list[str]]:

    if risk_type not in SCENARIO_RULES:

        return (
            0.0,
            [],
        )

    collection = candidate.get(
        "collection"
    )

    article = (
        candidate
        .get(
            "metadata",
            {}
        )
        .get(
            "article",
            ""
        )
    )

    query_lower = query_text.lower()

    total_bonus = 0.0

    matched_scenarios = []

    for scenario in (
        SCENARIO_RULES[
            risk_type
        ]
    ):

        # Query에서 실제 등장한 세부 키워드
        query_matches = [
            keyword

            for keyword
            in scenario[
                "query_keywords"
            ]

            if keyword.lower()
            in query_lower
        ]

        if not query_matches:

            continue

        for target in scenario[
            "targets"
        ]:

            if (
                target[
                    "collection"
                ]
                == collection

                and

                target[
                    "article"
                ]
                == article
            ):

                # 해당 scenario 키워드가 여러 개 나오면
                # 보너스 소폭 증가
                keyword_multiplier = (
                    1.0
                    + (
                        min(
                            len(
                                query_matches
                            ),
                            3,
                        )
                        - 1
                    )
                    * 0.20
                )

                bonus = (
                    scenario[
                        "bonus"
                    ]
                    * keyword_multiplier
                )

                total_bonus += bonus

                matched_scenarios.append(
                    scenario[
                        "name"
                    ]
                )

    return (
        total_bonus,
        matched_scenarios,
    )


# ============================================================
# Reranking
# ============================================================

def rerank_candidate(
    candidate: dict[str, Any],
    risk_type: str | None,
    query_text: str,
) -> dict[str, Any]:

    vector_score = distance_to_score(
        candidate.get(
            "distance"
        )
    )

    if risk_type not in RISK_RULES:

        return {
            **candidate,

            "vector_score":
                round(
                    vector_score,
                    6
                ),

            "rerank_score":
                round(
                    vector_score,
                    6
                ),

            "matched_keywords":
                [],

            "matched_scenarios":
                [],

            "scenario_bonus":
                0.0,

            "priority_target":
                False,

            "domain_relevant":
                True,
        }

    rule = RISK_RULES[
        risk_type
    ]

    metadata = candidate.get(
        "metadata",
        {}
    )

    article_title = (
        metadata.get(
            "article_title",
            ""
        )
        or ""
    )

    article_title_lower = (
        article_title.lower()
    )

    candidate_text = (
        build_candidate_text(
            candidate
        )
    )

    query_lower = (
        query_text.lower()
    )

    # ========================================================
    # 1. Vector similarity
    #
    # 이전보다 비중을 낮춘다.
    # ========================================================

    score = (
        vector_score
        * 1.5
    )


    # ========================================================
    # 2. Query와 Document 양쪽에 있는 키워드만 가점
    #
    # 기존 문제:
    # 문서 안에 단어가 있기만 해도 점수를 받음
    #
    # 수정:
    # 실제 Query에도 등장해야 가점
    # ========================================================

    matched_keywords = []

    for keyword in rule[
        "positive_keywords"
    ]:

        keyword_lower = (
            keyword.lower()
        )

        if (
            keyword_lower
            in query_lower

            and

            keyword_lower
            in candidate_text
        ):

            matched_keywords.append(
                keyword
            )

            score += 0.40


    # ========================================================
    # 3. Query keyword + Article Title 정확 일치
    # ========================================================

    title_matches = []

    for keyword in rule[
        "strong_keywords"
    ]:

        keyword_lower = (
            keyword.lower()
        )

        if (
            keyword_lower
            in query_lower

            and

            keyword_lower
            in article_title_lower
        ):

            title_matches.append(
                keyword
            )

            score += 2.0


    # ========================================================
    # 4. 기본 Priority Target
    #
    # 이전 +3.0에서 +1.0으로 감소.
    #
    # 제42/43/44가 모두 후보군에는 유지되지만
    # 구체적 상황에 따른 Scenario 점수가
    # 순위를 결정하게 한다.
    # ========================================================

    priority_target = (
        is_priority_target(
            candidate,
            risk_type,
        )
    )

    if priority_target:

        score += 1.0


    # ========================================================
    # 5. 구체적인 현장 Scenario
    #
    # 이번 개선의 핵심.
    # ========================================================

    (
        scenario_bonus,
        matched_scenarios,
    ) = calculate_scenario_bonus(
        candidate,
        risk_type,
        query_text,
    )

    score += (
        scenario_bonus
    )


    # ========================================================
    # 6. 안전보건기준 규칙 가점
    # ========================================================

    if (
        candidate.get(
            "collection"
        )
        == "osh_safety_rule"
    ):

        score += 0.25


    # ========================================================
    # 7. 무관한 분야 감점
    # ========================================================

    penalty_keywords = []

    for keyword in rule[
        "negative_keywords"
    ]:

        if keyword.lower() in candidate_text:

            penalty_keywords.append(
                keyword
            )

            score -= 1.0


    # ========================================================
    # 8. 관련성
    # ========================================================

    domain_relevant = bool(

        priority_target

        or

        matched_keywords

        or

        title_matches

        or

        matched_scenarios
    )

    if not domain_relevant:

        score -= 1.0


    return {
        **candidate,

        "vector_score":
            round(
                vector_score,
                6
            ),

        "rerank_score":
            round(
                score,
                6
            ),

        "matched_keywords":
            list(
                dict.fromkeys(
                    matched_keywords
                )
            ),

        "title_matches":
            list(
                dict.fromkeys(
                    title_matches
                )
            ),

        "matched_scenarios":
            matched_scenarios,

        "scenario_bonus":
            round(
                scenario_bonus,
                4
            ),

        "penalty_keywords":
            list(
                dict.fromkeys(
                    penalty_keywords
                )
            ),

        "priority_target":
            priority_target,

        "domain_relevant":
            domain_relevant,
    }


# ============================================================
# 중복 제거
# ============================================================

def remove_duplicates(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    seen = set()

    unique = []

    for result in results:

        metadata = result.get(
            "metadata",
            {}
        )

        key = (
            metadata.get(
                "law_name"
            ),
            metadata.get(
                "article"
            ),
        )

        if key in seen:

            continue

        seen.add(key)

        unique.append(
            result
        )

    return unique


# ============================================================
# 전체 검색
# ============================================================

def search_regulations(
    query: str,
    final_top_k: int = 5,
    per_collection_k: int = 3,
) -> list[dict[str, Any]]:

    query = query.strip()

    if not query:

        return []

    # --------------------------------------------------------
    # Risk Type
    # --------------------------------------------------------

    (
        risk_type,
        clean_query,
    ) = extract_risk_type(
        query
    )

    print(
        f"[RAG] 위험 유형: "
        f"{risk_type or 'UNKNOWN'}"
    )


    # --------------------------------------------------------
    # Query Embedding
    # --------------------------------------------------------

    query_embedding = (
        embed_query(
            clean_query
        )
    )


    # --------------------------------------------------------
    # Vector 후보
    # --------------------------------------------------------

    candidate_per_collection = max(
        per_collection_k,
        12,
    )

    candidates = []

    for collection_name in (
        COLLECTION_NAMES
    ):

        try:

            candidates.extend(

                search_collection(
                    collection_name,
                    query_embedding,
                    candidate_per_collection,
                )
            )

        except Exception as error:

            print(
                f"[RAG 검색 오류] "
                f"{collection_name}: "
                f"{error}"
            )


    # --------------------------------------------------------
    # Priority 후보 추가
    # --------------------------------------------------------

    candidates.extend(

        fetch_priority_candidates(
            risk_type,
            query_embedding,
        )
    )


    # --------------------------------------------------------
    # 중복 병합
    # --------------------------------------------------------

    candidates = (
        merge_candidates(
            candidates
        )
    )


    # --------------------------------------------------------
    # Query-aware Reranking
    # --------------------------------------------------------

    reranked = [

        rerank_candidate(
            candidate,
            risk_type,
            clean_query,
        )

        for candidate
        in candidates
    ]


    reranked.sort(

        key=lambda item: (
            item.get(
                "rerank_score",
                -9999
            )
        ),

        reverse=True,
    )


    reranked = (
        remove_duplicates(
            reranked
        )
    )


    # --------------------------------------------------------
    # 관련 후보 우선
    # --------------------------------------------------------

    relevant = [

        result

        for result
        in reranked

        if result.get(
            "domain_relevant",
            False
        )
    ]

    fallback = [

        result

        for result
        in reranked

        if not result.get(
            "domain_relevant",
            False
        )
    ]


    final_results = (
        relevant
        + fallback
    )

    return (
        final_results[
            :final_top_k
        ]
    )


# ============================================================
# 테스트 출력
# ============================================================

def print_search_results(
    results: list[dict[str, Any]],
) -> None:

    if not results:

        print(
            "관련 법령을 찾지 못했습니다."
        )

        return

    print()
    print("=" * 60)
    print("관련 산업안전 법령")
    print("=" * 60)


    for index, result in enumerate(
        results,
        start=1,
    ):

        metadata = result.get(
            "metadata",
            {}
        )

        law_name = metadata.get(
            "law_name",
            "법령명 없음"
        )

        article = metadata.get(
            "article",
            ""
        )

        article_title = metadata.get(
            "article_title",
            ""
        )

        print()
        print(
            f"[{index}] {law_name}"
        )

        print(
            f"조항: "
            f"{article} "
            f"{article_title}"
        )

        print(
            f"Collection: "
            f"{result.get('collection')}"
        )

        distance = result.get(
            "distance"
        )

        if distance is not None:

            print(
                f"Vector distance: "
                f"{distance:.4f}"
            )

        print(
            f"Rerank score: "
            f"{result.get('rerank_score', 0):.4f}"
        )


        matched_keywords = (
            result.get(
                "matched_keywords",
                []
            )
        )

        if matched_keywords:

            print(
                "Query 일치 키워드: "
                + ", ".join(
                    matched_keywords
                )
            )


        title_matches = (
            result.get(
                "title_matches",
                []
            )
        )

        if title_matches:

            print(
                "조문 제목 일치: "
                + ", ".join(
                    title_matches
                )
            )


        scenarios = result.get(
            "matched_scenarios",
            []
        )

        if scenarios:

            print(
                "상황 매칭: "
                + ", ".join(
                    scenarios
                )
            )

            print(
                f"상황 가점: "
                f"+{result.get('scenario_bonus', 0):.2f}"
            )


        if result.get(
            "priority_target",
            False
        ):

            print(
                "핵심 조항: YES"
            )

        print(
            f"후보 출처: "
            f"{result.get('candidate_source')}"
        )


# ============================================================
# 직접 실행
# ============================================================

def main() -> None:

    print()
    print(
        f"ChromaDB 경로: "
        f"{CHROMA_PATH}"
    )

    print(
        "사용 가능한 Collection:"
    )

    for name in (
        get_available_collections()
    ):

        print(
            f"- {name}"
        )


    while True:

        print()

        query = input(
            "검색할 위험 상황 "
            "(종료: q): "
        ).strip()

        if query.lower() == "q":

            break

        if not query:

            continue


        results = search_regulations(
            query=query,
            final_top_k=3,
            per_collection_k=12,
        )

        print_search_results(
            results
        )


if __name__ == "__main__":

    main()
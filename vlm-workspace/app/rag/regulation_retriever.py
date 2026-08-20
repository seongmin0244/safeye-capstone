from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer


# ============================================================
# 경로 및 모델 설정
# ============================================================

# 현재 파일:
# vlm-workspace/app/rag/regulation_retriever.py
#
# parent        -> rag
# parent.parent -> app
# parent.parent.parent -> vlm-workspace
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

EMBEDDING_MODEL = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)


# ============================================================
# 검색 대상 ChromaDB Collection
# ============================================================

COLLECTION_NAMES = [
    "osh_law",
    "osh_decree",
    "osh_enforcement_rule",
    "osh_safety_rule",
]


# ============================================================
# Embedding Model
# ============================================================

print(
    f"[RAG] 임베딩 모델 로딩: "
    f"{EMBEDDING_MODEL}"
)

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL
)


# ============================================================
# ChromaDB 연결
# ============================================================

if not CHROMA_PATH.exists():
    raise FileNotFoundError(
        "ChromaDB를 찾을 수 없습니다.\n"
        f"경로: {CHROMA_PATH}\n"
        "먼저 scripts/build_vector_db.py를 실행하세요."
    )


client = chromadb.PersistentClient(
    path=str(CHROMA_PATH)
)


# ============================================================
# 현재 Collection 확인
# ============================================================

def get_available_collections() -> list[str]:
    """
    현재 ChromaDB에 존재하는 collection 이름을 반환한다.
    """

    collections = (
        client.list_collections()
    )

    return [
        collection.name
        for collection in collections
    ]


# ============================================================
# 검색문 Embedding
# ============================================================

def embed_query(
    query: str,
) -> list[float]:
    """
    검색 문장을 embedding vector로 변환한다.
    """

    query = query.strip()

    if not query:
        raise ValueError(
            "검색 문장이 비어 있습니다."
        )

    embedding = (
        embedding_model.encode(
            query,
            normalize_embeddings=True,
        )
    )

    return embedding.tolist()


# ============================================================
# 단일 Collection 검색
# ============================================================

def search_collection(
    collection_name: str,
    query_embedding: list[float],
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """
    하나의 ChromaDB collection에서 검색한다.
    """

    available = (
        get_available_collections()
    )

    if collection_name not in available:
        print(
            f"[RAG 경고] "
            f"Collection 없음: {collection_name}"
        )

        return []

    collection = (
        client.get_collection(
            name=collection_name
        )
    )

    count = collection.count()

    if count == 0:
        print(
            f"[RAG 경고] "
            f"빈 Collection: {collection_name}"
        )

        return []

    # DB에 들어있는 개수보다 큰 n_results를
    # 요청하지 않도록 제한
    n_results = min(
        top_k,
        count,
    )

    result = collection.query(
        query_embeddings=[
            query_embedding
        ],
        n_results=n_results,
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    results: list[dict[str, Any]] = []

    ids = (
        result.get("ids", [[]])[0]
        or []
    )

    documents = (
        result.get("documents", [[]])[0]
        or []
    )

    metadatas = (
        result.get("metadatas", [[]])[0]
        or []
    )

    distances = (
        result.get("distances", [[]])[0]
        or []
    )

    for index, item_id in enumerate(
        ids
    ):

        document = (
            documents[index]
            if index < len(documents)
            else ""
        )

        metadata = (
            metadatas[index]
            if index < len(metadatas)
            else {}
        )

        distance = (
            distances[index]
            if index < len(distances)
            else None
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
                    metadata or {},

                "distance":
                    float(distance)
                    if distance is not None
                    else None,
            }
        )

    return results


# ============================================================
# 전체 법령 검색
# ============================================================

def search_regulations(
    query: str,
    final_top_k: int = 5,
    per_collection_k: int = 3,
) -> list[dict[str, Any]]:
    """
    모든 산업안전 법령 collection을 검색하고,
    유사도가 높은 결과 final_top_k개를 반환한다.

    Parameters
    ----------
    query:
        VLM/Aggregator에서 만들어진 위험 상황 검색 문장

    final_top_k:
        최종적으로 반환할 법령 개수

    per_collection_k:
        각 collection에서 가져올 후보 개수
    """

    query = query.strip()

    if not query:
        return []

    # --------------------------------
    # 1. 검색문 embedding
    # --------------------------------

    query_embedding = (
        embed_query(
            query
        )
    )

    all_results: list[
        dict[str, Any]
    ] = []

    # --------------------------------
    # 2. 각 법령 collection 검색
    # --------------------------------

    for collection_name in (
        COLLECTION_NAMES
    ):

        try:

            collection_results = (
                search_collection(
                    collection_name=
                        collection_name,

                    query_embedding=
                        query_embedding,

                    top_k=
                        per_collection_k,
                )
            )

            all_results.extend(
                collection_results
            )

        except Exception as error:

            print(
                f"[RAG 검색 오류] "
                f"{collection_name}: "
                f"{error}"
            )

    # --------------------------------
    # 3. distance 기준 정렬
    #
    # ChromaDB의 distance는 일반적으로
    # 낮을수록 더 유사한 결과
    # --------------------------------

    all_results.sort(
        key=lambda item: (
            item["distance"]
            if item["distance"]
            is not None
            else float("inf")
        )
    )

    # --------------------------------
    # 4. 중복 조항 제거
    # --------------------------------

    unique_results = []

    seen = set()

    for result in all_results:

        metadata = result.get(
            "metadata",
            {}
        )

        law_name = (
            metadata.get("law_name")
            or metadata.get(
                "document_name"
            )
            or metadata.get("law")
            or ""
        )

        article = (
            metadata.get("article")
            or metadata.get(
                "article_number"
            )
            or ""
        )

        # 법령명 + 조항으로 중복 판정
        duplicate_key = (
            law_name,
            article,
            result.get("document", ""),
        )

        if duplicate_key in seen:
            continue

        seen.add(
            duplicate_key
        )

        unique_results.append(
            result
        )

        if (
            len(unique_results)
            >= final_top_k
        ):
            break

    return unique_results


# ============================================================
# 사람이 보기 위한 출력 함수
# ============================================================

def print_search_results(
    results: list[dict[str, Any]],
) -> None:
    """
    터미널 테스트용 검색 결과 출력.
    """

    if not results:

        print(
            "\n관련 법령을 찾지 못했습니다."
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

        law_name = (
            metadata.get("law_name")
            or metadata.get(
                "document_name"
            )
            or metadata.get(
                "document_title"
            )
            or "법령명 없음"
        )

        article = (
            metadata.get("article")
            or metadata.get(
                "article_number"
            )
            or ""
        )

        article_title = (
            metadata.get(
                "article_title"
            )
            or ""
        )

        distance = result.get(
            "distance"
        )

        print()
        print(
            f"[{index}] "
            f"{law_name}"
        )

        if article:
            print(
                f"조항: "
                f"{article} "
                f"{article_title}"
            )

        print(
            f"Collection: "
            f"{result['collection']}"
        )

        if distance is not None:
            print(
                f"Distance: "
                f"{distance:.4f}"
            )

        document = result.get(
            "document",
            ""
        )

        if document:
            print(
                f"내용: {document}"
            )


# ============================================================
# 단독 RAG 테스트
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

    available = (
        get_available_collections()
    )

    for name in available:
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

        print()
        print(
            f"검색 중: {query}"
        )

        results = (
            search_regulations(
                query=query,
                final_top_k=5,
                per_collection_k=3,
            )
        )

        print_search_results(
            results
        )


if __name__ == "__main__":
    main()
from pathlib import Path

import chromadb
from sentence_transformers import (
    SentenceTransformer
)


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


COLLECTION_NAMES = [
    "osh_law",
    "osh_decree",
    "osh_enforcement_rule",
    "osh_safety_rule",
]


model = SentenceTransformer(
    EMBEDDING_MODEL
)

client = chromadb.PersistentClient(
    path=str(CHROMA_PATH)
)


def search_one_collection(
    collection_name: str,
    query_embedding,
    top_k: int = 3,
) -> list[dict]:

    try:
        collection = client.get_collection(
            collection_name
        )

    except Exception:
        return []

    count = collection.count()

    if count == 0:
        return []

    actual_k = min(
        top_k,
        count
    )

    result = collection.query(
        query_embeddings=query_embedding,
        n_results=actual_k,
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    items = []

    for index in range(
        len(result["ids"][0])
    ):

        items.append(
            {
                "id":
                    result["ids"][0][
                        index
                    ],

                "document":
                    result[
                        "documents"
                    ][0][index],

                "metadata":
                    result[
                        "metadatas"
                    ][0][index],

                "distance":
                    float(
                        result[
                            "distances"
                        ][0][index]
                    ),

                "collection":
                    collection_name,
            }
        )

    return items


def search_regulations(
    query: str,
    final_top_k: int = 5,
    per_collection_k: int = 3,
) -> list[dict]:

    query_embedding = model.encode(
        [query],
        normalize_embeddings=True,
    ).tolist()

    all_results = []

    for collection_name in (
        COLLECTION_NAMES
    ):

        results = (
            search_one_collection(
                collection_name,
                query_embedding,
                top_k=per_collection_k,
            )
        )

        all_results.extend(results)

    # cosine distance는 작을수록 유사
    all_results.sort(
        key=lambda item:
        item["distance"]
    )

    return all_results[
        :final_top_k
    ]


def main():

    while True:

        query = input(
            "\n검색할 위험 상황 "
            "(종료: q): "
        ).strip()

        if query.lower() == "q":
            break

        results = search_regulations(
            query=query,
            final_top_k=5,
            per_collection_k=3,
        )

        print("\n검색 결과")

        for index, result in enumerate(
            results,
            start=1
        ):

            metadata = (
                result["metadata"]
            )

            print()
            print(
                f"[{index}위]"
            )

            print(
                f"컬렉션: "
                f"{result['collection']}"
            )

            print(
                f"법령: "
                f"{metadata['law_name']}"
            )

            print(
                f"조항: "
                f"{metadata['article']} "
                f"{metadata['article_title']}"
            )

            print(
                f"거리: "
                f"{result['distance']:.4f}"
            )

            print(
                "내용:"
            )

            print(
                result["document"][:500]
            )


if __name__ == "__main__":
    main()
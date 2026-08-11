from pathlib import Path
import json

import chromadb
from sentence_transformers import SentenceTransformer


# vlm-workspace/
BASE_DIR = Path(__file__).resolve().parent.parent

CHROMA_PATH = (
    BASE_DIR
    / "data"
    / "rag"
    / "chroma_db"
)

JSONL_PATH = (
    BASE_DIR
    / "data"
    / "rag"
    / "parsed"
    / "regulations.jsonl"
)



EMBEDDING_MODEL = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)

# ==========================================
# document_type -> collection 이름
# ==========================================

COLLECTION_MAP = {
    "LAW": "osh_law",
    "ENFORCEMENT_DECREE": "osh_decree",
    "ENFORCEMENT_RULE": "osh_enforcement_rule",
    "SAFETY_REGULATION": "osh_safety_rule",
}


def load_records() -> list[dict]:
    records = []

    with JSONL_PATH.open(
        "r",
        encoding="utf-8"
    ) as file:

        for line_number, line in enumerate(
            file,
            start=1
        ):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
                records.append(record)

            except json.JSONDecodeError as error:
                raise ValueError(
                    f"{line_number}번째 줄의 JSON이 잘못되었습니다."
                ) from error

    return records


def build_embedding_text(record: dict) -> str:
    """
    단순 본문만 임베딩하지 않고,
    법령명 + 조문 제목 + 본문을 함께 넣는다.
    """

    return (
        f"법령명: {record['law_name']}\n"
        f"조항: {record['article']} "
        f"{record.get('article_title', '')}\n"
        f"본문: {record['content']}"
    )


def get_collection_name(
    record: dict
) -> str | None:

    document_type = record.get(
        "document_type"
    )

    return COLLECTION_MAP.get(
        document_type
    )


def main():

    records = load_records()

    print(
        f"전체 조문 수: {len(records)}"
    )

    # ======================================
    # 종류별 분리
    # ======================================

    grouped_records = {
        collection_name: []
        for collection_name
        in COLLECTION_MAP.values()
    }

    skipped_records = []

    for record in records:

        collection_name = (
            get_collection_name(record)
        )

        if collection_name is None:
            skipped_records.append(record)
            continue

        grouped_records[
            collection_name
        ].append(record)

    print("\n문서 종류별 조문 수")

    for name, items in grouped_records.items():
        print(
            f"{name}: {len(items)}개"
        )

    if skipped_records:
        print(
            f"분류되지 않은 조문: "
            f"{len(skipped_records)}개"
        )

    # ======================================
    # 모델 로드
    # ======================================

    print(
        "\n임베딩 모델 로딩 중..."
    )

    model = SentenceTransformer(
        EMBEDDING_MODEL
    )

    # ======================================
    # Chroma 초기화
    # ======================================

    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH)
    )

    # 기존 컬렉션 삭제
    for collection_name in (
        COLLECTION_MAP.values()
    ):

        try:
            client.delete_collection(
                collection_name
            )

            print(
                f"기존 컬렉션 삭제: "
                f"{collection_name}"
            )

        except Exception:
            pass

    # ======================================
    # 컬렉션별 저장
    # ======================================

    for (
        collection_name,
        collection_records
    ) in grouped_records.items():

        if not collection_records:
            print(
                f"\n{collection_name}: "
                f"데이터 없음 → 건너뜀"
            )
            continue

        print()
        print(
            "=" * 50
        )

        print(
            f"컬렉션 구축: "
            f"{collection_name}"
        )

        print(
            f"조문 수: "
            f"{len(collection_records)}"
        )

        # ----------------------------------
        # 임베딩할 텍스트
        # ----------------------------------

        documents = [
            build_embedding_text(record)
            for record
            in collection_records
        ]

        ids = [
            record["chunk_id"]
            for record
            in collection_records
        ]

        metadatas = []

        for record in collection_records:

            metadata = {
                "law_name":
                    record["law_name"],

                "document_type":
                    record[
                        "document_type"
                    ],

                "article":
                    record["article"],

                "article_title":
                    record.get(
                        "article_title",
                        ""
                    ),

                "source":
                    record.get(
                        "source",
                        ""
                    ),
            }

            metadatas.append(metadata)

        # ----------------------------------
        # 임베딩 생성
        # ----------------------------------

        print(
            "임베딩 생성 중..."
        )

        embeddings = model.encode(
            documents,
            batch_size=32,
            show_progress_bar=True,
            normalize_embeddings=True,
        ).tolist()

        # ----------------------------------
        # 컬렉션 생성
        # ----------------------------------

        collection = (
            client.create_collection(
                name=collection_name,
                metadata={
                    "hnsw:space": "cosine"
                },
            )
        )

        # ----------------------------------
        # 작은 batch로 저장
        # ----------------------------------

        batch_size = 100

        for start in range(
            0,
            len(collection_records),
            batch_size
        ):

            end = min(
                start + batch_size,
                len(collection_records)
            )

            collection.add(
                ids=ids[start:end],
                documents=documents[
                    start:end
                ],
                metadatas=metadatas[
                    start:end
                ],
                embeddings=embeddings[
                    start:end
                ],
            )

            print(
                f"저장: "
                f"{end}/"
                f"{len(collection_records)}"
            )

        print(
            f"{collection_name} "
            f"저장 완료: "
            f"{collection.count()}개"
        )

    print()
    print("=" * 50)
    print("모든 Vector DB 구축 완료")


if __name__ == "__main__":
    main()
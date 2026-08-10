from pathlib import Path
import json
import re


BASE_DIR = Path(__file__).resolve().parent.parent

PROCESSED_DIR = BASE_DIR / "data" / "processed"
PARSED_DIR = BASE_DIR / "data" / "parsed"

OUTPUT_PATH = (
    PARSED_DIR / "regulations.jsonl"
)


ARTICLE_PATTERN = re.compile(
    r"^(제\s*\d+\s*조(?:의\s*\d+)?"
    r"(?:\([^)]*\))?)"
)


def normalize_spaces(text: str) -> str:
    """
    지나치게 많은 공백을 정리한다.
    """

    return re.sub(
        r"[ \t]+",
        " ",
        text
    ).strip()


def parse_article_header(
    header: str
) -> tuple[str, str]:
    """
    제42조(추락의 방지)

    ->
    article = 제42조
    title = 추락의 방지
    """

    article_match = re.search(
        r"제\s*\d+\s*조(?:의\s*\d+)?",
        header
    )

    title_match = re.search(
        r"\((.*?)\)",
        header
    )

    article = (
        article_match.group(0)
        if article_match
        else header
    )

    title = (
        title_match.group(1)
        if title_match
        else ""
    )

    return article, title


def split_articles(
    text: str
) -> list[dict]:
    """
    전체 법령 텍스트를 조 단위로 분리한다.
    """

    lines = text.splitlines()

    articles = []

    current_header = None
    current_content = []

    for line in lines:

        line = normalize_spaces(line)

        if not line:
            continue

        # 새로운 제○조 시작
        if ARTICLE_PATTERN.match(line):

            # 이전 조문 저장
            if current_header:

                articles.append(
                    {
                        "header": current_header,
                        "content": "\n".join(
                            current_content
                        ).strip()
                    }
                )

            current_header = line
            current_content = []

        else:

            if current_header:
                current_content.append(line)

    # 마지막 조문 저장
    if current_header:

        articles.append(
            {
                "header": current_header,
                "content": "\n".join(
                    current_content
                ).strip()
            }
        )

    return articles


def guess_document_type(
    law_name: str
) -> str:

    if "시행령" in law_name:
        return "ENFORCEMENT_DECREE"

    if "시행규칙" in law_name:
        return "ENFORCEMENT_RULE"

    if "기준에 관한 규칙" in law_name:
        return "SAFETY_REGULATION"

    return "LAW"


def process_file(
    txt_path: Path
) -> list[dict]:

    law_name = txt_path.stem

    text = txt_path.read_text(
        encoding="utf-8"
    )

    articles = split_articles(text)

    records = []

    for index, item in enumerate(
        articles,
        start=1
    ):

        article, title = parse_article_header(
            item["header"]
        )

        # 제목 뒤에 붙어 있는 본문이 있을 수 있으므로
        # header 전체도 content에 포함
        content = (
            f"{item['header']}\n"
            f"{item['content']}"
        ).strip()

        record = {
            "chunk_id": (
                f"{txt_path.stem}-{index:04d}"
            ),
            "law_name": law_name,
            "document_type": (
                guess_document_type(
                    law_name
                )
            ),
            "article": article,
            "article_title": title,
            "source": "국가법령정보센터",
            "content": content
        }

        records.append(record)

    return records


def main():

    PARSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    txt_files = list(
        PROCESSED_DIR.glob("*.txt")
    )

    if not txt_files:

        print(
            "processed 폴더에 TXT 파일이 없습니다."
        )
        return

    total_records = []

    for txt_path in txt_files:

        print(
            f"조문 분석 중: {txt_path.name}"
        )

        records = process_file(txt_path)

        print(
            f"  → {len(records)}개 조문"
        )

        total_records.extend(records)

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8"
    ) as file:

        for record in total_records:

            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                )
            )

            file.write("\n")

    print()
    print(
        f"총 {len(total_records)}개의 "
        f"조문을 저장했습니다."
    )

    print(
        f"저장 위치: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
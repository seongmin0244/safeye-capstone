"""latency 벤치와 accuracy 평가 결과를 합쳐 운영 후보를 고른다.

예시:
    python notebooks/compare_vlm_results.py \
        --latency bench_latency.csv --accuracy eval_accuracy.md
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def _number(value: str):
    value = (value or "").strip()
    if value in {"", "None", "none", "-"}:
        return None
    try:
        f = float(value)
    except ValueError:
        return value
    return int(f) if f.is_integer() else f


def read_latency(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return [{k: _number(v) for k, v in row.items()} for row in csv.DictReader(f)]


def read_accuracy_markdown(path: str) -> list[dict]:
    rows: list[dict] = []
    headers: list[str] | None = None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("|"):
            if rows:
                break
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c) <= {"-"} for c in cells):
            continue
        if headers is None:
            headers = cells
            continue
        rows.append({k: _number(v) for k, v in zip(headers, cells)})
    return rows


def join_rows(latency: list[dict], accuracy: list[dict]) -> list[dict]:
    by_key = {
        (str(row.get("model")), int(row.get("edge"))): row
        for row in latency
        if row.get("edge") is not None
    }
    joined = []
    for acc in accuracy:
        key = (str(acc.get("model")), int(acc.get("edge")))
        lat = by_key.get(key)
        if lat:
            joined.append({**lat, **{f"acc_{k}": v for k, v in acc.items()}})
    return joined


def is_candidate(row: dict, args) -> bool:
    def value(key: str, default: float) -> float:
        v = row.get(key)
        return default if v is None else float(v)

    return (
        value("json_ok_rate", 0.0) >= args.min_latency_json_ok
        and value("acc_json_ok_rate", 0.0) >= args.min_accuracy_json_ok
        and value("acc_critical_miss_rate", 1.0) <= args.max_critical_miss
        and value("acc_danger_miss_rate", 1.0) <= args.max_danger_miss
        and row.get("p95_ms") is not None
    )


def render(rows: list[dict], args) -> str:
    if not rows:
        return "No matching model/edge rows found between latency and accuracy results."

    ranked = sorted(
        rows,
        key=lambda r: (
            not is_candidate(r, args),
            float(r.get("acc_critical_miss_rate") or 1),
            float(r.get("acc_danger_miss_rate") or 1),
            float(r.get("p95_ms") or 10**12),
            float(r.get("p50_ms") or 10**12),
        ),
    )
    cols = [
        "decision",
        "model",
        "edge",
        "p50_ms",
        "p95_ms",
        "json_ok_rate",
        "acc_json_ok_rate",
        "acc_critical_miss_rate",
        "acc_danger_miss_rate",
        "acc_false_alarm_rate",
        "acc_severity_exact",
    ]
    lines = [
        "| " + " | ".join(cols) + " |",
        "|" + "|".join("---" for _ in cols) + "|",
    ]
    for row in ranked:
        out = {**row, "decision": "candidate" if is_candidate(row, args) else "drop"}
        lines.append("| " + " | ".join(str(out.get(c, "")) for c in cols) + " |")
    lines += [
        "",
        "Rule: drop rows that fail JSON reliability or miss-rate gates; rank remaining rows by critical miss, danger miss, then p95 latency.",
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Compare VLM latency and accuracy results")
    ap.add_argument("--latency", default="bench_latency.csv")
    ap.add_argument("--accuracy", default="eval_accuracy.md")
    ap.add_argument("--out", default="vlm_decision.md")
    ap.add_argument("--min-latency-json-ok", type=float, default=0.95)
    ap.add_argument("--min-accuracy-json-ok", type=float, default=0.95)
    ap.add_argument("--max-critical-miss", type=float, default=0.0)
    ap.add_argument("--max-danger-miss", type=float, default=0.0)
    args = ap.parse_args()

    rows = join_rows(read_latency(args.latency), read_accuracy_markdown(args.accuracy))
    md = render(rows, args)
    Path(args.out).write_text(md, encoding="utf-8")
    print(md)
    print(f"\nsaved {args.out}")


if __name__ == "__main__":
    main()

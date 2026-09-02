"""골든셋으로 모델 정확도를 비교함.

현재 도메인에서는 전체 accuracy보다 critical miss가 더 중요함. 위험한 장면을
INFO로 놓치는 모델은 빠르더라도 운영 후보에서 빼는 쪽이 안전함.

golden.jsonl 예시:
    {"image": "samples/a.jpg", "hazard_detected": true, "severity": "CRITICAL", "hazard_type": "떨어짐"}
    {"image": "samples/b.jpg", "hazard_detected": false, "severity": "INFO", "hazard_type": "없음"}
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.local.config import local_settings as cfg  # noqa: E402
from app.local.imageops import to_edge  # noqa: E402
from app.local.ollama_client import OllamaClient  # noqa: E402
from app.postprocess import verify  # noqa: E402
from app.prompt import build_prompt  # noqa: E402
from app.schemas import INTERNAL_JSON_SCHEMA, VLMInternal  # noqa: E402

SEV_RANK = {"INFO": 0, "WARNING": 1, "CRITICAL": 2}


def load_golden(path: str) -> list[dict]:
    rows = []
    base = Path(path).parent
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as e:
                raise SystemExit(f"{path}:{i} JSON error: {e}") from e
            image_path = Path(row["image"])
            row["_path"] = image_path if image_path.is_absolute() or image_path.exists() else base / image_path
            if not Path(row["_path"]).exists():
                raise SystemExit(f"{path}:{i} image not found: {row['_path']}")
            rows.append(row)
    if not rows:
        raise SystemExit("golden set is empty")
    return rows


async def predict(client: OllamaClient, model: str, img: bytes, prompt: str) -> dict:
    try:
        obj, timing = await client.chat_json(img, prompt, INTERNAL_JSON_SCHEMA, model=model)
        internal = VLMInternal.model_validate(obj)
        _, hallucinated = verify(internal.model_copy(deep=True))
        return {
            "parsed": True,
            "hazard_detected": internal.hazard_detected,
            "severity": internal.severity,
            "hazard_type": internal.hazard_type,
            "confidence": internal.confidence,
            "n_objects": len(internal.observed_objects),
            "n_uncertain": len(internal.uncertain),
            "hallucinated": ",".join(hallucinated),
            "latency_ms": round(timing.total_ms, 0),
        }
    except Exception as e:
        return {"parsed": False, "error": f"{type(e).__name__}: {str(e)[:120]}"}


def score(records: list[dict]) -> dict:
    n = len(records)
    parsed = [r for r in records if r["parsed"]]
    if not parsed:
        return {"n": n, "json_ok_rate": 0.0}

    danger_truth = [r for r in parsed if r["t_hazard"]]
    safe_truth = [r for r in parsed if not r["t_hazard"]]
    crit_truth = [r for r in parsed if r["t_severity"] == "CRITICAL"]

    def rate(hits, total):
        return round(hits / total, 3) if total else None

    miss = sum(
        1 for r in danger_truth
        if r["severity"] == "INFO" or not r["hazard_detected"]
    )
    crit_miss = sum(1 for r in crit_truth if r["severity"] != "CRITICAL")
    false_alarm = sum(1 for r in safe_truth if r["hazard_detected"])
    under = sum(
        1 for r in parsed
        if SEV_RANK[r["severity"]] < SEV_RANK[r["t_severity"]]
    )
    over = sum(
        1 for r in parsed
        if SEV_RANK[r["severity"]] > SEV_RANK[r["t_severity"]]
    )

    typed = [r for r in parsed if r.get("t_hazard_type")]
    return {
        "n": n,
        "json_ok_rate": rate(len(parsed), n),
        "critical_miss_rate": rate(crit_miss, len(crit_truth)),
        "danger_miss_rate": rate(miss, len(danger_truth)),
        "false_alarm_rate": rate(false_alarm, len(safe_truth)),
        "severity_exact": rate(
            sum(1 for r in parsed if r["severity"] == r["t_severity"]),
            len(parsed),
        ),
        "severity_under": rate(under, len(parsed)),
        "severity_over": rate(over, len(parsed)),
        "detect_acc": rate(
            sum(1 for r in parsed if r["hazard_detected"] == r["t_hazard"]),
            len(parsed),
        ),
        "hazard_type_acc": rate(
            sum(1 for r in typed if r["hazard_type"] == r["t_hazard_type"]),
            len(typed),
        ),
        "halluc_rate": rate(sum(1 for r in parsed if r["hallucinated"]), len(parsed)),
        "mean_conf": round(statistics.mean(r["confidence"] for r in parsed), 3),
        "mean_objects": round(statistics.mean(r["n_objects"] for r in parsed), 2),
        "p50_ms": round(statistics.median(r["latency_ms"] for r in parsed), 0),
    }


async def evaluate(args) -> tuple[dict, list[dict]]:
    golden = load_golden(args.golden)
    prompt = build_prompt()
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    edges = [int(e) for e in args.edges.split(",") if e.strip()]
    client = OllamaClient(
        base_url=args.ollama,
        model=models[0],
        connect_timeout=cfg.connect_timeout,
        read_timeout=args.read_timeout,
        keep_alive=cfg.keep_alive,
        num_ctx=cfg.num_ctx,
        num_predict=cfg.num_predict,
        temperature=args.temperature,
        think=cfg.think,
    )

    summary: dict[str, dict] = {}
    detail: list[dict] = []

    for model in models:
        try:
            await client.warmup(model)
        except Exception as e:
            print(f"!! {model} warmup failed; skipping: {e}")
            continue

        for edge in edges:
            records = []
            for row in golden:
                raw = Path(row["_path"]).read_bytes()
                img = to_edge(raw, edge)
                votes = [await predict(client, model, img, prompt) for _ in range(args.runs)]
                ok = [v for v in votes if v["parsed"]]
                if ok:
                    severity = Counter(v["severity"] for v in ok).most_common(1)[0][0]
                    pick = next(v for v in ok if v["severity"] == severity)
                else:
                    pick = votes[0]

                rec = {
                    **pick,
                    "image": Path(row["_path"]).name,
                    "t_hazard": bool(row.get("hazard_detected", False)),
                    "t_severity": row.get("severity", "INFO"),
                    "t_hazard_type": row.get("hazard_type"),
                    "unstable": len({v.get("severity") for v in ok}) > 1,
                }
                records.append(rec)
                mark = "!" if not rec["parsed"] else (
                    "O" if rec["severity"] == rec["t_severity"] else "X"
                )
                print(
                    f"  [{model:26s} e={edge:4d}] {rec['image']:22s} {mark} "
                    f"pred={rec.get('severity', '-'):8s} true={rec['t_severity']}"
                )
                detail.append({"model": model, "edge": edge, **rec})

            key = f"{model}@{edge}"
            summary[key] = {"model": model, "edge": edge, **score(records)}
            print(
                f"  summary {key}: "
                f"critical_miss={summary[key].get('critical_miss_rate')} "
                f"severity_exact={summary[key].get('severity_exact')}"
            )

        if not args.keep_loaded:
            await client.unload(model)
    return summary, detail


def render(summary: dict, baseline: str | None) -> str:
    cols = [
        "model",
        "edge",
        "n",
        "json_ok_rate",
        "critical_miss_rate",
        "danger_miss_rate",
        "false_alarm_rate",
        "severity_exact",
        "hazard_type_acc",
        "halluc_rate",
        "mean_conf",
        "p50_ms",
    ]
    lines = [
        "| " + " | ".join(cols) + " |",
        "|" + "|".join("---" for _ in cols) + "|",
    ]
    for row in summary.values():
        lines.append("| " + " | ".join(str(row.get(c, "")) for c in cols) + " |")

    base_row = next((r for r in summary.values() if r["model"] == baseline), None)
    if base_row:
        lines += [
            "",
            f"### Baseline delta ({baseline})",
            "",
            "| model | edge | critical_miss_delta | severity_exact_delta | p50_ms_delta |",
            "|---|---|---|---|---|",
        ]
        for row in summary.values():
            def delta(key):
                a, b = row.get(key), base_row.get(key)
                if a is None or b is None:
                    return "-"
                return f"{round(a - b, 3):+}"

            lines.append(
                f"| {row['model']} | {row['edge']} | "
                f"{delta('critical_miss_rate')} | {delta('severity_exact')} | {delta('p50_ms')} |"
            )
        lines += [
            "",
            "Suggested rule: drop any combination whose critical_miss_rate is worse than baseline.",
            "Among the remaining combinations, prefer the lower p95/p50 latency.",
        ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Evaluate VLM accuracy against a golden set")
    ap.add_argument("--golden", required=True, help="golden JSONL")
    ap.add_argument("--models", default=cfg.bench_models)
    ap.add_argument("--edges", default="1024")
    ap.add_argument("--baseline", default="", help="baseline model")
    ap.add_argument("--runs", type=int, default=1, help="repeat count per image")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--ollama", default=cfg.ollama_base_url)
    ap.add_argument("--read-timeout", type=float, default=180.0)
    ap.add_argument("--keep-loaded", action="store_true")
    ap.add_argument("--out", default="eval_accuracy")
    args = ap.parse_args()

    summary, detail = asyncio.run(evaluate(args))
    if not summary:
        raise SystemExit("no results")

    with open(f"{args.out}_detail.csv", "w", newline="", encoding="utf-8") as f:
        keys = sorted({k for row in detail for k in row})
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(detail)

    md = render(summary, args.baseline or None)
    Path(f"{args.out}.md").write_text(md, encoding="utf-8")
    print("\n" + md)
    print(f"\nsaved {args.out}.md / {args.out}_detail.csv")


if __name__ == "__main__":
    main()

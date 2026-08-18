"""모델과 입력 해상도별 지연시간을 비교함.

이 스크립트는 얼마나 빠른가만 봄. 실제로 어떤 모델을 쓸지는
`eval_accuracy.py`의 miss/false alarm 결과와 함께 판단 필요.

예시:
    python scripts/bench_latency.py --images ./samples --n 5
    python scripts/bench_latency.py --images ./samples --n 10 \
        --models qwen3-vl:8b-q4_K_M,qwen3-vl:8b-q8_0 --edges 672,1024 --out bench.csv
    python scripts/bench_latency.py --images ./samples --n 5 --via-api http://100.x.y.z:8100
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import statistics
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.local.config import local_settings as cfg  # noqa: E402
from app.local.imageops import dims, to_edge  # noqa: E402
from app.local.ollama_client import OllamaClient  # noqa: E402
from app.prompt import build_prompt  # noqa: E402
from app.schemas import INTERNAL_JSON_SCHEMA, VLMInternal  # noqa: E402


def pct(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    return s[max(0, min(len(s) - 1, int(len(s) * p) - 1))]


def load_images(folder: str, n: int) -> list[tuple[str, bytes]]:
    paths = sorted(
        p for p in Path(folder).iterdir()
        if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
    )[:n]
    if not paths:
        raise SystemExit(f"no images found: {folder}")
    return [(p.name, p.read_bytes()) for p in paths]


async def run_direct(client: OllamaClient, model: str, img: bytes, prompt: str) -> dict:
    t0 = time.perf_counter()
    try:
        obj, timing = await client.chat_json(img, prompt, INTERNAL_JSON_SCHEMA, model=model)
        wall = (time.perf_counter() - t0) * 1000
        try:
            VLMInternal.model_validate(obj)
            valid = True
        except Exception:
            valid = False
        return {"ok": True, "schema_valid": valid, "wall_ms": wall, **timing.as_dict()}
    except Exception as e:
        return {
            "ok": False,
            "schema_valid": False,
            "wall_ms": (time.perf_counter() - t0) * 1000,
            "error": f"{type(e).__name__}: {e}",
        }


async def run_via_api(base: str, img: bytes, prompt: str, key: str = "") -> dict:
    t0 = time.perf_counter()
    headers = {"X-Local-Key": key} if key else {}
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                f"{base.rstrip('/')}/v1/analyze_internal",
                files={"image": ("img.jpg", img, "image/jpeg")},
                data={"prompt": prompt},
                headers=headers,
            )
            wall = (time.perf_counter() - t0) * 1000
            ok = response.status_code == 200
            return {
                "ok": ok,
                "schema_valid": ok,
                "wall_ms": wall,
                "status": response.status_code,
                "error": "" if ok else response.text[:120],
            }
    except Exception as e:
        return {
            "ok": False,
            "schema_valid": False,
            "wall_ms": (time.perf_counter() - t0) * 1000,
            "error": f"{type(e).__name__}: {e}",
        }


async def bench(args) -> list[dict]:
    images = load_images(args.images, args.n)
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
        temperature=cfg.temperature,
    )

    rows: list[dict] = []
    for model in models:
        if not args.via_api:
            print(f"\n=== loading {model} ===", flush=True)
            try:
                load_ms = await client.warmup(model)
                vram = await client.loaded_vram_mb(model)
                print(f"    load={load_ms:.0f}ms  vram={vram:.0f}MB")
            except Exception as e:
                print(f"    !! warmup failed; skipping: {e}")
                continue

        for edge in edges:
            samples: list[dict] = []
            for _ in range(args.repeat):
                for name, raw in images:
                    img = to_edge(raw, edge)
                    if args.via_api:
                        result = await run_via_api(args.via_api, img, prompt, args.key)
                    else:
                        result = await run_direct(client, model, img, prompt)
                    result["image"] = name
                    result["px"] = "x".join(map(str, dims(img)))
                    samples.append(result)

                    flag = "ok " if result["ok"] else "FAIL"
                    print(
                        f"  [{model:28s} e={edge:4d}] {name:24s} {flag} "
                        f"{result['wall_ms']:7.0f}ms"
                        + ("" if result["ok"] else f"  {result.get('error', '')[:70]}")
                    )

            good = [s for s in samples if s["ok"]]
            walls = [s["wall_ms"] for s in good]
            row = {
                "model": model,
                "edge": edge,
                "n": len(samples),
                "ok": len(good),
                "json_ok_rate": round(
                    sum(s["schema_valid"] for s in samples) / len(samples), 3
                ),
                "p50_ms": round(statistics.median(walls), 0) if walls else None,
                "p95_ms": round(pct(walls, 0.95), 0) if walls else None,
                "max_ms": round(max(walls), 0) if walls else None,
            }
            if good and not args.via_api:
                row |= {
                    "prefill_ms": round(statistics.median(
                        [s["prompt_eval_ms"] for s in good]), 0),
                    "decode_ms": round(statistics.median(
                        [s["eval_ms"] for s in good]), 0),
                    "decode_tps": round(statistics.median(
                        [s["decode_tps"] for s in good]), 1),
                    "vis_tokens": int(statistics.median(
                        [s["prompt_tokens"] for s in good])),
                    "vram_mb": await client.loaded_vram_mb(model),
                }
            rows.append(row)
            print(
                f"  summary {model} edge={edge}: "
                f"p50={row['p50_ms']}ms p95={row['p95_ms']}ms json_ok={row['json_ok_rate']}"
            )

        if not args.via_api and not args.keep_loaded:
            await client.unload(model)
    return rows


def to_markdown(rows: list[dict]) -> str:
    if not rows:
        return "(no results)"
    cols = [
        "model",
        "edge",
        "n",
        "p50_ms",
        "p95_ms",
        "prefill_ms",
        "decode_ms",
        "decode_tps",
        "vis_tokens",
        "vram_mb",
        "json_ok_rate",
    ]
    cols = [c for c in cols if any(c in r for r in rows)]
    head = "| " + " | ".join(cols) + " |"
    sep = "|" + "|".join("---" for _ in cols) + "|"
    body = "\n".join(
        "| " + " | ".join(str(r.get(c, "")) for c in cols) + " |" for r in rows
    )
    return "\n".join([head, sep, body])


def main():
    ap = argparse.ArgumentParser(description="Measure VLM latency by model and image size")
    ap.add_argument("--images", required=True, help="sample image folder")
    ap.add_argument("--n", type=int, default=5, help="number of images")
    ap.add_argument("--repeat", type=int, default=1, help="repeat count per image")
    ap.add_argument("--models", default=cfg.bench_models)
    ap.add_argument("--edges", default=cfg.bench_edges)
    ap.add_argument("--ollama", default=cfg.ollama_base_url)
    ap.add_argument("--read-timeout", type=float, default=180.0)
    ap.add_argument("--via-api", default="", help="local node URL for end-to-end measurement")
    ap.add_argument("--key", default="", help="X-Local-Key")
    ap.add_argument("--keep-loaded", action="store_true", help="do not unload model between runs")
    ap.add_argument("--out", default="bench_latency.csv")
    args = ap.parse_args()

    rows = asyncio.run(bench(args))

    if rows:
        keys = sorted({k for r in rows for k in r})
        with open(args.out, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(rows)
        md = to_markdown(rows)
        Path(args.out).with_suffix(".md").write_text(md, encoding="utf-8")
        print("\n" + md)
        print(f"\nsaved {args.out} / {Path(args.out).with_suffix('.md')}")
        print("Latency is only half of the decision. Compare with eval_accuracy.py too.")
    else:
        print("no results", file=sys.stderr)


if __name__ == "__main__":
    main()

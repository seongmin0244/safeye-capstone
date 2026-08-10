#!/usr/bin/env bash
# 후보 모델을 한 번에 받아서 벤치마크를 돌리기 위한 스크립트
#
#   bash scripts/pull_models.sh
#   MODELS="qwen3-vl:8b-q4_K_M qwen3-vl:4b" bash scripts/pull_models.sh

set -u

MODELS="${MODELS:-qwen3-vl:8b-q4_K_M qwen3-vl:8b-q8_0 qwen3-vl:4b-q4_K_M qwen2.5vl:7b}"

echo "== pull =="
for model in $MODELS; do
  echo "--- $model"
  ollama pull "$model" || echo "    skip: tag not found or network failed"
done

echo
echo "== installed models =="
ollama list

echo
echo "== loaded models =="
ollama ps

echo
echo "Next: copy the working model list into LN_BENCH_MODELS, then run:"
echo "      python scripts/bench_latency.py --images ./samples --n 5"

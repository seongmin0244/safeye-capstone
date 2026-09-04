from pathlib import Path

# 프로젝트 루트: vlm-workspace/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 프롬프트 경로
PROMPTS_DIR = BASE_DIR / "prompts"

# TODO[RAG-VLM]: 기존 VLM 모델 설정과 통합 예정
VLM_MODEL = "qwen2.5vl:7b"
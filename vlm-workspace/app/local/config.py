from pathlib import Path
import os


# vlm-workspace/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = BASE_DIR / "data"

VIDEO_DIR = DATA_DIR / "videos"
FRAME_DIR = DATA_DIR / "frames"

PROMPTS_DIR = BASE_DIR / "prompts"

VIDEO_ANALYSIS_PROMPT = (
    PROMPTS_DIR / "video_analysis.txt"
)


# Ollama에서 실제 설치되어 있는 모델
VLM_MODEL = os.getenv(
    "VLM_MODEL",
    "qwen2.5vl:3b",
)

# 몇 초마다 프레임을 추출할지
FRAME_INTERVAL_SEC = 2.0
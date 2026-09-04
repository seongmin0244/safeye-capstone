# SAFEye-capstone
산업 현장 위험 상황 맥락 인지를 위한 VLM 및 추론 엔진 (SAFEye 관제 시스템)


# 실행 방법

# * 전체 파이프라인 실행(아래 작업 우선) *
python -m app.pipeline

# 1. VLM 작업폴더 이동
cd vlm-workspace

# 2.가상환경 생성 및 활성화
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Python 패키지 설치
python -m pip install --upgrade pip
python -m pip install -r requirements.local.txt

# 4. Ollama 모델 설치
ollama pull qwen3-vl:8b-instruct


# 5. RAG Vector DB 구축
python scripts/build_vector_db.py


# 6. FastAPI 실행
python -m uvicorn app.api:app --host 0.0.0.0 --port 8000

정상 실행 후 Swagger 접속:
http://127.0.0.1:8000/docs

POST /api/vlm/analyze
→ Try it out
→ image 파일 선택
→ Execute


# 영상자료 위치
vlm-workspace\data\videos\test.mp4


# 프로젝트 구조

safEYE-capstone/
├─ backend/                         # Spring Boot
├─ frontend/                        # Frontend
│
└─ vlm-workspace/
   ├─ app/
   │  ├─ local/                     # VLM 호출 및 이미지 처리
   │  ├─ rag/                       # RAG 검색 및 재정렬
   │  ├─ api.py                     # FastAPI
   │  ├─ api_schemas.py             # API Schema
   │  ├─ image_pipeline.py          # 이미지 분석 Pipeline
   │  ├─ response_builder.py        # 최종 응답 생성
   │  └─ severity.py                # 위험도 산정
   │
   ├─ data/
   │  ├─ raw_laws/                  # 법령 원문
   │  ├─ processed/                 # HWPX 추출 TXT
   │  ├─ parsed/
   │  │  └─ regulations.jsonl       # 파싱된 RAG Dataset
   │  └─ rag/
   │     └─ chroma_db/              # Local Vector DB
   │
   ├─ prompts/
   │  └─ video_analysis.txt
   │
   ├─ scripts/
   │  ├─ extract_hwpx.py
   │  ├─ parse_articles.py
   │  └─ build_vector_db.py
   │
   └─ requirements.local.txt

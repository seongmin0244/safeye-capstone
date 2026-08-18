"""실제 VLM 대신 쓰는 가짜 백엔드.

같은 이미지는 항상 같은 시나리오로 매핑함.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import random

from app.schemas import ObservedObject, VLMInternal


def _env_float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, default))
    except ValueError:
        return default


FIXTURES: dict[str, VLMInternal] = {
    "CRITICAL": VLMInternal(
        observed_objects=[
            ObservedObject(
                name="작업자",
                attributes=["안전모 미착용", "안전고리 미체결"],
                location="중앙 상단",
            ),
            ObservedObject(name="고소작업대", attributes=["난간 있음"], location="중앙"),
        ],
        spatial_relations=["작업자가 고소작업대 상부에 위치함"],
        uncertain=["안전화 착용 여부는 이미지상 명확하지 않음"],
        hazard_detected=True,
        hazard_type="떨어짐",
        severity="CRITICAL",
        reasoning=(
            "고소작업대에서 작업 중인 작업자가 안전모와 안전고리를 제대로 착용하지 "
            "않은 것으로 보입니다. 추락 시 중상 이상의 사고로 이어질 수 있습니다."
        ),
        recommended_actions=[
            "즉시 작업 중단",
            "안전고리 체결 후 작업 재개",
            "관리감독자 현장 확인",
        ],
        references=["산업안전보건기준에 관한 규칙 제2조 추락 방지"],
        confidence=0.88,
    ),
    "WARNING": VLMInternal(
        observed_objects=[
            ObservedObject(name="작업자", attributes=["안전모 착용"], location="좌측"),
            ObservedObject(name="자재", attributes=["통로에 놓임"], location="바닥"),
        ],
        hazard_detected=True,
        hazard_type="넘어짐",
        severity="WARNING",
        reasoning="통로에 자재가 놓여 있어 이동 중 걸려 넘어질 위험이 있습니다.",
        recommended_actions=["통로 자재 정리", "이동 통로 확보"],
        references=["산업안전보건기준에 관한 규칙 제9조 작업장의 정리정돈"],
        confidence=0.71,
    ),
    "INFO": VLMInternal(
        observed_objects=[
            ObservedObject(
                name="작업자",
                attributes=["안전모 착용", "안전조끼 착용"],
                location="중앙",
            )
        ],
        hazard_detected=False,
        hazard_type="없음",
        severity="INFO",
        reasoning="보호구를 정상 착용한 상태로 작업 중이며 뚜렷한 위험 요인은 보이지 않습니다.",
        confidence=0.82,
    ),
    "CRITICAL_PINCH": VLMInternal(
        observed_objects=[
            ObservedObject(name="작업자", attributes=["장갑 착용"], location="우측 하단"),
            ObservedObject(name="컨베이어", attributes=["방호덮개 없음", "가동 중"], location="우측"),
        ],
        spatial_relations=["작업자의 손이 컨베이어 구동부에 가까움"],
        hazard_detected=True,
        hazard_type="끼임",
        severity="CRITICAL",
        reasoning=(
            "가동 중인 컨베이어 구동부에 방호덮개가 없고 작업자의 손이 가까이 있습니다. "
            "끼임 사고가 발생할 가능성이 높습니다."
        ),
        recommended_actions=[
            "설비 정지 후 방호덮개 설치",
            "구동부 접근 금지 표시",
            "정비 전 잠금표지 절차 수행",
        ],
        references=["산업안전보건기준에 관한 규칙 제7조 동력기계 방호조치"],
        confidence=0.91,
    ),
    "LOW_CONFIDENCE": VLMInternal(
        observed_objects=[ObservedObject(name="작업자", attributes=[], location="원거리")],
        uncertain=[
            "보호구 착용 여부 판별 어려움",
            "작업 종류 특정 어려움",
            "역광으로 일부 경계가 흐림",
        ],
        hazard_detected=False,
        hazard_type="없음",
        severity="INFO",
        reasoning=(
            "촬영 거리가 멀고 역광이 있어 보호구 착용 여부를 확실히 판별하기 어렵습니다. "
            "위험 여부를 단정하기 어렵습니다."
        ),
        recommended_actions=["카메라 각도 조정 후 재촬영"],
        confidence=0.34,
    ),
    "EMPTY_SCENE": VLMInternal(
        observed_objects=[
            ObservedObject(name="자재 적치대", attributes=["정리 상태"], location="중앙")
        ],
        hazard_detected=False,
        hazard_type="없음",
        severity="INFO",
        reasoning="화면 안에 작업자가 보이지 않으며 뚜렷한 위험 요인도 관찰되지 않습니다.",
        confidence=0.79,
    ),
}

DEFAULT_WEIGHTS = {
    "CRITICAL": 2,
    "CRITICAL_PINCH": 1,
    "WARNING": 3,
    "INFO": 3,
    "EMPTY_SCENE": 2,
    "LOW_CONFIDENCE": 1,
}


def pick_scenario(image_bytes: bytes, weights: dict[str, int] | None = None) -> str:
    """이미지 해시로 시나리오를 고른다. 같은 이미지는 같은 결과를 받는다."""
    w = weights or DEFAULT_WEIGHTS
    pool = [key for key, n in w.items() for _ in range(n) if key in FIXTURES]
    if not pool:
        pool = list(FIXTURES)
    idx = int(hashlib.sha1(image_bytes).hexdigest(), 16) % len(pool)
    return pool[idx]


class MockBackend:
    """실제 VLM처럼 지연시간을 흉내 내고 fixture 복사본을 돌려준다."""

    name = "mock"

    def __init__(
        self,
        latency: tuple[float, float] | None = None,
        scenario: str | None = None,
        deterministic: bool = True,
        weights: dict[str, int] | None = None,
    ):
        self.latency = latency or (
            _env_float("MOCK_LATENCY_MIN", 8.0),
            _env_float("MOCK_LATENCY_MAX", 20.0),
        )
        self.scenario = scenario
        self.deterministic = deterministic
        self.weights = weights

    def resolve(self, image_bytes: bytes) -> str:
        if self.scenario:
            return self.scenario
        if self.deterministic:
            return pick_scenario(image_bytes, self.weights)
        return random.choice(list(FIXTURES))

    async def analyze(self, image_bytes: bytes, prompt: str) -> VLMInternal:
        lo, hi = self.latency
        if hi > 0:
            await asyncio.sleep(random.uniform(lo, hi))
        key = self.resolve(image_bytes)
        return FIXTURES[key].model_copy(deep=True)

    async def health(self) -> bool:
        return True


class FailingMock:
    """게이트웨이의 오류 처리와 서킷 브레이커를 확인하기 위한 실패 백엔드."""

    name = "mock-fail"

    MODES = ("timeout", "error", "badjson", "unreachable", "slow", "empty", "http500")

    def __init__(self, mode: str):
        self.mode = mode

    async def analyze(self, image_bytes: bytes, prompt: str) -> VLMInternal:
        if self.mode == "timeout":
            await asyncio.sleep(600)
        if self.mode == "slow":
            await asyncio.sleep(55)
        if self.mode == "error":
            raise RuntimeError("simulated backend failure")
        if self.mode == "badjson":
            raise ValueError("simulated JSON parse failure")
        if self.mode == "unreachable":
            raise ConnectionError("simulated device offline")
        if self.mode == "http500":
            raise RuntimeError("simulated upstream 500")
        if self.mode == "empty":
            return VLMInternal()
        return FIXTURES["INFO"].model_copy(deep=True)

    async def health(self) -> bool:
        return False

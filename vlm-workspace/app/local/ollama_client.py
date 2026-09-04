"""Ollama HTTP 클라이언트.

로컬 서버와 게이트웨이 어댑터가 함께 쓰는 래퍼. 연결 실패, read timeout,
JSON 파싱 실패를 나눠서 올려야 게이트웨이가 우회할지, 재시도할지 판단.
"""

from __future__ import annotations

import base64
import json
import re
from dataclasses import asdict, dataclass

import httpx

_NS_PER_MS = 1_000_000
_FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.MULTILINE)


class OllamaError(RuntimeError):
    """Ollama 계열 오류의 공통 부모."""


class OllamaUnreachable(OllamaError):
    """Ollama가 꺼져 있거나 연결 자체가 안 되는 상태."""


class OllamaTimeout(OllamaError):
    """연결은 됐지만 제한 시간 안에 추론이 끝나지 않은 상태."""


class OllamaBadJSON(OllamaError):
    """모델 응답이 비어 있거나 JSON으로 파싱되지 않는 상태."""


@dataclass
class OllamaTiming:
    """Ollama가 응답에 실어주는 추론 시간 지표."""

    total_ms: float = 0.0
    load_ms: float = 0.0
    prompt_eval_ms: float = 0.0
    eval_ms: float = 0.0
    prompt_tokens: int = 0
    eval_tokens: int = 0

    @property
    def decode_tps(self) -> float:
        return self.eval_tokens / (self.eval_ms / 1000) if self.eval_ms else 0.0

    @property
    def ttft_ms(self) -> float:
        return self.load_ms + self.prompt_eval_ms

    @classmethod
    def from_response(cls, body: dict) -> "OllamaTiming":
        def g(key: str) -> float:
            return float(body.get(key) or 0)

        return cls(
            total_ms=g("total_duration") / _NS_PER_MS,
            load_ms=g("load_duration") / _NS_PER_MS,
            prompt_eval_ms=g("prompt_eval_duration") / _NS_PER_MS,
            eval_ms=g("eval_duration") / _NS_PER_MS,
            prompt_tokens=int(g("prompt_eval_count")),
            eval_tokens=int(g("eval_count")),
        )

    def as_dict(self) -> dict:
        d = asdict(self)
        d["decode_tps"] = round(self.decode_tps, 2)
        d["ttft_ms"] = round(self.ttft_ms, 1)
        return d


def strip_fence(text: str) -> str:
    """모델이 실수로 ```json 코드블록을 붙여도 파싱할 수 있게 걷어낸다."""
    return _FENCE.sub("", text).strip()


def fallback_json_prompt(prompt: str) -> str:
    """엄격한 schema가 불안정한 VLM을 위해 더 단순한 JSON-전용 프롬프트로 낮춘다."""
    base = prompt.strip()
    suffix = (
        "\nReturn only valid JSON with no markdown, no code fences, "
        "and no prose. You MUST include every key exactly once: "
        "observed_objects, spatial_relations, uncertain, hazard_detected, "
        "hazard_type, severity, reasoning, recommended_actions, references, "
        "confidence. Use empty arrays when there is no value."
    )
    return (base + suffix).strip()


class OllamaClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        *,
        connect_timeout: float = 3.0,
        read_timeout: float = 60.0,
        keep_alive: str | int = "30m",
        num_ctx: int = 4096,
        num_predict: int = 400,
        temperature: float = 0.1,
        think: bool | None = False,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.keep_alive = keep_alive
        self.num_ctx = num_ctx
        self.num_predict = num_predict
        self.temperature = temperature
        self.think = think
        self.connect_timeout = connect_timeout
        self.timeout = httpx.Timeout(
            connect=connect_timeout,
            read=read_timeout,
            write=10.0,
            pool=5.0,
        )

    def _options(self, override: dict | None = None) -> dict:
        opt = {
            "temperature": self.temperature,
            "num_predict": self.num_predict,
            "num_ctx": self.num_ctx,
        }
        if override:
            opt.update({k: v for k, v in override.items() if v is not None})
        return opt

    async def _post(self, path: str, payload: dict, timeout=None) -> dict:
        try:
            async with httpx.AsyncClient(timeout=timeout or self.timeout) as client:
                response = await client.post(f"{self.base_url}{path}", json=payload)
                response.raise_for_status()
                return response.json()
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            raise OllamaUnreachable(f"Ollama unreachable: {self.base_url} ({e})") from e
        except httpx.ReadTimeout as e:
            raise OllamaTimeout(f"read timeout: {path}") from e
        except httpx.HTTPStatusError as e:
            raise OllamaError(
                f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            ) from e

    async def chat_json(
        self,
        image_bytes: bytes,
        prompt: str,
        json_schema: dict,
        *,
        model: str | None = None,
        options: dict | None = None,
    ) -> tuple[dict, OllamaTiming]:
        """이미지 1장과 프롬프트를 보내고 JSON dict와 타이밍을 받는다.

        일부 VLM 모델은 엄격한 JSON schema를 요구하는 format일 때 빈 응답을
        반환하는 경우가 있으므로, 실패 시 한 번만 일반 JSON 모드로 재시도한다.
        """
        attempts = [
            (prompt, json_schema),
            (fallback_json_prompt(prompt), "json"),
        ]
        required_keys = set(json_schema.get("required", ()))
        if not required_keys:
            required_keys = {
                "observed_objects",
                "spatial_relations",
                "uncertain",
                "hazard_detected",
                "hazard_type",
                "severity",
                "reasoning",
                "recommended_actions",
                "references",
                "confidence",
            }

        last_body: dict | None = None
        last_content = ""
        last_thinking = ""
        last_missing_keys: set[str] = set()
        for attempt_prompt, fmt in attempts:
            payload = {
                "model": model or self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": attempt_prompt,
                        "images": [base64.b64encode(image_bytes).decode()],
                    }
                ],
                "format": fmt,
                "stream": False,
                "keep_alive": self.keep_alive,
                "options": self._options(options),
            }
            if self.think is not None:
                payload["think"] = self.think
            body = await self._post("/api/chat", payload)
            last_body = body
            timing = OllamaTiming.from_response(body)
            message = body.get("message") or {}
            content = message.get("content", "")
            last_content = content
            last_thinking = message.get("thinking", "")

            candidates = [content, last_thinking]
            for candidate in candidates:
                if not candidate or not candidate.strip():
                    continue
                cleaned = strip_fence(candidate)
                if cleaned.startswith("<think>"):
                    cleaned = re.sub(r"^<think>\s*", "", cleaned, flags=re.I)
                    cleaned = re.sub(r"\s*</think>\s*$", "", cleaned, flags=re.I)
                try:
                    parsed = json.loads(cleaned)
                    if not isinstance(parsed, dict):
                        continue
                    missing_keys = required_keys.difference(parsed)
                    if missing_keys:
                        last_missing_keys = missing_keys
                        continue
                    return parsed, timing
                except json.JSONDecodeError:
                    continue

        if last_body is not None:
            raw_head = repr(last_content[:200].replace("\n", " "))
            thinking_head = repr(last_thinking[:200].replace("\n", " "))
            if last_missing_keys:
                missing = ", ".join(sorted(last_missing_keys))
                raise OllamaBadJSON(f"incomplete JSON / missing_keys={missing}")
            if last_content.strip():
                raise OllamaBadJSON(f"invalid JSON / raw_head={raw_head}")
            if last_thinking.strip():
                raise OllamaBadJSON(
                    f"empty content / thinking_head={thinking_head}"
                )
            raise OllamaBadJSON(f"empty response / raw_head={raw_head}")
        raise OllamaBadJSON("empty response")

    async def warmup(self, model: str | None = None) -> float:
        """모델을 미리 로드하고, 로드에 걸린 시간을 ms로 돌려준다."""
        payload = {
            "model": model or self.model,
            "prompt": "",
            "stream": False,
            "keep_alive": self.keep_alive,
        }
        body = await self._post(
            "/api/generate",
            payload,
            timeout=httpx.Timeout(
                connect=self.connect_timeout,
                read=300.0,
                write=10.0,
                pool=5.0,
            ),
        )
        return float(body.get("load_duration") or 0) / _NS_PER_MS

    async def unload(self, model: str | None = None) -> None:
        """벤치마크 중 다음 모델과 VRAM이 섞이지 않도록 모델을 내린다."""
        await self._post(
            "/api/generate",
            {"model": model or self.model, "prompt": "", "keep_alive": 0},
        )

    async def tags(self) -> list[dict]:
        """설치된 Ollama 모델 목록."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            return response.json().get("models", [])

    async def ps(self) -> list[dict]:
        """현재 메모리에 올라간 모델 목록."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/api/ps")
            response.raise_for_status()
            return response.json().get("models", [])

    async def show(self, model: str | None = None) -> dict:
        return await self._post("/api/show", {"model": model or self.model})

    async def loaded_vram_mb(self, model: str | None = None) -> float:
        target = model or self.model
        for item in await self.ps():
            if item.get("name", "").startswith(target) or item.get("model", "") == target:
                return round(float(item.get("size_vram") or 0) / 1024 / 1024, 1)
        return 0.0

    async def alive(self) -> bool:
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.connect_timeout)
            ) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

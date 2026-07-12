"""梦境图片供应商调度层。"""
from __future__ import annotations

from app.ai import stepfun, volcano
from app.core.config import settings


def generate_image(prompt: str, *, ref_url: str | None = None, seed: int | None = None,
                   timeout: float = 150.0) -> tuple[bytes, str | None]:
    if settings.image_provider == "volcano":
        return volcano.generate_image(prompt, ref_url=ref_url, seed=seed, timeout=timeout)
    return stepfun.generate_image(prompt, ref_url=ref_url, seed=seed, timeout=timeout)

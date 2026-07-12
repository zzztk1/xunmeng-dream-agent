"""火山方舟 SeedDream 图片适配器。

文本生成始终由 StepFun 负责。只有 IMAGE_PROVIDER=volcano 时，图片调度层才会调用本模块。
供应商临时 URL 会立即下载，产品前端只接收本地持久化后的 /assets URL。
"""
from __future__ import annotations

import base64

import httpx

from app.core.config import settings


class VolcanoError(Exception):
    pass


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.volcano_api_key}",
        "Content-Type": "application/json",
    }


def generate_image(prompt: str, *, ref_url: str | None = None, seed: int | None = None,
                   size: str = "2048x2048", model: str | None = None,
                   timeout: float = 150.0) -> tuple[bytes, str | None]:
    """调用 SeedDream 文生图/图生图，并返回下载后的图片字节与临时来源 URL。"""
    if not settings.volcano_api_key:
        raise VolcanoError("Volcano image disabled: 未配置 VOLCANO_API_KEY")
    payload: dict = {
        "model": model or settings.image_model,
        "prompt": prompt,
        "size": size,
        "response_format": "url",
        "watermark": False,
    }
    if seed is not None:
        payload["seed"] = seed
    if ref_url:
        payload["image"] = ref_url
    with httpx.Client(trust_env=False, timeout=timeout) as client:
        response = client.post(
            f"{settings.VOLCANO_ARK_BASE_URL.rstrip('/')}/images/generations",
            json=payload,
            headers=_headers(),
        )
        response.raise_for_status()
        item = (response.json().get("data") or [{}])[0]
        url = item.get("url")
        if url:
            image = client.get(url)
            image.raise_for_status()
            return image.content, url
        if item.get("b64_json"):
            return base64.b64decode(item["b64_json"]), None
    raise VolcanoError("图像响应缺少 url/b64_json")

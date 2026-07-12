"""阶跃星辰文本与图像适配器。

保持原有业务层调用协议不变。文本返回字符串，图像返回可持久化的字节。
供应商临时 URL 只用于下载，不直接暴露给产品前端。
"""
from __future__ import annotations

import base64

import httpx

from app.core.config import settings


class StepFunError(Exception):
    pass


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.api_key}",
        "Content-Type": "application/json",
    }


def chat(messages: list[dict], *, model: str | None = None, temperature: float = 0.9,
         max_tokens: int = 4096, timeout: float = 90.0, think: bool = False,
         json_mode: bool = False) -> str:
    """调用 StepFun Chat Completions，返回 message.content。

    think=False（默认）关闭模型深度思考(reasoning)，单次延迟约减半（织梦无需深度推理）。
    """
    if not settings.ai_enabled:
        raise StepFunError("AI disabled: 未配置 STEPFUN_API_KEY")
    payload: dict = {
        "model": model or settings.LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if not think:
        payload["thinking"] = {"type": "disabled"}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    with httpx.Client(trust_env=False, timeout=timeout) as client:
        resp = client.post(f"{settings.STEPFUN_API_BASE.rstrip('/')}/chat/completions",
                           json=payload, headers=_headers())
        resp.raise_for_status()
        data = resp.json()
    return data["choices"][0]["message"]["content"]


def generate_image(prompt: str, *, ref_url: str | None = None, seed: int | None = None,
                   size: str = "1024x1024", model: str | None = None,
                   timeout: float = 150.0) -> tuple[bytes, str | None]:
    """生成梦境图并立即下载，返回 (图片字节, 临时来源 URL)。"""
    if not settings.ai_enabled:
        raise StepFunError("AI disabled: 未配置 STEPFUN_API_KEY")
    if ref_url:
        prompt = f"{prompt}。保持与上一场景相同的角色设定、色彩、镜头语言和材质。"
    payload: dict = {
        "model": model or settings.stepfun_image_model,
        "prompt": prompt,
        "size": size,
        "response_format": "b64_json",
        "cfg_scale": 1.0,
        "steps": 8,
        "text_mode": True,
    }
    if seed is not None:
        payload["seed"] = seed
    with httpx.Client(trust_env=False, timeout=timeout) as client:
        resp = client.post(f"{settings.STEPFUN_API_BASE.rstrip('/')}/images/generations",
                           json=payload, headers=_headers())
        resp.raise_for_status()
        item = (resp.json().get("data") or [{}])[0]
        url = item.get("url")
        if url:
            img = client.get(url)
            img.raise_for_status()
            return img.content, url
        if item.get("b64_json"):
            return base64.b64decode(item["b64_json"]), None
    raise StepFunError("图像响应缺少 url/b64_json")

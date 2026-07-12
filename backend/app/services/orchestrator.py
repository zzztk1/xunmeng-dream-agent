"""梦境生成编排器：碎片 → 解析+情绪 → 分场景叙事 → 场景视觉(连续性) → 落库。

无 STEPFUN_API_KEY 时全程走降级路径（输入驱动的占位叙事 + 情绪渐变图），保证可演示。
"""
from __future__ import annotations

import json
import logging
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor

from app.ai import image_provider, stepfun
from app.ai.prompts import (ANALYZE_SYSTEM, WEAVE_FULL_SYSTEM, WEAVE_SYSTEM,
                            analyze_user_prompt, weave_full_user_prompt,
                            weave_user_prompt)
from app.core.config import BASE_DIR, settings
from app.core.db import SessionLocal
from app.models import Asset, Dream, Emotion, Narrative
from app.services.emotion import gradient_svg, palette_for

log = logging.getLogger("orchestrator")

ASSETS_DIR = os.path.join(BASE_DIR, "data", "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

DEFAULT_STYLE = "梦境感，柔焦超现实，低饱和电影质感，柔和漫射光，胶片颗粒，朦胧氛围"


# ----------------------------- 工具 -----------------------------
def _safe_json(text: str) -> dict:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            return json.loads(m.group(0))
        raise


def _fragments_text(dream) -> str:
    lines = [f"- {f.content.strip()}" for f in dream.fragments if f.content.strip()]
    return "\n".join(lines) if lines else "-（一片说不清的雾）"


# ----------------------------- LLM 两步 -----------------------------
def _analyze(frag_text: str) -> dict:
    if settings.ai_enabled:
        try:
            content = stepfun.chat(
                [{"role": "system", "content": ANALYZE_SYSTEM},
                 {"role": "user", "content": analyze_user_prompt(frag_text)}],
                temperature=0.4, max_tokens=2048, json_mode=True)
            data = _safe_json(content)
            data["_model"] = settings.LLM_MODEL
            return data
        except Exception as e:  # noqa: BLE001
            log.warning("LLM 解析失败，降级：%s", e)
    return {"imagery": [], "characters": [], "places": [],
            "sensations": [], "emotions": [], "summary": frag_text[:60]}


def _weave(frag_text: str, analysis: dict, primary: str, dream) -> dict:
    if settings.ai_enabled:
        try:
            content = stepfun.chat(
                [{"role": "system", "content": WEAVE_SYSTEM},
                 {"role": "user", "content": weave_user_prompt(frag_text, analysis, primary)}],
                temperature=0.95, max_tokens=4096, json_mode=True)
            data = _safe_json(content)
            if data.get("scenes"):
                data["_model"] = settings.LLM_MODEL
                return _normalize(data)
        except Exception as e:  # noqa: BLE001
            log.warning("LLM 编织失败，降级：%s", e)
    return _fallback_weave(dream, primary)


def _weave_full(frag_text: str, user_emotion: str, dream) -> dict:
    """合并「解析+编织」为单次调用（关闭深度思考提速），返回含 emotions 的完整结构；失败降级。"""
    if settings.ai_enabled:
        try:
            content = stepfun.chat(
                [{"role": "system", "content": WEAVE_FULL_SYSTEM},
                 {"role": "user", "content": weave_full_user_prompt(frag_text, user_emotion)}],
                temperature=0.92, max_tokens=4096, json_mode=True)
            data = _safe_json(content)
            if data.get("scenes"):
                data["_model"] = settings.LLM_MODEL
                return data
        except Exception as e:  # noqa: BLE001
            log.warning("LLM 织梦失败，降级：%s", e)
    fb = _fallback_weave(dream, user_emotion or "朦胧")
    fb["emotions"] = [{"label": user_emotion or "朦胧", "intensity": 0.6}]
    return fb


def _normalize(data: dict) -> dict:
    scenes = []
    for sc in (data.get("scenes") or [])[:4]:
        scenes.append({
            "text": (sc.get("text") or "").strip(),
            "visual_prompt": (sc.get("visual_prompt") or sc.get("text") or "").strip(),
            "recurring_entities": sc.get("recurring_entities") or [],
            "ambient": sc.get("ambient") or "",
        })
    return {
        "title": (data.get("title") or "未命名的梦").strip()[:40],
        "global_style": (data.get("global_style") or DEFAULT_STYLE).strip(),
        "scenes": scenes or _fallback_scenes_from_text(""),
        "closing_reflection": (data.get("closing_reflection") or "我在这儿，这个梦已经被好好收下了。").strip(),
        "_model": data.get("_model") or "fallback",
    }


def _fallback_scenes_from_text(_):
    return [{"text": "你在一片说不清的雾里，慢慢往前。", "visual_prompt": "迷雾，朦胧",
             "recurring_entities": [], "ambient": "朦胧"}]


def _fallback_weave(dream, primary: str) -> dict:
    """输入驱动的占位叙事：保留用户碎片原话，编织成 1~3 个场景。"""
    texts = [f.content.strip() for f in dream.fragments if f.content.strip()] or ["一片说不清的雾"]
    n = min(3, max(1, len(texts)))
    groups: list[list[str]] = [[] for _ in range(n)]
    for i, t in enumerate(texts):
        groups[i % n].append(t)
    connectors = ["你发现自己置身其中——", "画面忽然一转，", "再睁眼时，"]
    scenes = []
    for i, group in enumerate(groups):
        body = "；".join(group)
        scenes.append({
            "text": f"{connectors[i % len(connectors)]}{body}。一切都很轻，像随时会散开。",
            "visual_prompt": f"{body}，{DEFAULT_STYLE}",
            "recurring_entities": group[:1],
            "ambient": primary,
        })
    title = texts[0][:12] or "未命名的梦"
    return {
        "title": title,
        "global_style": DEFAULT_STYLE,
        "scenes": scenes,
        "closing_reflection": f"这个梦里，你好像被一种「{primary}」的情绪轻轻包着。我在这儿，它已经被好好收下了。",
        "_model": "fallback",
    }


# ----------------------------- 图像（连续性） -----------------------------
def _compose_prompt(scene: dict, global_style: str) -> str:
    parts = [scene.get("visual_prompt", "")]
    ents = scene.get("recurring_entities") or []
    if ents:
        parts.append("画面中保持一致：" + "，".join(ents))
    parts.append(global_style or DEFAULT_STYLE)
    return "，".join(p for p in parts if p)


def _gen_image(idx: int, prompt: str, seed: int, ref_url: str | None, palette: dict):
    """返回 (ext, data_bytes, ark_url, meta)。网络生成，可在线程中执行（不碰 DB）。"""
    if settings.image_enabled:
        try:
            data, url = image_provider.generate_image(prompt, ref_url=ref_url, seed=seed + idx)
            return "jpeg", data, url, {"mode": "i2i" if ref_url else "t2i", "seed": seed + idx,
                                       "ref": bool(ref_url), "scene_index": idx,
                                       "provider": settings.image_provider,
                                       "model": settings.image_model}
        except Exception as e:  # noqa: BLE001
            log.warning("图像生成失败(scene %s)，降级渐变：%s", idx, e)
    svg = gradient_svg(palette, seed, idx)
    return "svg", svg.encode("utf-8"), None, {"mode": "fallback", "seed": seed + idx, "scene_index": idx}


def _persist_asset(db, dream, idx: int, prompt: str, ext: str, data: bytes, meta: dict) -> dict:
    asset = Asset(dream_id=dream.id, type="image", prompt=prompt, meta=meta)
    db.add(asset)
    db.flush()  # 取得 asset.id
    filename = f"{asset.id}.{ext}"
    with open(os.path.join(ASSETS_DIR, filename), "wb") as fp:
        fp.write(data)
    asset.path = filename
    return {"id": asset.id, "image_url": f"/assets/{filename}"}


def _render_scene(dream_id: str, i: int, prompt: str, seed: int,
                  ref_url: str | None, palette: dict, lock: threading.Lock) -> str | None:
    """生成单张场景图（网络部分可并行），落库时加锁 + 独立会话，避免 JSON 列竞写。返回 Ark URL。"""
    ext, data, url, meta = _gen_image(i, prompt, seed, ref_url, palette)  # 慢/网络，锁外并行
    with lock:
        db = SessionLocal()
        try:
            dream = db.get(Dream, dream_id)
            if not dream or not dream.narrative:
                return url
            asset = Asset(dream_id=dream_id, type="image", prompt=prompt, meta=meta)
            db.add(asset)
            db.flush()
            fn = f"{asset.id}.{ext}"
            with open(os.path.join(ASSETS_DIR, fn), "wb") as fp:
                fp.write(data)
            asset.path = fn
            sc = list(dream.narrative.scenes or [])  # 锁内重新读最新，避免覆盖其他场景
            if i < len(sc):
                sc[i] = {**sc[i], "image_url": f"/assets/{fn}", "asset_id": asset.id}
                dream.narrative.scenes = sc
                db.add(dream.narrative)
            db.commit()
        except Exception:  # noqa: BLE001
            log.exception("落库场景 %s 失败", i)
        finally:
            db.close()
    return url


def render_images(dream_id: str) -> None:
    """后台：场景0文生图(锚定)→其余图生图并行；逐张落库可渐进显示，完成置 generated。"""
    db = SessionLocal()
    try:
        dream = db.get(Dream, dream_id)
        if not dream or not dream.narrative:
            return
        scenes = list(dream.narrative.scenes or [])
        palette = dream.palette or palette_for(dream.primary_emotion)
        style = dream.narrative.global_style or DEFAULT_STYLE
        seed = int(dream.id[:8], 16) % 100000
        prompts = [_compose_prompt(sc, style) for sc in scenes]
    finally:
        db.close()
    if not scenes:
        return
    lock = threading.Lock()
    try:
        anchor = _render_scene(dream_id, 0, prompts[0], seed, None, palette, lock)  # 锚定图
        rest = list(range(1, len(scenes)))
        if rest:
            with ThreadPoolExecutor(max_workers=min(3, len(rest))) as ex:
                list(ex.map(lambda i: _render_scene(dream_id, i, prompts[i], seed, anchor, palette, lock), rest))
    except Exception:  # noqa: BLE001
        log.exception("后台图片生成失败")
    db = SessionLocal()
    try:
        d = db.get(Dream, dream_id)
        if d:
            d.status = "generated"
            db.commit()
    finally:
        db.close()


# ----------------------------- 编排入口 -----------------------------
def weave_narrative(db, dream) -> None:
    """快速阶段：LLM 解析+织叙事，提交「无图叙事」并置 status=imaging；图片随后由 render_images 后台补齐。"""
    frag_text = _fragments_text(dream)
    user_emotion = next((e.label for e in dream.emotions if e.source == "user" and e.label), None)

    data = _weave_full(frag_text, user_emotion or "", dream)  # 单次 LLM（关思考）
    ai_emotions = data.get("emotions") or []
    primary = (ai_emotions[0].get("label") if ai_emotions else None) or user_emotion or "朦胧"
    woven = _normalize(data)
    palette = palette_for(primary)

    # 跨梦统一画风：首个梦确立风格，之后所有梦沿用 → 个人专属、可辨识的梦境视觉
    user = dream.user
    if user:
        if user.dream_style:
            woven["global_style"] = user.dream_style
        else:
            user.dream_style = woven["global_style"]

    for sc in woven["scenes"]:
        sc["image_url"] = None
        sc["asset_id"] = None

    # 重新生成：清理旧叙事与旧图
    if dream.narrative:
        db.delete(dream.narrative)
        db.flush()
    for a in list(dream.assets):
        try:
            if a.path:
                os.remove(os.path.join(ASSETS_DIR, a.path))
        except OSError:
            pass
        db.delete(a)
    db.flush()

    db.add(Narrative(
        dream_id=dream.id, title=woven["title"], global_style=woven["global_style"],
        scenes=woven["scenes"], closing_reflection=woven["closing_reflection"],
        model=woven.get("_model") or "fallback"))

    for e in list(dream.emotions):
        if e.source == "ai":
            db.delete(e)
    emo_list = ai_emotions[:3] if ai_emotions else [{"label": primary, "intensity": 0.6}]
    for em in emo_list:
        db.add(Emotion(dream_id=dream.id, label=str(em.get("label", ""))[:50],
                       intensity=float(em.get("intensity", 0.5) or 0.5), source="ai"))

    dream.title = woven["title"] or dream.title
    dream.primary_emotion = primary
    dream.palette = palette
    dream.status = "imaging"  # 叙事就绪、图片生成中
    db.commit()

"""梦境 CRUD、日历聚合与序列化。所有查询按 user_id 隔离（账号私有）。"""
from __future__ import annotations

import os
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, select

from app.core.config import settings
from app.models import Dream, DreamFragment, Emotion, User
from app.schemas import DreamCreate, DreamPatch
from app.services.orchestrator import ASSETS_DIR


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def create_dream(db, user_id: str, payload: DreamCreate) -> Dream:
    dream = Dream(
        user_id=user_id,
        dream_date=(payload.dream_date or _today())[:10],
        title=(payload.title or "未命名的梦")[:200],
        status="draft",
    )
    db.add(dream)
    db.flush()
    for i, frag in enumerate(payload.fragments):
        if frag.content.strip():
            db.add(DreamFragment(dream_id=dream.id, type=frag.type or "text",
                                 content=frag.content.strip(), order_index=i))
    if payload.emotion and payload.emotion.label:
        db.add(Emotion(dream_id=dream.id, label=payload.emotion.label[:50],
                       intensity=float(payload.emotion.intensity or 0.5), source="user"))
    db.commit()
    db.refresh(dream)
    return dream


def get_dream(db, user_id: str, dream_id: str) -> Dream:
    dream = db.get(Dream, dream_id)
    if not dream or dream.user_id != user_id:
        raise HTTPException(status_code=404, detail="梦境不存在")
    return dream


def list_dreams(db, user_id: str, limit: int = 50, offset: int = 0) -> list[Dream]:
    stmt = (select(Dream).where(Dream.user_id == user_id)
            .order_by(Dream.created_at.desc()).limit(limit).offset(offset))
    return list(db.execute(stmt).scalars())


def patch_dream(db, user_id: str, dream_id: str, patch: DreamPatch) -> Dream:
    dream = get_dream(db, user_id, dream_id)
    if patch.title is not None:
        dream.title = patch.title[:200]
    if patch.emotions is not None:
        for e in list(dream.emotions):
            if e.source == "user":
                db.delete(e)
        for em in patch.emotions:
            db.add(Emotion(dream_id=dream.id, label=em.label[:50],
                           intensity=float(em.intensity), source="user"))
    db.commit()
    db.refresh(dream)
    return dream


def delete_dream(db, user_id: str, dream_id: str) -> None:
    dream = get_dream(db, user_id, dream_id)
    for a in dream.assets:
        try:
            if a.path:
                os.remove(os.path.join(ASSETS_DIR, a.path))
        except OSError:
            pass
    db.delete(dream)
    db.commit()


def calendar(db, user_id: str, month: str) -> dict:
    """month: YYYY-MM。返回 {month, days:{date:{count,cover_image_url,primary_emotion}}}。"""
    stmt = (select(Dream).where(Dream.user_id == user_id, Dream.dream_date.like(f"{month}%"))
            .order_by(Dream.created_at.desc()))
    dreams = list(db.execute(stmt).scalars())
    days: dict[str, dict] = {}
    for d in dreams:
        day = days.setdefault(d.dream_date, {"count": 0, "cover_image_url": None,
                                             "primary_emotion": None, "dream_ids": []})
        day["count"] += 1
        day["dream_ids"].append(d.id)
        if not day["cover_image_url"]:
            day["cover_image_url"] = _cover(d)
            day["primary_emotion"] = d.primary_emotion
    return {"month": month, "days": days}


def _cover(dream: Dream) -> str | None:
    if dream.narrative and dream.narrative.scenes:
        for sc in dream.narrative.scenes:
            if sc.get("image_url"):
                return sc["image_url"]
    return None


def serialize(dream: Dream) -> dict:
    narr = dream.narrative
    return {
        "id": dream.id,
        "title": dream.title,
        "dream_date": dream.dream_date,
        "status": dream.status,
        "primary_emotion": dream.primary_emotion,
        "palette": dream.palette,
        "cover_image_url": _cover(dream),
        "created_at": dream.created_at.isoformat() if dream.created_at else None,
        "updated_at": dream.updated_at.isoformat() if dream.updated_at else None,
        "fragments": [
            {"id": f.id, "type": f.type, "content": f.content, "order_index": f.order_index}
            for f in dream.fragments
        ],
        "narrative": None if not narr else {
            "title": narr.title,
            "global_style": narr.global_style,
            "closing_reflection": narr.closing_reflection,
            "model": narr.model,
            "scenes": narr.scenes or [],
        },
        "emotions": [
            {"label": e.label, "intensity": e.intensity, "source": e.source}
            for e in dream.emotions
        ],
    }


def showcase(db) -> dict | None:
    """默认账号最新一条已生成的梦，公开展示。"""
    u = db.execute(
        select(User).where(func.lower(User.username) == settings.DEFAULT_USERNAME.lower())
    ).scalar_one_or_none()
    if not u:
        return None
    d = (db.execute(select(Dream).where(Dream.user_id == u.id, Dream.status == "generated")
                    .order_by(Dream.created_at.desc())).scalars().first())
    return serialize(d) if d else None


def insights(db, user_id: str) -> dict:
    """情绪分布、高频意象、按月分布。"""
    from collections import Counter
    dreams = list(db.execute(
        select(Dream).where(Dream.user_id == user_id).order_by(Dream.created_at)
    ).scalars())
    emo: Counter = Counter()
    imagery: Counter = Counter()
    months: Counter = Counter()
    for d in dreams:
        if d.primary_emotion:
            emo[d.primary_emotion] += 1
        if d.dream_date:
            months[d.dream_date[:7]] += 1
        if d.narrative and d.narrative.scenes:
            for sc in d.narrative.scenes:
                for e in (sc.get("recurring_entities") or []):
                    w = (e or "").strip()
                    if w:
                        imagery[w] += 1
    return {
        "total": len(dreams),
        "emotions": [{"label": k, "count": v} for k, v in emo.most_common(8)],
        "imagery": [{"word": k, "count": v} for k, v in imagery.most_common(14)],
        "by_month": [{"month": k, "count": v} for k, v in sorted(months.items())],
    }

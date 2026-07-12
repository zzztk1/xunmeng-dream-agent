"""SQLAlchemy 模型。

约定：主键统一使用 UUID 字符串，禁止自增主键（遵循项目规范）。
梦境归属于账号(user)；session 仅作浏览器会话→登录用户的映射。
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, ForeignKey,
                        Integer, String, Text)
from sqlalchemy.orm import relationship

from app.core.db import Base


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(32), primary_key=True, default=_uuid)
    username = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), default="")
    salt = Column(String(64), default="")
    display_name = Column(String(64), default="")
    is_guest = Column(Boolean, default=False)        # 游客账号（未注册）
    dream_style = Column(Text, default="")           # 跨梦统一画风契约（首梦确立）
    gen_date = Column(String(10), default="")        # 当日生成配额：日期
    gen_count = Column(Integer, default=0)           # 当日生成配额：次数
    created_at = Column(DateTime, default=_now)

    dreams = relationship("Dream", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(32), primary_key=True, default=_uuid)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=_now)
    last_seen_at = Column(DateTime, default=_now)


class Dream(Base):
    __tablename__ = "dreams"

    id = Column(String(32), primary_key=True, default=_uuid)
    user_id = Column(String(32), ForeignKey("users.id"), index=True, nullable=False)
    title = Column(String(200), default="未命名的梦")
    dream_date = Column(String(10), index=True)        # YYYY-MM-DD
    status = Column(String(20), default="draft")       # draft|generating|generated|failed
    primary_emotion = Column(String(50), nullable=True)
    palette = Column(JSON, nullable=True)              # {bg, colors[], accent}
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    user = relationship("User", back_populates="dreams")
    fragments = relationship("DreamFragment", back_populates="dream",
                            cascade="all, delete-orphan",
                            order_by="DreamFragment.order_index")
    narrative = relationship("Narrative", back_populates="dream", uselist=False,
                            cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="dream",
                          cascade="all, delete-orphan")
    emotions = relationship("Emotion", back_populates="dream",
                            cascade="all, delete-orphan")


class DreamFragment(Base):
    __tablename__ = "dream_fragments"

    id = Column(String(32), primary_key=True, default=_uuid)
    dream_id = Column(String(32), ForeignKey("dreams.id"), index=True, nullable=False)
    type = Column(String(20), default="text")          # text|voice|image|tag
    content = Column(Text, default="")
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=_now)

    dream = relationship("Dream", back_populates="fragments")


class Narrative(Base):
    __tablename__ = "narratives"

    id = Column(String(32), primary_key=True, default=_uuid)
    dream_id = Column(String(32), ForeignKey("dreams.id"), index=True, nullable=False)
    title = Column(String(200), default="")
    global_style = Column(Text, default="")            # 统一风格契约
    scenes = Column(JSON, default=list)                # [{text,visual_prompt,recurring_entities,ambient,image_url,asset_id}]
    closing_reflection = Column(Text, default="")
    model = Column(String(80), default="")
    created_at = Column(DateTime, default=_now)

    dream = relationship("Dream", back_populates="narrative")


class Asset(Base):
    __tablename__ = "assets"

    id = Column(String(32), primary_key=True, default=_uuid)
    dream_id = Column(String(32), ForeignKey("dreams.id"), index=True, nullable=False)
    type = Column(String(20), default="image")         # image|audio
    path = Column(String(300), default="")             # data/assets 下文件名
    prompt = Column(Text, default="")
    meta = Column(JSON, default=dict)                  # {mode,seed,ref_asset_id,strength,scene_index}
    created_at = Column(DateTime, default=_now)

    dream = relationship("Dream", back_populates="assets")


class Emotion(Base):
    __tablename__ = "emotions"

    id = Column(String(32), primary_key=True, default=_uuid)
    dream_id = Column(String(32), ForeignKey("dreams.id"), index=True, nullable=False)
    label = Column(String(50), default="")
    intensity = Column(Float, default=0.5)
    source = Column(String(20), default="ai")          # ai|user
    created_at = Column(DateTime, default=_now)

    dream = relationship("Dream", back_populates="emotions")

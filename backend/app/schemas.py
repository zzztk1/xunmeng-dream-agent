"""Pydantic 请求/响应契约。"""
from typing import Any, Optional

from pydantic import BaseModel, Field


class FragmentIn(BaseModel):
    type: str = "text"          # text|voice|image|tag
    content: str = ""


class EmotionInput(BaseModel):
    """记录页情绪输入：可给主标签+强度，或多轴滑块。"""
    label: Optional[str] = None
    intensity: Optional[float] = None
    axes: Optional[dict[str, float]] = None


class DreamCreate(BaseModel):
    fragments: list[FragmentIn] = Field(default_factory=list)
    emotion: Optional[EmotionInput] = None
    dream_date: Optional[str] = None      # YYYY-MM-DD，默认今天
    title: Optional[str] = None


class EmotionPatch(BaseModel):
    label: str
    intensity: float = 0.5


class DreamPatch(BaseModel):
    title: Optional[str] = None
    emotions: Optional[list[EmotionPatch]] = None   # 用户校准


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=128)
    display_name: Optional[str] = None


class LoginIn(BaseModel):
    username: str
    password: str

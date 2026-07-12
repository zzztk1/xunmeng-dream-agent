"""情绪 → 氛围（色板/音景）映射 + 降级用梦感渐变图生成。"""
from __future__ import annotations

import math

# 情绪桶：bg 背景色、colors 渐变色（由深到浅）、accent 点缀、ambient 音景标识
EMOTION_BUCKETS: dict[str, dict] = {
    "calm":    {"bg": "#0f1b2d", "colors": ["#16314a", "#2a6f7f", "#bfe3d0"], "accent": "#bfe3d0", "ambient": "water_pad", "zh": "平静"},
    "fear":    {"bg": "#0a0a14", "colors": ["#1a1030", "#3a1f5c", "#7d5ab0"], "accent": "#9d7bd8", "ambient": "low_drone", "zh": "不安"},
    "longing": {"bg": "#1d1413", "colors": ["#3a241f", "#7a4a3a", "#e0a070"], "accent": "#f0c08a", "ambient": "piano_wind", "zh": "怅惘"},
    "joy":     {"bg": "#1a1226", "colors": ["#4a2c6f", "#b05a9a", "#ffd1e0"], "accent": "#ffd1e0", "ambient": "chime", "zh": "轻盈"},
    "neutral": {"bg": "#11131f", "colors": ["#1e2235", "#3a4060", "#8a93c0"], "accent": "#aeb6e0", "ambient": "airy", "zh": "朦胧"},
}

# 中文情绪词 → 桶
_KEYWORDS = {
    "calm": ["平静", "安宁", "宁静", "平和", "安心", "放松", "温柔", "安详"],
    "fear": ["害怕", "恐惧", "不安", "焦虑", "紧张", "惊", "慌", "压抑", "危险", "逃"],
    "longing": ["留恋", "怅然", "思念", "想念", "孤独", "悲伤", "难过", "失落", "遗憾", "哀", "怀念", "不舍"],
    "joy": ["喜悦", "开心", "快乐", "兴奋", "幸福", "雀跃", "轻盈", "愉悦", "欢"],
}


def classify(label: str | None) -> str:
    if not label:
        return "neutral"
    for bucket, words in _KEYWORDS.items():
        if any(w in label for w in words):
            return bucket
    return "neutral"


def palette_for(label: str | None) -> dict:
    b = EMOTION_BUCKETS[classify(label)]
    return {"bg": b["bg"], "colors": b["colors"], "accent": b["accent"], "ambient": b["ambient"]}


def ambient_for(label: str | None) -> str:
    return EMOTION_BUCKETS[classify(label)]["ambient"]


def _rnd(seed: float, n: int) -> float:
    x = math.sin(seed * 12.9898 + n * 78.233) * 43758.5453
    return x - math.floor(x)


def gradient_svg(palette: dict, seed: int = 0, idx: int = 0) -> str:
    """生成梦感雾状渐变 SVG（降级/占位图）。同一梦共用 palette → 视觉连续。"""
    c = palette["colors"]
    bg = palette["bg"]
    accent = palette.get("accent", c[-1])
    s = seed + idx * 97
    cx1 = 20 + _rnd(s, 1) * 60
    cy1 = 18 + _rnd(s, 2) * 50
    cx2 = 25 + _rnd(s, 3) * 55
    cy2 = 45 + _rnd(s, 4) * 45
    r1 = 22 + _rnd(s, 5) * 14
    r2 = 14 + _rnd(s, 6) * 12
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" '
        'viewBox="0 0 100 100" preserveAspectRatio="xMidYMid slice">'
        '<defs>'
        f'<radialGradient id="g" cx="{cx1:.1f}%" cy="{cy1:.1f}%" r="85%">'
        f'<stop offset="0%" stop-color="{c[2]}" stop-opacity="0.85"/>'
        f'<stop offset="55%" stop-color="{c[1]}" stop-opacity="0.65"/>'
        f'<stop offset="100%" stop-color="{bg}" stop-opacity="1"/>'
        '</radialGradient>'
        '<filter id="b" x="-30%" y="-30%" width="160%" height="160%">'
        '<feGaussianBlur stdDeviation="5"/></filter>'
        '</defs>'
        f'<rect width="100" height="100" fill="{bg}"/>'
        f'<rect width="100" height="100" fill="url(#g)"/>'
        f'<circle cx="{cx2:.1f}" cy="{cy2:.1f}" r="{r1:.1f}" fill="{accent}" opacity="0.22" filter="url(#b)"/>'
        f'<circle cx="{cx1:.1f}" cy="{cy2:.1f}" r="{r2:.1f}" fill="{c[1]}" opacity="0.30" filter="url(#b)"/>'
        f'<circle cx="{cx2:.1f}" cy="{cy1:.1f}" r="{r2*0.8:.1f}" fill="{c[2]}" opacity="0.18" filter="url(#b)"/>'
        '</svg>'
    )

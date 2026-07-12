"""LLM 提示词模板：梦境解析（LLM-A）与叙事编织（LLM-B）。"""
from __future__ import annotations

ANALYZE_SYSTEM = (
    "你是「寻梦」的梦境分析助手。用户给出若干零散的梦境碎片，"
    "请抽取关键要素并分析情绪。严格只输出 JSON，不要解释、不要 markdown。"
)

WEAVE_SYSTEM = (
    "你是「寻梦」的织梦师。你的任务是把零散的梦境碎片，编织成一段第二人称、"
    "带有梦的断裂感与情绪连续性的梦境叙事，并拆成 2–4 个场景。\n"
    "硬性要求：\n"
    "1) 必须保留用户碎片中的关键意象、人物、地点、身体感受；\n"
    "2) 不得新增与碎片相矛盾的设定；\n"
    "3) 语气温柔、克制，让人感到被理解、被接住；\n"
    "4) 为保证「同一个梦」的多张图视觉连续，请给出统一的 global_style，"
    "并对反复出现的人物/意象用固定规范措辞写入每个场景的 recurring_entities。\n"
    "严格只输出 JSON，不要解释、不要 markdown。"
)


WEAVE_FULL_SYSTEM = (
    "你是「寻梦」的织梦师。把用户零散的梦境碎片，一次性编织成第二人称、带梦的断裂感与"
    "情绪连续性的梦境叙事，并拆成 2–4 个场景；同时分析这个梦的情绪。\n"
    "硬性要求：\n"
    "1) 保留碎片中的关键意象、人物、地点、身体感受，不得新增与碎片矛盾的设定；\n"
    "2) 语气温柔、克制，让人感到被理解、被接住；\n"
    "3) 为保证「同一个梦」多张图视觉连续，给出统一 global_style，并对反复出现的人物/意象用"
    "固定规范措辞写入每个场景的 recurring_entities。\n"
    "严格只输出 JSON，不要解释、不要 markdown。"
)


def weave_full_user_prompt(fragments_text: str, user_emotion: str) -> str:
    return (
        f"梦境碎片（逐条）：\n{fragments_text}\n\n"
        f"用户标注的情绪：{user_emotion or '（未标注）'}\n\n"
        "请输出 JSON：\n"
        "{\n"
        '  "title": "≤12字标题",\n'
        '  "global_style": "统一视觉风格：媒介/色调/光线/质感（用于所有场景图，保证连续）",\n'
        '  "emotions": [{"label": "中文情绪词", "intensity": 0.0}],\n'
        '  "scenes": [\n'
        '    {"text": "该场景叙事 60~120字，第二人称，有断裂感",\n'
        '     "visual_prompt": "画面：主体/环境/氛围/构图，可直接用于文生图与图生图",\n'
        '     "recurring_entities": ["反复出现的人物或意象的唯一规范描述，逐字复用"],\n'
        '     "ambient": "氛围词"}\n'
        "  ],\n"
        '  "closing_reflection": "一句温柔的情绪安放话，第二人称，≤40字"\n'
        "}\n"
        "emotions 按显著度排序、intensity 取 0~1；scenes 给 2~4 个，按梦的推进排序。"
    )


def analyze_user_prompt(fragments_text: str) -> str:
    return (
        f"梦境碎片（逐条）：\n{fragments_text}\n\n"
        "请输出 JSON：\n"
        "{\n"
        '  "imagery": ["关键意象"],\n'
        '  "characters": ["人物"],\n'
        '  "places": ["地点"],\n'
        '  "sensations": ["身体感受"],\n'
        '  "emotions": [{"label": "中文情绪词", "intensity": 0.0}],\n'
        '  "summary": "一句话概括这个梦"\n'
        "}\n"
        "emotions 按显著程度排序，intensity 取 0~1。"
    )


def weave_user_prompt(fragments_text: str, analysis: dict, primary_emotion: str) -> str:
    import json
    return (
        f"原始碎片：\n{fragments_text}\n\n"
        f"已抽取要素：{json.dumps(analysis, ensure_ascii=False)}\n"
        f"主导情绪：{primary_emotion}\n\n"
        "请输出 JSON：\n"
        "{\n"
        '  "title": "≤12字的梦境标题",\n'
        '  "global_style": "统一视觉风格描述：媒介/色调/光线/质感（用于所有场景图，保证连续）",\n'
        '  "scenes": [\n'
        '    {\n'
        '      "text": "该场景的梦境叙事，60~120字，第二人称，有断裂感",\n'
        '      "visual_prompt": "画面描述：主体/环境/氛围/构图，可直接用于文生图与图生图",\n'
        '      "recurring_entities": ["反复出现的人物或意象的唯一规范描述，逐字复用"],\n'
        '      "ambient": "氛围词，如 静谧/不安/怅惘/轻盈"\n'
        "    }\n"
        "  ],\n"
        '  "closing_reflection": "一句温柔的情绪安放话，第二人称，≤40字"\n'
        "}\n"
        "scenes 给 2~4 个，按梦的推进排序。"
    )

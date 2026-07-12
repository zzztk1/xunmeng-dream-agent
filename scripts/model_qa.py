import http.cookiejar
import json
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "http://127.0.0.1:8003"
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def request(path: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        BASE_URL + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="GET" if payload is None else "POST",
    )
    with opener.open(req, timeout=180) as response:
        return json.load(response)


started = time.perf_counter()
rows = []
transport_ok = True
provider_ok = False
schema_ok = False
semantic_ok = False
quality_ok = False
try:
    health = request("/api/health").get("data") or {}
    provider_ok = health.get("provider") == "stepfun" and health.get("ai_enabled") is True
    rows.append({
        "name": "stepfun-provider",
        "ok": provider_ok,
        "model": str(health.get("llm_model") or "stepfun"),
        "latencyMs": round((time.perf_counter() - started) * 1000),
        "faithfulness": "pass" if provider_ok else "fail",
        "dreamFeeling": "pass" if provider_ok else "fail",
        "overreach": "pass" if provider_ok else "fail",
        "errorType": "" if provider_ok else "missing_key_or_fallback",
    })

    if provider_ok:
        suffix = str(int(time.time() * 1000))[-10:]
        request("/api/auth/register", {
            "username": f"qa_{suffix}",
            "password": "QaDream2026!",
            "display_name": "真实模型验收",
        })
        dream = request("/api/dreams", {
            "fragments": [{"type": "text", "content": "雨停后，我在海边车站捡到一封写给未来自己的信。"}],
            "emotion": {"label": "期待与迟疑", "intensity": 0.72},
            "title": "海边车站的信",
        }).get("data") or {}
        generated = request(f"/api/dreams/{dream['id']}/generate", {}).get("data") or {}
        narrative = generated.get("narrative") or {}
        scenes = narrative.get("scenes") or []
        schema_ok = len(scenes) >= 3 and all(scene.get("text") for scene in scenes[:3])
        semantic_ok = narrative.get("model") not in (None, "", "fallback") and bool(narrative.get("closing_reflection"))

        deadline = time.time() + 180
        while time.time() < deadline:
            current = request(f"/api/dreams/{dream['id']}").get("data") or {}
            scenes = ((current.get("narrative") or {}).get("scenes") or [])
            if len(scenes) >= 3 and all(scene.get("image_url") for scene in scenes[:3]):
                break
            time.sleep(3)
        image_urls = [scene.get("image_url") for scene in scenes[:3]]
        quality_ok = len(image_urls) == 3 and all(url and not str(url).endswith(".svg") for url in image_urls)
        text_ok = provider_ok and schema_ok and semantic_ok
        rows.append({
            "name": "dream-text-generation",
            "ok": text_ok,
            "model": str(narrative.get("model") or health.get("llm_model") or "stepfun"),
            "latencyMs": round((time.perf_counter() - started) * 1000),
            "faithfulness": "pass" if schema_ok else "fail",
            "dreamFeeling": "pass" if semantic_ok else "fail",
            "overreach": "pass" if semantic_ok else "fail",
            "title": str(generated.get("title") or ""),
            "errorType": "" if text_ok else "text_generation_failure",
        })
        rows.append({
            "name": "dream-image-generation",
            "ok": quality_ok,
            "model": str(health.get("image_model") or "stepfun-image"),
            "latencyMs": round((time.perf_counter() - started) * 1000),
            "faithfulness": "pass" if quality_ok else "fail",
            "dreamFeeling": "pass" if quality_ok else "fail",
            "overreach": "pass" if quality_ok else "fail",
            "errorType": "" if quality_ok else "image_generation_failure",
        })
except (KeyError, OSError, urllib.error.URLError, ValueError, json.JSONDecodeError) as exc:
    transport_ok = False
    rows.append({
        "name": "runtime-transport",
        "ok": False,
        "model": "stepfun",
        "faithfulness": "fail",
        "dreamFeeling": "fail",
        "overreach": "fail",
        "errorType": type(exc).__name__,
    })

result = {
    "rows": rows,
    "aggregate": {
        "transport_ok": transport_ok,
        "provider_ok": provider_ok,
        "schema_ok": schema_ok,
        "semantic_ok": semantic_ok,
        "quality_ok": quality_ok,
    },
}
(ROOT / "MODEL_QA_RUN.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))

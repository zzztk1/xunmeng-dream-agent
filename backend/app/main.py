"""寻梦后端入口。"""
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import BASE_DIR, settings
from app.core.db import SessionLocal, init_db
from app.models import Session as SessionModel
from app.routers import auth as auth_router
from app.routers import dreams as dreams_router

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("main")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    # 播种网站内置默认账号
    from app.services.auth import ensure_default_user
    _db = SessionLocal()
    try:
        ensure_default_user(_db)
    finally:
        _db.close()
    log.info("DB 就绪；AI %s（LLM=%s, IMAGE=%s/%s）",
             "已启用" if settings.ai_enabled else "降级模式(未配置 STEPFUN_API_KEY)",
             settings.LLM_MODEL, settings.image_provider, settings.image_model)
    yield


app = FastAPI(title="寻梦 API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def session_middleware(request: Request, call_next):
    # 仅 /api 路径需要会话；静态资源跳过
    if not request.url.path.startswith("/api"):
        return await call_next(request)
    sid = request.cookies.get("sid")
    is_new = False
    if not sid:
        sid = uuid.uuid4().hex
        is_new = True
    request.state.sid = sid
    db = SessionLocal()
    try:
        s = db.get(SessionModel, sid)
        if not s:
            db.add(SessionModel(id=sid))
            db.commit()
        else:
            s.last_seen_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()
    response = await call_next(request)
    if is_new:
        response.set_cookie("sid", sid, max_age=60 * 60 * 24 * 365,
                            httponly=True, samesite="lax")
    return response


@app.get("/api/health")
def health():
    return {"code": 0, "data": {
        "provider": "stepfun" if settings.ai_enabled else "fallback",
        "text_provider": "stepfun" if settings.ai_enabled else "fallback",
        "ai_enabled": settings.ai_enabled,
        "llm_model": settings.LLM_MODEL,
        "image_provider": settings.image_provider,
        "image_enabled": settings.image_enabled,
        "image_model": settings.image_model,
    }}


app.include_router(auth_router.router)
app.include_router(dreams_router.router)

# 生成的图/音静态服务
ASSETS_DIR = os.path.join(BASE_DIR, "data", "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)
app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

# 生产：托管前端构建产物（开发用 Vite，不依赖此处）
_FRONT_DIST = os.path.normpath(os.path.join(BASE_DIR, "..", "frontend", "dist"))
if os.path.isdir(_FRONT_DIST):
    app.mount("/", StaticFiles(directory=_FRONT_DIST, html=True), name="frontend")

"""梦境端点（账号私有）。注意路由顺序：/dreams/calendar 须在 /dreams/{id} 之前。"""
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request

from app.core.db import get_db
from app.models import User
from app.schemas import DreamCreate, DreamPatch
from app.services import auth as auth_svc
from app.services import dreams as svc
from app.services import orchestrator

log = logging.getLogger("routers.dreams")
router = APIRouter(prefix="/api", tags=["dreams"])


def require_user(request: Request, db=Depends(get_db)) -> User:
    user = auth_svc.current_user(db, request.state.sid)
    if not user:
        raise HTTPException(status_code=401, detail="请先登录")
    return user


def current_or_guest(request: Request, db=Depends(get_db)) -> User:
    """记录梦境无需登录：未登录则自动创建游客账号（注册后认领）。"""
    return auth_svc.get_or_create_guest(db, request.state.sid)


@router.post("/dreams")
def create_dream(payload: DreamCreate, db=Depends(get_db), user: User = Depends(current_or_guest)):
    dream = svc.create_dream(db, user.id, payload)
    return {"code": 0, "data": svc.serialize(dream)}


def _run_generate(dream_id: str, db, user: User, background_tasks: BackgroundTasks):
    dream = svc.get_dream(db, user.id, dream_id)
    auth_svc.check_quota(db, user)  # 每日生成配额，超额 429
    try:
        dream.status = "weaving"
        db.commit()
        orchestrator.weave_narrative(db, dream)  # 快：返回叙事
    except Exception as e:  # noqa: BLE001
        db.rollback()
        log.exception("织梦失败")
        try:
            d = svc.get_dream(db, user.id, dream_id)
            d.status = "failed"
            db.commit()
        except Exception:  # noqa: BLE001
            pass
        raise HTTPException(status_code=500, detail=f"生成失败：{e}")
    # 图片后台逐张生成（前端轮询渐进显示）
    background_tasks.add_task(orchestrator.render_images, dream.id)
    db.refresh(dream)
    return {"code": 0, "data": svc.serialize(dream)}


@router.post("/dreams/{dream_id}/generate")
def generate_dream(dream_id: str, background_tasks: BackgroundTasks,
                   db=Depends(get_db), user: User = Depends(require_user)):
    return _run_generate(dream_id, db, user, background_tasks)


@router.post("/dreams/{dream_id}/regenerate")
def regenerate_dream(dream_id: str, background_tasks: BackgroundTasks,
                     db=Depends(get_db), user: User = Depends(require_user)):
    return _run_generate(dream_id, db, user, background_tasks)


@router.get("/dreams")
def list_dreams(db=Depends(get_db), user: User = Depends(require_user),
                limit: int = Query(50, le=200), offset: int = 0):
    items = svc.list_dreams(db, user.id, limit, offset)
    return {"code": 0, "data": [svc.serialize(d) for d in items]}


@router.get("/dreams/calendar")
def calendar(month: str, db=Depends(get_db), user: User = Depends(require_user)):
    return {"code": 0, "data": svc.calendar(db, user.id, month)}


@router.get("/dreams/{dream_id}")
def get_dream(dream_id: str, db=Depends(get_db), user: User = Depends(require_user)):
    dream = svc.get_dream(db, user.id, dream_id)
    return {"code": 0, "data": svc.serialize(dream)}


@router.patch("/dreams/{dream_id}")
def patch_dream(dream_id: str, patch: DreamPatch, db=Depends(get_db), user: User = Depends(require_user)):
    dream = svc.patch_dream(db, user.id, dream_id, patch)
    return {"code": 0, "data": svc.serialize(dream)}


@router.delete("/dreams/{dream_id}")
def delete_dream(dream_id: str, db=Depends(get_db), user: User = Depends(require_user)):
    svc.delete_dream(db, user.id, dream_id)
    return {"code": 0, "data": {"deleted": dream_id}}


@router.get("/showcase")
def showcase(db=Depends(get_db)):
    """公开样例梦（默认账号最新一条已生成的梦），免登录展示。"""
    return {"code": 0, "data": svc.showcase(db)}


@router.get("/insights")
def insights(db=Depends(get_db), user: User = Depends(require_user)):
    return {"code": 0, "data": svc.insights(db, user.id)}

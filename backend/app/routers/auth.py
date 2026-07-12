"""账号端点：注册 / 登录 / 登出 / 当前用户。"""
from fastapi import APIRouter, Depends, Request

from app.core.db import get_db
from app.schemas import LoginIn, RegisterIn
from app.services import auth as svc

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
def register(payload: RegisterIn, request: Request, db=Depends(get_db)):
    # 游客注册即「升级」其账号，保留已做的梦
    user = svc.register_or_upgrade(db, request.state.sid, payload.username, payload.password, payload.display_name)
    return {"code": 0, "data": svc.serialize_user(user)}


@router.post("/login")
def login(payload: LoginIn, request: Request, db=Depends(get_db)):
    # 登录时认领游客已做的梦
    user = svc.login_claim(db, request.state.sid, payload.username, payload.password)
    return {"code": 0, "data": svc.serialize_user(user)}


@router.post("/logout")
def logout(request: Request, db=Depends(get_db)):
    svc.bind_session(db, request.state.sid, None)
    return {"code": 0, "data": {"ok": True}}


@router.get("/me")
def me(request: Request, db=Depends(get_db)):
    user = svc.current_user(db, request.state.sid)
    return {"code": 0, "data": svc.serialize_user(user) if user else None}

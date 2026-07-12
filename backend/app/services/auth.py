"""账号：注册 / 登录 / 会话绑定。密码用 pbkdf2_hmac(sha256) + 每用户 salt。"""
from __future__ import annotations

import hashlib
import secrets

import logging

from fastapi import HTTPException
from sqlalchemy import func, select

from app.core.config import settings
from app.models import Session, User

log = logging.getLogger("auth")

_ITER = 120_000


def _hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _ITER).hex()


def hash_password(password: str) -> tuple[str, str]:
    salt = secrets.token_hex(16)
    return _hash(password, salt), salt


def verify_password(password: str, salt: str, expected: str) -> bool:
    return secrets.compare_digest(_hash(password, salt), expected)


def serialize_user(u: User) -> dict:
    return {
        "id": u.id,
        "username": u.username,
        "display_name": u.display_name or u.username,
        "is_guest": bool(u.is_guest),
    }


def register(db, username: str, password: str, display_name: str | None) -> User:
    username = username.strip()
    exists = db.execute(
        select(User).where(func.lower(User.username) == username.lower())
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="该用户名已被使用")
    pwd_hash, salt = hash_password(password)
    user = User(username=username, password_hash=pwd_hash, salt=salt,
                display_name=(display_name or "").strip() or username)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db, username: str, password: str) -> User:
    user = db.execute(
        select(User).where(func.lower(User.username) == username.strip().lower())
    ).scalar_one_or_none()
    if not user or not verify_password(password, user.salt, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码不正确")
    return user


def bind_session(db, sid: str, user_id: str | None) -> None:
    """把当前浏览器会话绑定到用户（登录/注册）或解绑（登出）。"""
    s = db.get(Session, sid)
    if not s:
        s = Session(id=sid)
        db.add(s)
    s.user_id = user_id
    db.commit()


def current_user(db, sid: str) -> User | None:
    s = db.get(Session, sid)
    if s and s.user_id:
        return db.get(User, s.user_id)
    return None


def ensure_default_user(db) -> None:
    """启动时播种网站内置默认账号（配置于 config.env），已存在则跳过。"""
    username = (settings.DEFAULT_USERNAME or "").strip()
    password = settings.DEFAULT_PASSWORD or ""
    if not username or not password:
        return
    exists = db.execute(
        select(User).where(func.lower(User.username) == username.lower())
    ).scalar_one_or_none()
    if exists:
        return
    pwd_hash, salt = hash_password(password)
    db.add(User(username=username, password_hash=pwd_hash, salt=salt, display_name=username))
    db.commit()
    log.info("已创建默认账号: %s", username)


def get_or_create_guest(db, sid: str) -> User:
    """游客：会话已绑用户则返回，否则自动创建游客账号并绑定（用于免登录试做）。"""
    s = db.get(Session, sid)
    if s and s.user_id:
        u = db.get(User, s.user_id)
        if u:
            return u
    guest = User(username=f"guest-{sid[:12]}", is_guest=True, display_name="游客")
    db.add(guest)
    db.flush()
    if not s:
        s = Session(id=sid)
        db.add(s)
    s.user_id = guest.id
    db.commit()
    db.refresh(guest)
    return guest


def register_or_upgrade(db, sid: str, username: str, password: str, display_name: str | None) -> User:
    """注册：若当前是游客则「升级」该账号（保留其已做的梦），否则新建。"""
    username = username.strip()
    cur = current_user(db, sid)
    if cur and cur.is_guest:
        clash = db.execute(
            select(User).where(func.lower(User.username) == username.lower(), User.id != cur.id)
        ).scalar_one_or_none()
        if clash:
            raise HTTPException(status_code=409, detail="该用户名已被使用")
        pwd_hash, salt = hash_password(password)
        cur.username = username
        cur.password_hash = pwd_hash
        cur.salt = salt
        cur.display_name = (display_name or "").strip() or username
        cur.is_guest = False
        db.commit()
        db.refresh(cur)
        return cur
    user = register(db, username, password, display_name)
    bind_session(db, sid, user.id)
    return user


def login_claim(db, sid: str, username: str, password: str) -> User:
    """登录：若当前游客有梦，认领到目标账号后再切换。"""
    target = authenticate(db, username, password)
    s = db.get(Session, sid)
    cur = db.get(User, s.user_id) if (s and s.user_id) else None
    if cur and cur.is_guest and cur.id != target.id:
        for d in list(cur.dreams):
            d.user_id = target.id
        db.flush()
        db.delete(cur)
    if not s:
        s = Session(id=sid)
        db.add(s)
    s.user_id = target.id
    db.commit()
    return target


def check_quota(db, user: User, *, cap_user: int = 60, cap_guest: int = 5) -> None:
    """每用户每日生成配额（防刷控成本）。超额抛 429。"""
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    if user.gen_date != today:
        user.gen_date = today
        user.gen_count = 0
    cap = cap_guest if user.is_guest else cap_user
    if (user.gen_count or 0) >= cap:
        db.commit()
        raise HTTPException(status_code=429, detail="今日生成次数已达上限，明天再来，或注册解锁更多。")
    user.gen_count = (user.gen_count or 0) + 1
    db.commit()

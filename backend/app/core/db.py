"""数据库引擎与会话。默认 SQLite（零依赖，利于稳定演示）。"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import BASE_DIR, settings


def _resolve_url(url: str) -> str:
    """SQLite 相对路径解析到 backend/ 下，并确保目录存在。"""
    prefix = "sqlite:///"
    if url.startswith(prefix):
        path = url[len(prefix):]
        if not os.path.isabs(path):
            path = os.path.normpath(os.path.join(BASE_DIR, path))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return prefix + path
    return url


DATABASE_URL = _resolve_url(settings.DATABASE_URL)
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def _ensure_columns() -> None:
    """轻量迁移：为已存在的表补齐新增列（SQLite ADD COLUMN），避免改 schema 删库。"""
    from sqlalchemy import inspect, text
    insp = inspect(engine)
    if "users" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("users")}
    wanted = {
        "is_guest": "BOOLEAN DEFAULT 0",
        "dream_style": "TEXT DEFAULT ''",
        "gen_date": "VARCHAR(10) DEFAULT ''",
        "gen_count": "INTEGER DEFAULT 0",
    }
    missing = [(c, d) for c, d in wanted.items() if c not in cols]
    if missing:
        with engine.begin() as conn:
            for c, d in missing:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {c} {d}"))


def init_db() -> None:
    import app.models  # noqa: F401  确保模型注册到 Base.metadata
    Base.metadata.create_all(bind=engine)
    _ensure_columns()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

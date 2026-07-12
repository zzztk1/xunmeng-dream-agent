# 寻梦后端

FastAPI + SQLAlchemy + SQLite 的梦境编织服务。

## 能力

- 注册、登录、访客会话和数据隔离。
- 梦境碎片、情绪、叙事、场景资源和日历查询。
- StepFun 文本生成与默认图片生成适配。
- 可通过 `IMAGE_PROVIDER=volcano` 切换到独立的火山方舟 SeedDream 图片接口。
- 生成图片立即下载到 backend/data/assets，前端不依赖临时 URL。
- 未配置密钥时使用明确的本地 fallback。

## 启动

    py -m venv .venv
    .\.venv\Scripts\pip install -r requirements.txt
    .\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8003

环境变量见 config.env.example。真实密钥只允许通过进程环境或本机加密配置注入。火山图片密钥使用 `VOLCANO_API_KEY`，不得与 `STEPFUN_API_KEY` 混用。

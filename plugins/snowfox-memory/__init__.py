"""SnowFox 五级记忆 L1 写入插件。

每次 LLM 调用完成后（post_llm_call），将用户输入 + 助手回复
写入 memories/recent/ 目录，作为 L1 近期流。
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── 缓存 HERMES_HOME ──────────────────────────────────────────────
def _hermes_home() -> Path:
    """解析 HERMES_HOME 环境变量或默认路径。"""
    env = __import__("os").environ.get("HERMES_HOME")
    if env:
        return Path(env)
    return Path.home() / "AppData" / "Local" / "hermes"


def register(ctx) -> None:
    """注册 post_llm_call 钩子。"""
    ctx.register_hook("post_llm_call", _on_post_llm_call)
    logger.info("snowfox-memory: post_llm_call hook registered")


def _on_post_llm_call(
    session_id: str = "",
    task_id: str = "",
    turn_id: str = "",
    user_message: str = "",
    assistant_response: str = "",
    conversation_history: list = None,
    model: str = "",
    platform: str = "",
    **_: Any,
) -> None:
    """将本轮对话写入 L1 (memories/recent/)。"""
    try:
        l1_dir = _hermes_home() / "memories" / "recent"
        l1_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 截取用户消息前 40 字符做文件名预览
        safe = "".join(
            c for c in (user_message or "")[:80] if c.isalnum() or c in " _-."
        ).strip() or "turn"
        fname = f"{ts}_{turn_id or '0'}_{safe[:40]}.md"
        path = l1_dir / fname

        path.write_text(
            f"## User\n\n{user_message or ''}\n\n"
            f"## Assistant\n\n{assistant_response or ''}\n\n",
            encoding="utf-8",
        )
        logger.debug("snowfox-memory: wrote %s (%d B)", fname, path.stat().st_size)
    except Exception as exc:
        logger.warning("snowfox-memory: failed to write L1: %s", exc)

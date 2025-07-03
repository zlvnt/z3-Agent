"""
Supervisor sederhana: memetakan 'task' → fungsi agent.

Saat ini:
 task == "reply"   ➜ agents.reply.generate_reply()

Jika di masa depan ada caption atau search, cukup tambahkan di `TASK_MAP`.
"""

from __future__ import annotations
from typing import Any, Callable

from app.services.logger import logger
from app.agents.reply import generate_reply

TASK_MAP: dict[str, Callable[..., str]] = {
    "reply": generate_reply,
    # "caption": generate_caption,   # contoh ekspansi berikutnya
}


def handle(task: str, **kwargs: Any) -> str:
    """
    Delegasikan task ke agen yang tepat.
    Raise KeyError jika task tidak dikenali.
    """
    if task not in TASK_MAP:
        raise KeyError(f"Unknown task '{task}'")

    logger.debug("Router dispatch", task=task)
    return TASK_MAP[task](**kwargs)

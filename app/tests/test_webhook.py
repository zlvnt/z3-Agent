import types
import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Minimal environment so settings import succeeds
os.environ.setdefault("INSTAGRAM_ACCESS_TOKEN", "x")
os.environ.setdefault("INSTAGRAM_ACCOUNT_ID", "x")
os.environ.setdefault("VERIFY_TOKEN", "x")
os.environ.setdefault("MODEL_NAME", "gemini")

# Stub modules used inside webhook to avoid heavy deps
stub_router = types.ModuleType("app.agents.router")
stub_router.handle = lambda *a, **k: "OK"
sys.modules.setdefault("app.agents.router", stub_router)
stub_ig = types.ModuleType("app.services.instagram_api")
stub_ig.upload_reply = lambda *a, **k: None
sys.modules.setdefault("app.services.instagram_api", stub_ig)
stub_logger = types.ModuleType("app.services.logger")
class _L:
    def __getattr__(self, _):
        return lambda *a, **k: None
stub_logger.logger = _L()
sys.modules.setdefault("app.services.logger", stub_logger)

from app.api import webhook as webhook_module

# Regression test for webhook processing no TypeError

def test_process_payload_no_type_error(monkeypatch):
    calls = {}

    def fake_handle(comment, post_id, comment_id, username, **kwargs):
        calls['handle'] = (comment, post_id, comment_id, username)
        return "OK"

    def fake_upload_reply(comment_id, reply_txt):
        calls['upload'] = (comment_id, reply_txt)

    fake_settings = types.SimpleNamespace(BOT_USERNAME="bot")

    monkeypatch.setattr(webhook_module, "handle", fake_handle)
    monkeypatch.setattr(webhook_module, "upload_reply", fake_upload_reply)
    monkeypatch.setattr(webhook_module, "settings", fake_settings)

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "field": "comments",
                        "value": {
                            "text": "hello",
                            "id": "c123",
                            "media": {"id": "m456"},
                            "from": {"username": "user1"},
                        },
                    }
                ]
            }
        ]
    }

    # Should not raise an exception
    webhook_module._process_payload(payload)

    assert calls["handle"] == ("hello", "m456", "c123", "user1")
    assert calls["upload"] == ("c123", "OK")
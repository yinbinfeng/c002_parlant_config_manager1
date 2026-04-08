from __future__ import annotations

from mining_agents.utils import logger as logger_mod


class _DummyStream:
    def __init__(self) -> None:
        self.reconfigure_calls: list[dict] = []

    def reconfigure(self, **kwargs) -> None:
        self.reconfigure_calls.append(kwargs)

    def write(self, _text: str) -> int:
        return 0

    def flush(self) -> None:
        return None


def test_configure_logging_reconfigure_stdio_utf8(monkeypatch):
    stderr = _DummyStream()
    stdout = _DummyStream()
    monkeypatch.setattr(logger_mod.sys, "stderr", stderr)
    monkeypatch.setattr(logger_mod.sys, "stdout", stdout)

    # 确保幂等签名不短路本次调用
    monkeypatch.setattr(logger_mod, "_CONFIGURED_SIGNATURE", None)

    logger_mod.configure_logging(level="INFO")

    assert stderr.reconfigure_calls, "stderr 应被 reconfigure 为 utf-8"
    assert stdout.reconfigure_calls, "stdout 应被 reconfigure 为 utf-8"
    assert stderr.reconfigure_calls[-1].get("encoding") == "utf-8"
    assert stdout.reconfigure_calls[-1].get("encoding") == "utf-8"

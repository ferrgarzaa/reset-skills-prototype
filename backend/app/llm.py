"""Model access. Only the backend talks to the model.

Modes (LLM_MODE env var, or the dev switch):
- mock: deterministic saved responses, no API calls (default, used for tests)
- live: Anthropic API, limited to LLM_CALL_LIMIT calls per server run, then mock
- fail: every call raises, to test fallbacks
"""
import json
import os
import time
from pathlib import Path

from . import db

HERE = Path(__file__).resolve().parent
MOCKS = json.loads((HERE / "mock_responses.json").read_text())
JOURNAL_SYSTEM = (HERE / "prompts" / "journal_system.md").read_text()
SHORT_SYSTEM = (HERE / "prompts" / "short_lines_system.md").read_text()


class LLMError(Exception):
    pass


class _State:
    mode = None  # set lazily from env
    live_calls = 0
    mock_counter = 0


def get_mode() -> str:
    if _State.mode is None:
        env = os.getenv("LLM_MODE", "").strip().lower()
        if env in ("mock", "live", "fail"):
            _State.mode = env
        else:
            _State.mode = "live" if os.getenv("ANTHROPIC_API_KEY") else "mock"
    return _State.mode


def set_mode(mode: str) -> None:
    if mode not in ("mock", "live", "fail"):
        raise ValueError(mode)
    _State.mode = mode


def call_limit() -> int:
    return int(os.getenv("LLM_CALL_LIMIT", "50"))


def status() -> dict:
    return {
        "mode": get_mode(),
        "model": os.getenv("MODEL_ID", "claude-haiku-5-5"),
        "live_calls": _State.live_calls,
        "call_limit": call_limit(),
    }


def _mock(purpose: str, messages: list[dict], usual: bool = False) -> str:
    _State.mock_counter += 1
    i = _State.mock_counter
    if purpose == "journal":
        last = messages[-1]["content"].lower() if messages else ""
        for rule in MOCKS["journal"]["rules"]:
            if any(w in last for w in rule["match"]):
                return rule["reply"]
        d = MOCKS["journal"]["default"]
        return d[i % len(d)]
    key = "closing_usual" if (purpose == "closing" and usual) else purpose
    options = MOCKS[key]
    return options[i % len(options)]


def _live(system: str, messages: list[dict], max_tokens: int, timeout: float) -> str:
    import anthropic  # imported here so mock mode works without the package configured

    client = anthropic.Anthropic(timeout=timeout, max_retries=0)
    resp = client.messages.create(
        model=os.getenv("MODEL_ID", "claude-haiku-5-5"),
        system=system,
        max_tokens=max_tokens,
        messages=messages,
    )
    return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()


def generate(purpose: str, messages: list[dict], system: str, max_tokens: int,
             timeout: float, usual: bool = False) -> tuple[str, str]:
    """Return (text, source) where source is 'model' or 'mock'. Raises LLMError."""
    mode = get_mode()
    if mode == "live" and _State.live_calls >= call_limit():
        mode = "mock"  # call limit reached, fall back to saved responses
    start = time.monotonic()
    try:
        if mode == "fail":
            raise LLMError("simulated model failure (LLM_MODE=fail)")
        if mode == "mock":
            text, source = _mock(purpose, messages, usual), "mock"
        else:
            _State.live_calls += 1
            text, source = _live(system, messages, max_tokens, timeout), "model"
        db.log_llm_call(purpose, mode, True, int((time.monotonic() - start) * 1000))
        return text, source
    except LLMError as e:
        db.log_llm_call(purpose, mode, False, int((time.monotonic() - start) * 1000), str(e))
        raise
    except Exception as e:  # timeouts, network, API errors
        db.log_llm_call(purpose, mode, False, int((time.monotonic() - start) * 1000),
                        f"{type(e).__name__}: {e}"[:300])
        raise LLMError(str(e)) from e

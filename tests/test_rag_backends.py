import httpx
import pytest

from retraction_bench.rag.backends import (
    GROQ_MODEL,
    MAX_RETRY_DELAY,
    OLLAMA_MODELS,
    BackendFatalError,
    BackendRetryableError,
    _retry_delay,
    call_groq,
    call_ollama,
    resolve_backend,
)


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_call_groq_returns_content_not_reasoning(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {"content": "ANSWER: Yes.", "reasoning": "long chain of thought"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"total_tokens": 42},
            },
        )

    text, usage = call_groq("prompt", GROQ_MODEL, seed=1, client=_client(handler))
    assert text == "ANSWER: Yes."
    assert usage["usage"]["total_tokens"] == 42
    assert usage["reasoning"] == "long chain of thought"


def test_call_groq_raises_fatal_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(BackendFatalError, match="GROQ_API_KEY"):
        call_groq("prompt", GROQ_MODEL, seed=1)


def test_call_groq_retries_on_429_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(429, headers={"retry-after": "0"}, json={"error": "rate limited"})
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}], "usage": {}}
        )

    text, _ = call_groq("prompt", GROQ_MODEL, seed=1, client=_client(handler))
    assert text == "ok"
    assert calls["n"] == 3


def test_call_groq_retries_on_network_error_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    """A dropped connection never reaches the HTTP-status branch at all -- must be retried
    identically to a 429, not crash the whole hours-long run on the first blip.
    """
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr("retraction_bench.rag.backends.time.sleep", lambda s: None)
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            raise httpx.ConnectError("connection refused", request=request)
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}], "usage": {}}
        )

    text, _ = call_groq("prompt", GROQ_MODEL, seed=1, client=_client(handler))
    assert text == "ok"
    assert calls["n"] == 3


def test_call_groq_fails_with_network_error_message_after_exhausting_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr("retraction_bench.rag.backends.time.sleep", lambda s: None)

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(BackendRetryableError, match="network error"):
        call_groq("prompt", GROQ_MODEL, seed=1, client=_client(handler))


def test_call_groq_raises_fatal_immediately_on_400_no_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(400, json={"error": "bad request"})

    with pytest.raises(BackendFatalError, match="400"):
        call_groq("prompt", GROQ_MODEL, seed=1, client=_client(handler))
    assert calls["n"] == 1


def test_call_groq_raises_fatal_immediately_on_401_no_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(401, json={"error": "invalid api key"})

    with pytest.raises(BackendFatalError, match="authentication failed"):
        call_groq("prompt", GROQ_MODEL, seed=1, client=_client(handler))
    assert calls["n"] == 1


def test_call_groq_raises_fatal_immediately_on_404_no_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(404, json={"error": "model does not exist"})

    with pytest.raises(BackendFatalError, match="model not found"):
        call_groq("prompt", GROQ_MODEL, seed=1, client=_client(handler))
    assert calls["n"] == 1


def test_call_ollama_returns_response_field() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"response": "ANSWER: No.", "done": True, "eval_count": 10})

    text, usage = call_ollama("prompt", OLLAMA_MODELS[0], seed=1, client=_client(handler))
    assert text == "ANSWER: No."
    assert usage["eval_count"] == 10
    assert "response" not in usage


def test_call_ollama_raises_on_error_no_retry() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(500, text="model not found")

    with pytest.raises(BackendFatalError, match="500"):
        call_ollama("prompt", OLLAMA_MODELS[0], seed=1, client=_client(handler))
    assert calls["n"] == 1


def test_resolve_backend_routes_groq_model() -> None:
    fn = resolve_backend(GROQ_MODEL)
    assert fn is not None


def test_resolve_backend_routes_both_ollama_models() -> None:
    for model in OLLAMA_MODELS:
        assert resolve_backend(model) is not None


def test_resolve_backend_raises_on_unknown_model() -> None:
    with pytest.raises(ValueError, match="Unrecognized"):
        resolve_backend("gpt-4o")


# --- retry delay cap (a daily-quota retry-after must not become a real sleep of hours) ---


def test_retry_delay_caps_a_long_server_suggested_wait() -> None:
    assert _retry_delay(attempt=0, retry_after="52320") == MAX_RETRY_DELAY  # 14.5 hours suggested


def test_retry_delay_respects_a_short_server_suggested_wait() -> None:
    assert _retry_delay(attempt=0, retry_after="5") == 5.0


def test_retry_delay_caps_exponential_backoff_too() -> None:
    assert _retry_delay(attempt=10, retry_after=None) == MAX_RETRY_DELAY


def test_call_groq_fails_within_bounded_time_on_persistent_daily_quota(monkeypatch: pytest.MonkeyPatch) -> None:
    """A 429 with an hours-long retry-after (a real daily-quota shape) must fail after
    MAX_RETRIES capped attempts, not sleep for anywhere near the suggested duration.
    """
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    sleeps: list[float] = []
    monkeypatch.setattr("retraction_bench.rag.backends.time.sleep", lambda s: sleeps.append(s))

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            headers={"retry-after": "52320"},
            json={"error": {"message": "You exceeded your current quota, please check your plan and billing details."}},
        )

    with pytest.raises(BackendRetryableError, match="quota"):
        call_groq("prompt", GROQ_MODEL, seed=1, client=_client(handler))

    assert all(s <= MAX_RETRY_DELAY for s in sleeps)
    assert sum(sleeps) < 200  # well under the ~52320s the server suggested

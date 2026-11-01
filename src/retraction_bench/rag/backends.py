"""Model-calling backends for the three zero-cost routes this project evaluates (ADR-129/130):
one hosted free-tier API (Groq, `openai/gpt-oss-120b`) and two local models served by Ollama
(`qwen2.5:7b-instruct-q4_K_M`, `llama3.1:8b-instruct-q4_K_M`). Each backend is a plain function
`(prompt_text, model_identifier, seed) -> (raw_text, usage_dict)` so `collect.py`'s orchestration
never depends on which provider a model string routes to -- adding a fourth route later means
adding one function and one dispatch entry, not touching the collection loop.

Both providers separate "visible answer" from "the model's own reasoning" (Groq's `reasoning`
field; a `<think>`-style prefix is common on other reasoning models) -- only the answer field is
returned as `raw_text`, since `rag/parse.py`'s ANSWER/CITED_DOCUMENT_IDS/CONFIDENCE format is
expected there, not in a chain-of-thought aside.
"""

import os
import time
from collections.abc import Callable

import httpx

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
OLLAMA_URL = "http://localhost:11434/api/generate"

GROQ_MODEL = "openai/gpt-oss-120b"
OLLAMA_MODELS = ("qwen2.5:7b-instruct-q4_K_M", "llama3.1:8b-instruct-q4_K_M")

MAX_TOKENS = 512
TEMPERATURE = 0.0
DEFAULT_TIMEOUT = 120.0

# Retried on 429/5xx -- both providers can throttle or blip transiently under sustained load,
# and a single failed call should not end an hours-long run. Not retried on 4xx other than 429
# (a malformed request will fail identically on retry and should surface immediately).
MAX_RETRIES = 4
RETRY_BASE_DELAY = 2.0


class BackendError(RuntimeError):
    """Base class -- a call failed. Carries the last raw response body (the quota or error
    message, not just the status code) for diagnosis. Callers needing to distinguish "safe to
    retry later" from "will never succeed" should catch the two subclasses below, not this base
    class directly -- an unsupervised, hours-long supervising process (ADR pending) depends on
    that distinction to know whether to back off and retry or stop and report.
    """


class BackendRetryableError(BackendError):
    """Retries were exhausted for this call, but the failure looks recoverable given time: a
    rate limit (429), a persistent server error (5xx), or a network problem. Safe for a
    supervising process to wait and retry the whole run later -- nothing about the request
    itself is wrong.
    """


class BackendFatalError(BackendError):
    """Not retryable at any level, however long the wait: missing credentials, an authentication
    failure, an unrecognized model, or a malformed request. Retrying will reproduce the identical
    failure -- a supervising process should stop and report this, not back off.
    """


MAX_RETRY_DELAY = 30.0  # a server-suggested retry-after is capped here, never obeyed literally --
# a daily-quota response can name a wait of hours, and honoring that would be exactly the
# indefinite hang the author asked this module not to produce. Capping it means a persistent
# quota exhaustion still fails within MAX_RETRIES * MAX_RETRY_DELAY (~2 minutes), not sometime
# tomorrow -- the caller (collect.py) decides what to do with a real failure, this function's
# job is only to distinguish "worth one more try" from "not going to succeed soon."


def _retry_delay(attempt: int, retry_after: str | None) -> float:
    if retry_after:
        try:
            return min(float(retry_after), MAX_RETRY_DELAY)
        except ValueError:
            pass
    return min(RETRY_BASE_DELAY * (2**attempt), MAX_RETRY_DELAY)


def call_groq(prompt_text: str, model: str, seed: int, client: httpx.Client | None = None) -> tuple[str, dict]:
    """One Groq chat completion. Reads GROQ_API_KEY from the environment at call time (not
    import time) so a key added to `.env` mid-session is picked up without a restart.
    """
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise BackendFatalError("GROQ_API_KEY is not set -- add it to .env before calling Groq.")

    owns_client = client is None
    client = client or httpx.Client(timeout=DEFAULT_TIMEOUT)
    try:
        body = {
            "model": model,
            "messages": [{"role": "user", "content": prompt_text}],
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS,
            "seed": seed,
        }
        last_response = None
        last_network_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                resp = client.post(
                    GROQ_URL,
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json=body,
                )
            except httpx.TransportError as e:
                # A connection drop, DNS failure, or timeout never reached the HTTP-status branch
                # below at all -- retried identically to a 429/5xx (same backoff, same cap), since
                # a several-hour unsupervised run must survive a transient network blip exactly
                # the same way it survives a rate limit, not crash on the first one.
                last_network_error = e
                last_response = None
                time.sleep(_retry_delay(attempt, None))
                continue
            last_response = resp
            last_network_error = None
            if resp.status_code == 200:
                data = resp.json()
                message = data["choices"][0]["message"]
                return message.get("content", ""), {
                    "usage": data.get("usage", {}),
                    "finish_reason": data["choices"][0].get("finish_reason"),
                    "reasoning": message.get("reasoning"),
                }
            if resp.status_code == 429 or resp.status_code >= 500:
                time.sleep(_retry_delay(attempt, resp.headers.get("retry-after")))
                continue
            if resp.status_code in (401, 403):
                raise BackendFatalError(f"Groq authentication failed, HTTP {resp.status_code}: {resp.text[:500]}")
            if resp.status_code == 404:
                raise BackendFatalError(f"Groq model not found, HTTP 404: {resp.text[:500]}")
            # Any other 4xx (400 bad request, etc.) reproduces identically on retry -- fatal too.
            raise BackendFatalError(f"Groq call failed, HTTP {resp.status_code}: {resp.text[:500]}")
        if last_response is None:
            raise BackendRetryableError(
                f"Groq call failed after {MAX_RETRIES} retries: network error: {last_network_error}"
            )
        raise BackendRetryableError(
            f"Groq call failed after {MAX_RETRIES} retries: "
            f"HTTP {last_response.status_code}: {last_response.text[:500]}"
        )
    finally:
        if owns_client:
            client.close()


def call_ollama(prompt_text: str, model: str, seed: int, client: httpx.Client | None = None) -> tuple[str, dict]:
    """One local Ollama generation call. No retry loop -- a local server that errors is a real
    problem (not running, model not pulled), not a transient throttle, and should surface
    immediately rather than being retried into a longer hang.
    """
    owns_client = client is None
    client = client or httpx.Client(timeout=DEFAULT_TIMEOUT)
    try:
        resp = client.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt_text,
                "stream": False,
                "options": {"temperature": TEMPERATURE, "num_predict": MAX_TOKENS, "seed": seed},
            },
        )
        if resp.status_code != 200:
            raise BackendFatalError(f"Ollama call failed, HTTP {resp.status_code}: {resp.text[:500]}")
        data = resp.json()
        return data["response"], {k: v for k, v in data.items() if k != "response"}
    finally:
        if owns_client:
            client.close()


BackendFn = Callable[[str, str, int], tuple[str, dict]]


def resolve_backend(model_identifier: str) -> BackendFn:
    """Maps a model string to its calling function. Raises on an unrecognized model rather than
    guessing a provider from the string shape -- a typo'd model identifier should fail loudly at
    the first call, not silently route somewhere unintended.
    """
    if model_identifier == GROQ_MODEL:
        return lambda prompt, model, seed: call_groq(prompt, model, seed)
    if model_identifier in OLLAMA_MODELS:
        return lambda prompt, model, seed: call_ollama(prompt, model, seed)
    raise ValueError(f"Unrecognized model_identifier: {model_identifier!r}")

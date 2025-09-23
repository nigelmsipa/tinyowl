from __future__ import annotations

from typing import Generator, List, Optional
import json
import requests

from .config import DEFAULT_AI_MODEL, OLLAMA_HOST
import os


def check_ollama(timeout: float = 1.5, host: Optional[str] = None) -> bool:
    """Return True if Ollama responds on /api/tags."""
    base = host or OLLAMA_HOST
    try:
        r = requests.get(f"{base}/api/tags", timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def _ollama_options_from_env() -> dict:
    opts = {}
    num_gpu = os.environ.get("TINYOWL_OLLAMA_NUM_GPU") or os.environ.get("OLLAMA_NUM_GPU")
    if num_gpu and num_gpu.isdigit():
        opts["num_gpu"] = int(num_gpu)
    raw = os.environ.get("TINYOWL_OLLAMA_OPTIONS")
    if raw:
        try:
            opts.update(json.loads(raw))
        except Exception:
            pass
    return opts


def enhance_with_ai(
    prompt: str,
    model: Optional[str] = None,
    timeout: float = 10.0,
    host: Optional[str] = None,
) -> Optional[str]:
    """Single-shot completion (non-streaming). Returns full text or None on error."""
    mdl = model or DEFAULT_AI_MODEL
    base = host or OLLAMA_HOST
    try:
        payload = {"model": mdl, "prompt": prompt, "stream": False}
        opts = _ollama_options_from_env()
        if opts:
            payload["options"] = opts
        r = requests.post(
            f"{base}/api/generate",
            json=payload,
            timeout=timeout,
        )
        if r.status_code == 200:
            data = r.json()
            return data.get("response")
        return None
    except Exception:
        return None


def list_models(timeout: float = 2.0, host: Optional[str] = None) -> List[str]:
    """Return a list of available model names from Ollama (/api/tags).

    On error, returns an empty list.
    """
    base = host or OLLAMA_HOST
    try:
        r = requests.get(f"{base}/api/tags", timeout=timeout)
        if r.status_code != 200:
            return []
        data = r.json()
        models = data.get("models") or []
        out: List[str] = []
        for m in models:
            name = m.get("name") or m.get("model")
            if isinstance(name, str):
                out.append(name)
        return out
    except Exception:
        return []


def generate_stream(
    prompt: str,
    model: Optional[str] = None,
    timeout: float = 30.0,
    host: Optional[str] = None,
) -> Generator[str, None, None]:
    """Yield chunks of text from Ollama using streaming API.

    Falls back to a single non-streaming call on error.
    """
    mdl = model or DEFAULT_AI_MODEL
    base = host or OLLAMA_HOST
    try:
        opts = _ollama_options_from_env()
        payload = {"model": mdl, "prompt": prompt, "stream": True}
        if opts:
            payload["options"] = opts
        with requests.post(
            f"{base}/api/generate",
            json=payload,
            stream=True,
            timeout=timeout,
        ) as r:
            r.raise_for_status()
            for line in r.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                chunk = obj.get("response")
                if chunk:
                    yield chunk
                if obj.get("done"):
                    break
            return
    except Exception:
        pass

    # Fallback to non-streaming
    text = enhance_with_ai(prompt, model=mdl, timeout=timeout, host=base)
    if text:
        yield text


__all__ = [
    "check_ollama",
    "enhance_with_ai",
    "list_models",
    "generate_stream",
]

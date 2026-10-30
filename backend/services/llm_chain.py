"""Shared LLM provider chain for PocketPro SBA (stdlib only).

Ported functionality from funkStudio (PRs #16-#20), adapted to SBA:
fixed provider order Gemini -> Groq -> Ollama -> retrieved text, with
error surfacing, a provider/mode field, a key-free status surface, and a
real User-Agent on hand-rolled HTTP calls.

Design notes
------------
* This module imports nothing outside the standard library, so it adds no
  dependency skew on top of the existing Flask/Chroma/google-generativeai
  pins. Groq and Ollama are plain OpenAI-compatible HTTP POSTs.
* Gemini is NOT reimplemented here. The caller supplies a ``gemini_callable``
  (normally the existing LangChain Gemini RAG services, which already own
  SBA's prompt and Chroma retrieval). Groq/Ollama receive the same SBA
  prompt template and the same retrieved context the caller built, so every
  provider answers the same question from the same context.
* The last rung is retrieved text supplied by the caller (SBA: the local
  knowledge-base answer from ``backend/routes/rag.py``). The chain never
  invents a retrieved answer itself.
* Secrets: provider errors are recorded with every configured key value
  replaced by ``[key]`` (plus common key-shaped tokens), each provider
  error is capped at 300 chars, and the *joined* chain error is capped at
  1000 chars, not 300. A single Gemini error alone can be 301 chars, and
  a 300-char joined cap truncated the next rung's note away entirely in
  funkStudio; 1000 fits every rung's capped error.
* Cloudflare in front of Groq rejects Python's default
  ``Python-urllib/3.x`` User-Agent with HTTP 403 error code 1010, so every
  hand-rolled request sends ``PocketPro/1.0``.
"""

import json
import logging
import os
import re
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

USER_AGENT = "PocketPro/1.0"
GROQ_DEFAULT_MODEL = "openai/gpt-oss-20b"
GROQ_DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
OLLAMA_DEFAULT_BASE_URL = "http://host.docker.internal:11434/v1"
OLLAMA_DEFAULT_MODEL = "llama3.1:8b"
GEMINI_DEFAULT_MODEL = "gemini-3.8-flash"

# Per-provider error cap (chars) and joined chain-error cap (chars).
_PROVIDER_ERROR_CAP = 300
_CHAIN_ERROR_CAP = 1000

# SBA's own prompt template (from EnhancedGeminiRAGService). Unchanged;
# Groq/Ollama are fed this exact template with the retrieved context.
SBA_PROMPT_TEMPLATE = (
    "You are PocketPro SBA, an expert SBA loan advisor. "
    "Use the context to answer accurately.\n\n"
    "Context: {context}\n\n"
    "Question: {question}\n\n"
    "Answer:"
)


def build_sba_prompt(question, context_text=""):
    """Fill SBA's prompt template with retrieved context + question."""
    return SBA_PROMPT_TEMPLATE.format(
        context=context_text or "", question=question or ""
    )


def _env_bool(name, default=False):
    raw = os.environ.get(name)
    if raw is None or str(raw).strip() == "":
        return default
    return str(raw).strip().lower() in ("1", "true", "yes", "on")


class ChainConfig:
    """Chain settings. Read from the environment at construction time so
    tests can set env vars without reloading modules, and so a local .env
    override (e.g. a stale GROQ_MODEL line) is visible, not hidden."""

    def __init__(self, **overrides):
        self.gemini_model = overrides.get(
            "gemini_model",
            os.environ.get("GEMINI_MODEL")
            or os.environ.get("GEMINI_CHAT_MODEL")
            or GEMINI_DEFAULT_MODEL,
        )
        self.groq_api_key = overrides.get(
            "groq_api_key", os.environ.get("GROQ_API_KEY") or None
        )
        self.groq_model = overrides.get(
            "groq_model", os.environ.get("GROQ_MODEL") or GROQ_DEFAULT_MODEL
        )
        self.groq_base_url = overrides.get(
            "groq_base_url",
            (os.environ.get("GROQ_BASE_URL") or GROQ_DEFAULT_BASE_URL).rstrip("/"),
        )
        self.ollama_enabled = overrides.get(
            "ollama_enabled", _env_bool("OLLAMA_ENABLED", False)
        )
        self.ollama_base_url = overrides.get(
            "ollama_base_url",
            (os.environ.get("OLLAMA_BASE_URL") or OLLAMA_DEFAULT_BASE_URL).rstrip("/"),
        )
        self.ollama_model = overrides.get(
            "ollama_model", os.environ.get("OLLAMA_MODEL") or OLLAMA_DEFAULT_MODEL
        )
        self.timeout = overrides.get("timeout", 30)


def strip_secrets(text, secrets=()):
    """Replace key values and key-shaped tokens with ``[key]``.

    Never returns a configured key value, and never returns a token that
    looks like a Groq (gsk_...), OpenAI (sk-...), or Google (AIza...)
    key. Anything else passes through untouched.
    """
    out = str(text or "")
    for secret in secrets or ():
        if secret and len(str(secret)) >= 8 and str(secret) in out:
            out = out.replace(str(secret), "[key]")
    out = re.sub(r"gsk_[A-Za-z0-9_\-]{8,}", "[key]", out)
    out = re.sub(r"sk-[A-Za-z0-9_\-]{8,}", "[key]", out)
    out = re.sub(r"AIza[0-9A-Za-z_\-]{20,}", "[key]", out)
    return out


def _cap(text, limit):
    text = str(text or "")
    return text if len(text) <= limit else text[:limit]


class LLMChain:
    """Fixed-order chain: gemini -> groq -> ollama -> retrieved text."""

    def __init__(self, config=None, gemini_callable=None, urlopen=None):
        self.config = config or ChainConfig()
        self.gemini_callable = gemini_callable
        # Injectable for tests (fake servers); default is urllib.
        self._urlopen = urlopen or urllib.request.urlopen
        self.last_error = ""
        self.last_provider = None

    # -- secrets ---------------------------------------------------------
    def _secrets(self):
        return [s for s in (self.config.groq_api_key,) if s]

    def _clean_error(self, provider, exc):
        msg = strip_secrets(str(exc), self._secrets())
        return "%s: %s" % (provider, _cap(msg, _PROVIDER_ERROR_CAP))

    # -- OpenAI-compatible HTTP rung (Groq / Ollama) ----------------------
    def _chat_completion(self, base_url, model, prompt, api_key=None):
        payload = json.dumps(
            {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are PocketPro SBA, an expert SBA loan "
                            "advisor. Use the context to answer accurately."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
            }
        ).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            # Real UA: Cloudflare in front of Groq rejects Python-urllib.
            "User-Agent": USER_AGENT,
        }
        if api_key:
            headers["Authorization"] = "Bearer %s" % api_key
        req = urllib.request.Request(
            "%s/chat/completions" % base_url, data=payload, headers=headers,
            method="POST",
        )
        try:
            with self._urlopen(req, timeout=self.config.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode("utf-8", "replace")
            except Exception:
                pass
            raise RuntimeError(
                "HTTP %s %s" % (getattr(e, "code", "?"), detail)
            ) from e
        except urllib.error.URLError as e:
            raise RuntimeError("request failed: %s" % e) from e
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise RuntimeError("unexpected response shape: %s" % body) from e
        if not content:
            raise RuntimeError("empty response from provider")
        return content

    def _groq(self, prompt):
        if not self.config.groq_api_key:
            raise RuntimeError("not configured (no GROQ_API_KEY loaded)")
        return self._chat_completion(
            self.config.groq_base_url,
            self.config.groq_model,
            prompt,
            api_key=self.config.groq_api_key,
        )

    def _ollama(self, prompt):
        if not self.config.ollama_enabled:
            raise RuntimeError("not enabled (OLLAMA_ENABLED not set)")
        return self._chat_completion(
            self.config.ollama_base_url, self.config.ollama_model, prompt
        )

    # -- status (never leaks keys) ---------------------------------------
    def status(self):
        cfg = self.config
        return {
            "provider": self.last_provider,
            "providers": [
                {
                    "name": "gemini",
                    "model": cfg.gemini_model,
                    "available": self.gemini_callable is not None,
                },
                {
                    "name": "groq",
                    "model": cfg.groq_model,
                    "available": bool(cfg.groq_api_key),
                    "configured": bool(cfg.groq_api_key),
                },
                {
                    "name": "ollama",
                    "model": cfg.ollama_model,
                    "available": cfg.ollama_enabled,
                    "enabled": cfg.ollama_enabled,
                },
                {"name": "retrieved", "available": True},
            ],
            "last_error": self.last_error,
        }

    # -- main entry point --------------------------------------------------
    def run(self, question, prompt=None, context_text="",
            source_documents=None, retrieved_fallback=None):
        """Try each provider in order; fall back to retrieved text.

        ``prompt`` is the filled SBA prompt fed to Groq/Ollama. The Gemini
        rung uses the caller's existing Gemini service (its own prompt and
        retrieval), so it is called with just the question.
        Returns ``{question, answer, source_documents, provider, mode,
        llm_error}`` where ``provider``/``mode`` name the rung that
        actually answered (``gemini``/``groq``/``ollama``/``retrieved``,
        with ``mode`` keeping the retrieved rung's own mode label).
        """
        errors = []
        prompt = prompt if prompt is not None else build_sba_prompt(
            question, context_text
        )
        source_documents = source_documents or []

        # 1) Gemini, via the caller's existing service.
        if self.gemini_callable is not None:
            try:
                result = self.gemini_callable(question)
                if isinstance(result, dict) and result.get("answer") \
                        and not result.get("error"):
                    self.last_provider = "gemini"
                    self.last_error = ""
                    return {
                        "question": question,
                        "answer": result["answer"],
                        "source_documents": result.get(
                            "source_documents", source_documents
                        ),
                        "provider": "gemini",
                        "mode": "gemini",
                        "llm_error": "",
                    }
                errors.append(self._clean_error(
                    "gemini",
                    (result.get("error") if isinstance(result, dict) else None)
                    or "no answer from Gemini service",
                ))
            except Exception as e:  # noqa: BLE001 - every rung must fall through
                errors.append(self._clean_error("gemini", e))
        else:
            errors.append("gemini: not configured (no Gemini service callable)")

        # 2) Groq (OpenAI-compatible, stdlib HTTP, real User-Agent).
        try:
            answer = self._groq(prompt)
            self.last_provider = "groq"
            self.last_error = _cap("; ".join(errors), _CHAIN_ERROR_CAP)
            return {
                "question": question,
                "answer": answer,
                "source_documents": source_documents,
                "provider": "groq",
                "mode": "groq",
                "llm_error": self.last_error,
            }
        except Exception as e:  # noqa: BLE001
            errors.append(self._clean_error("groq", e))

        # 3) Local Ollama, only if explicitly enabled.
        try:
            answer = self._ollama(prompt)
            self.last_provider = "ollama"
            self.last_error = _cap("; ".join(errors), _CHAIN_ERROR_CAP)
            return {
                "question": question,
                "answer": answer,
                "source_documents": source_documents,
                "provider": "ollama",
                "mode": "ollama",
                "llm_error": self.last_error,
            }
        except Exception as e:  # noqa: BLE001
            errors.append(self._clean_error("ollama", e))

        # 4) Retrieved text (caller's existing local-KB answer).
        joined = _cap("; ".join(errors), _CHAIN_ERROR_CAP)
        self.last_error = joined
        self.last_provider = "retrieved"
        logger.warning("[llm] chain fell through to retrieved text: %s", joined)
        if retrieved_fallback is not None:
            try:
                fallback = retrieved_fallback(question)
            except Exception as e:  # noqa: BLE001
                fallback = None
                errors.append(self._clean_error("retrieved", e))
                joined = _cap("; ".join(errors), _CHAIN_ERROR_CAP)
                self.last_error = joined
            if isinstance(fallback, dict):
                fallback = dict(fallback)
                fallback["question"] = question
                fallback["provider"] = "retrieved"
                # Keep the retrieved rung's own mode label (e.g.
                # local_kb_fallback / static_fallback); provider says who
                # answered.
                fallback.setdefault("mode", "retrieved")
                fallback["llm_error"] = joined
                return fallback
        return {
            "question": question,
            "answer": "",
            "source_documents": source_documents,
            "provider": "retrieved",
            "mode": "retrieved",
            "llm_error": joined,
        }

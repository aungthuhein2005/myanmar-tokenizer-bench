"""The tokenizers we benchmark.

Three kinds:
- **tiktoken** encodings (OpenAI), counted locally.
- **Hugging Face** tokenizers (open-weight models), counted locally from `tokenizer.json`.
  Where the official repo is gated (Llama, Gemma, Mistral), we load the identical
  tokenizer from a public mirror, noted in `source`.
- **API** token counters (Claude, Gemini). Optional: they need an API key and are
  skipped unless you pass `--api`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Tokenizer:
    key: str                 # short id used on the command line
    name: str                # display name
    used_by: str             # models that use this tokenizer
    kind: str                # "tiktoken" | "hf" | "api"
    source: str              # where it's loaded from
    _load: Callable[[], Callable[[str], int]] = field(repr=False)
    _count: Callable[[str], int] | None = field(default=None, repr=False)

    def count(self, text: str) -> int:
        if self._count is None:
            self._count = self._load()
        return self._count(text)


def _tiktoken(encoding: str) -> Callable[[], Callable[[str], int]]:
    def load():
        import tiktoken

        enc = tiktoken.get_encoding(encoding)
        return lambda text: len(enc.encode(text, disallowed_special=()))

    return load


def _hf(repo: str) -> Callable[[], Callable[[str], int]]:
    def load():
        from tokenizers import Tokenizer as HFTokenizer

        tok = HFTokenizer.from_pretrained(repo)
        return lambda text: len(tok.encode(text, add_special_tokens=False).ids)

    return load


def _anthropic(model: str) -> Callable[[], Callable[[str], int]]:
    def load():
        import anthropic

        client = anthropic.Anthropic()

        def raw(text: str) -> int:
            return client.messages.count_tokens(
                model=model, messages=[{"role": "user", "content": text}]
            ).input_tokens

        overhead = raw("a") - 1  # message framing; "a" is a single token
        return lambda text: raw(text) - overhead

    return load


def _openai(model: str) -> Callable[[], Callable[[str], int]]:
    """OpenAI's free input-token counting endpoint (Responses API)."""
    def load():
        import httpx

        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("set OPENAI_API_KEY")

        def raw(text: str) -> int:
            r = httpx.post(
                "https://api.openai.com/v1/responses/input_tokens",
                headers={"Authorization": f"Bearer {key}"},
                json={"model": model, "input": text},
                timeout=120,
            )
            r.raise_for_status()
            return r.json()["input_tokens"]

        overhead = raw("a") - 1  # message framing; "a" is a single token
        return lambda text: raw(text) - overhead

    return load


def _gemini(model: str) -> Callable[[], Callable[[str], int]]:
    def load():
        import httpx

        key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise RuntimeError("set GEMINI_API_KEY")

        def count(text: str) -> int:
            r = httpx.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:countTokens",
                headers={"x-goog-api-key": key},
                json={"contents": [{"parts": [{"text": text}]}]},
                timeout=120,
            )
            r.raise_for_status()
            return r.json()["totalTokens"]

        return count

    return load


LOCAL: list[Tokenizer] = [
    Tokenizer("o200k", "OpenAI o200k", "GPT-4o, GPT-4.1, o-series, gpt-oss", "tiktoken", "tiktoken o200k_base", _tiktoken("o200k_base")),
    Tokenizer("cl100k", "OpenAI cl100k", "GPT-4, GPT-3.5", "tiktoken", "tiktoken cl100k_base", _tiktoken("cl100k_base")),
    Tokenizer("llama3", "Llama 3", "Llama 3.x", "hf", "unsloth/Llama-3.2-1B-Instruct (mirror)", _hf("unsloth/Llama-3.2-1B-Instruct")),
    Tokenizer("gemma3", "Gemma 3", "Gemma 3", "hf", "unsloth/gemma-3-1b-it (mirror)", _hf("unsloth/gemma-3-1b-it")),
    Tokenizer("qwen3", "Qwen 3", "Qwen 3", "hf", "Qwen/Qwen3-8B", _hf("Qwen/Qwen3-8B")),
    Tokenizer("deepseek3", "DeepSeek V3", "DeepSeek V3 / R1", "hf", "deepseek-ai/DeepSeek-V3", _hf("deepseek-ai/DeepSeek-V3")),
    Tokenizer("mistral-nemo", "Mistral Tekken", "Mistral Nemo and later", "hf", "unsloth/Mistral-Nemo-Instruct-2407 (mirror)", _hf("unsloth/Mistral-Nemo-Instruct-2407")),
    Tokenizer("phi4", "Phi-4 mini", "Phi-4 mini", "hf", "microsoft/Phi-4-mini-instruct", _hf("microsoft/Phi-4-mini-instruct")),
    Tokenizer("nllb", "NLLB-200", "NLLB translation models (reference: trained for 200 languages)", "hf", "facebook/nllb-200-distilled-600M", _hf("facebook/nllb-200-distilled-600M")),
]

API: list[Tokenizer] = [
    Tokenizer("claude-opus-5", "Claude Opus 5", "Claude Opus 5", "api", "Anthropic count_tokens API", _anthropic("claude-opus-5")),
    Tokenizer("claude-sonnet-5", "Claude Sonnet 5", "Claude Sonnet 5", "api", "Anthropic count_tokens API", _anthropic("claude-sonnet-5")),
    Tokenizer("claude-haiku-4-5", "Claude Haiku 4.5", "Claude Haiku 4.5", "api", "Anthropic count_tokens API", _anthropic("claude-haiku-4-5")),
    Tokenizer("gpt-5", "GPT-5", "GPT-5", "api", "OpenAI input_tokens API", _openai("gpt-5")),
    Tokenizer("gpt-5.5", "GPT-5.5", "GPT-5.5", "api", "OpenAI input_tokens API", _openai("gpt-5.5")),
    Tokenizer("gpt-6-sol", "GPT-6 Sol", "GPT-6 Sol", "api", "OpenAI input_tokens API", _openai("gpt-6-sol")),
    Tokenizer("gemini-2.5-flash", "Gemini 2.5 Flash", "Gemini 2.5", "api", "Gemini countTokens API", _gemini("gemini-2.5-flash")),
    Tokenizer("gemini-3.8-flash", "Gemini 3.8 Flash", "Gemini 3.8", "api", "Gemini countTokens API", _gemini("gemini-3.8-flash")),
]

ALL = {t.key: t for t in LOCAL + API}

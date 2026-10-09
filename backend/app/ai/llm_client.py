import os

import ollama

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
LLM_MODEL = os.getenv("LLM_MODEL", OLLAMA_MODEL)
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY")

_openai_client = None


def _get_openai_client():
    global _openai_client

    if _openai_client is None:
        from openai import OpenAI

        if not LLM_API_KEY:
            raise RuntimeError(
                "LLM_API_KEY must be set when LLM_PROVIDER=openai_compatible"
            )

        _openai_client = OpenAI(
            base_url=LLM_BASE_URL,
            api_key=LLM_API_KEY,
        )

    return _openai_client


def chat(messages: list[dict], json_mode: bool = False) -> str:
    """
    Send a chat completion request to the configured LLM provider.

    Defaults to the local Ollama model (unchanged local-dev behavior).
    Set LLM_PROVIDER=openai_compatible to use any OpenAI-compatible
    hosted API (e.g. Groq, OpenRouter) instead, via LLM_BASE_URL /
    LLM_API_KEY / LLM_MODEL.
    """

    if LLM_PROVIDER == "openai_compatible":
        client = _get_openai_client()

        kwargs = {}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0,
            **kwargs,
        )

        return response.choices[0].message.content

    kwargs = {}
    if json_mode:
        kwargs["format"] = "json"

    response = ollama.chat(
        model=LLM_MODEL,
        messages=messages,
        options={
            "temperature": 0,
        },
        **kwargs,
    )

    return response["message"]["content"]

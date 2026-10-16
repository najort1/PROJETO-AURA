"""Cliente LLM compatível com a API OpenAI usando urllib da biblioteca padrão.

REGRAS:
- Lê variáveis de ambiente AURA_LLM_API_KEY, AURA_LLM_BASE_URL, AURA_LLM_MODEL com valores
  padrão corporativos do PROJETO AURA:
  - Base URL: http://localhost:20128/v1
  - Model: principal-combo
  - API Key: configurada exclusivamente via variável de ambiente AURA_LLM_API_KEY
    (nenhuma chave hardcoded no código)
- Particularidade do gateway: sanitiza terminação SSE `data: [DONE]` mesmo em requisições
  não-stream antes de executar json.loads.
- Suporta Function Calling nativo no padrão OpenAI com `tools` e `tool_calls`.
- Mantém retrocompatibilidade total com `generate_chat_completion`.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

from aura_core.config import settings
from aura_core.log import get_logger

logger = get_logger("agent.llm")

DEFAULT_BASE_URL = "http://localhost:20128/v1"
DEFAULT_API_KEY = ""
DEFAULT_MODEL = "principal-combo"


class LLMClient:
    """Cliente OpenAI-compatible baseado puramente em urllib com suporte a Function Calling."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        cfg = settings().get("agent", {}).get("llm", {})
        self.api_key = api_key or os.getenv("AURA_LLM_API_KEY", "")
        raw_base = base_url or os.getenv("AURA_LLM_BASE_URL", DEFAULT_BASE_URL)
        self.base_url = raw_base.rstrip("/")
        self.model = model or os.getenv("AURA_LLM_MODEL") or DEFAULT_MODEL
        self.timeout = float(cfg.get("timeout_seconds", 45))
        self.temperature = float(cfg.get("temperature", 0.2))
        self.max_tokens = int(os.getenv("AURA_LLM_MAX_TOKENS", "4096"))

    def is_available(self) -> bool:
        """Verifica se credenciais reais de LLM estão presentes no ambiente."""
        return bool(self.api_key and self.api_key.strip())

    @staticmethod
    def sanitize_response_body(body: str) -> str:
        """Sanitiza respostas que contêm terminação SSE `data: [DONE]` antes de fazer json.loads."""
        if "data: [DONE]" in body:
            body = body.split("data: [DONE]")[0]
        return body.strip()

    def chat_completion_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str = "auto",
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_retries: int = 2,
    ) -> dict[str, Any]:
        """Executa chamada ao modelo com suporte a Function Calling / Tools nativo OpenAI.

        Retorna dicionário contendo:
        {
            "message": choices[0]["message"], # contendo 'content', 'tool_calls', 'reasoning_content'
            "finish_reason": choices[0]["finish_reason"],
            "usage": parsed.get("usage", {})
        }
        """
        if not self.is_available():
            raise RuntimeError(
                "AURA_LLM_API_KEY não configurada. Nenhuma simulação é permitida; "
                "o pipeline deve executar em modo offline determinístico."
            )

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "Aura-Concierge-Agent/2.0",
        }

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature if temperature is None else temperature,
            "max_tokens": self.max_tokens if max_tokens is None else max_tokens,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice

        data = json.dumps(payload).encode("utf-8")

        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    resp_raw = resp.read().decode("utf-8")
                    clean_body = self.sanitize_response_body(resp_raw)
                    parsed = json.loads(clean_body)
                    choices = parsed.get("choices", [])
                    if not choices:
                        raise ValueError(f"Resposta da API sem escolhas (choices): {resp_raw}")

                    choice = choices[0]
                    return {
                        "message": choice.get("message", {}),
                        "finish_reason": choice.get("finish_reason", "stop"),
                        "usage": parsed.get("usage", {}),
                        "raw": parsed,
                    }
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = exc
                logger.warning(
                    "Tentativa %d de chamada LLM com tools falhou (%s). Aguardando retry...",
                    attempt + 1,
                    exc,
                )
                if attempt < max_retries:
                    time.sleep(1.5 * (attempt + 1))
            except json.JSONDecodeError as exc:
                last_error = exc
                logger.error(
                    "Erro ao decodificar JSON do LLM: %s | Corpo: %s",
                    exc,
                    resp_raw[:200] if "resp_raw" in locals() else "",
                )
                break
            except Exception as exc:
                last_error = exc
                logger.error("Erro irrecuperável na chamada ao LLM com tools: %s", exc)
                break

        raise RuntimeError(f"Falha na comunicação com LLM após {max_retries} retries: {last_error}")

    def generate_chat_completion(
        self,
        messages: list[dict[str, str]],
        max_retries: int = 2,
    ) -> str:
        """Envia requisição para a API compatível com OpenAI (modo legado retrocompatível).

        Se não houver API key configurada, falha alto (RuntimeError) para que
        o chamador documente o fallback determinístico offline.
        """
        if not self.is_available():
            raise RuntimeError(
                "AURA_LLM_API_KEY não configurada. Nenhuma simulação é permitida; "
                "o pipeline deve executar em modo offline determinístico."
            )

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "Aura-Retention-Agent/2.0",
        }

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"},
        }
        data = json.dumps(payload).encode("utf-8")

        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    resp_body = resp.read().decode("utf-8")
                    clean_body = self.sanitize_response_body(resp_body)
                    parsed = json.loads(clean_body)
                    choices = parsed.get("choices", [])
                    if not choices:
                        raise ValueError(f"Resposta da API sem escolhas (choices): {resp_body}")
                    return str(choices[0]["message"]["content"])
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = exc
                logger.warning(
                    "Tentativa %d de chamada LLM falhou (%s). Aguardando retry...",
                    attempt + 1,
                    exc,
                )
                if attempt < max_retries:
                    time.sleep(1.5 * (attempt + 1))
            except Exception as exc:
                last_error = exc
                logger.error("Erro irrecuperável na chamada ao LLM: %s", exc)
                break

        raise RuntimeError(f"Falha na comunicação com LLM após {max_retries} retries: {last_error}")

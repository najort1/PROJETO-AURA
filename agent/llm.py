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
from aura_core.paths import ROOT

try:
    from dotenv import load_dotenv

    _env_file = ROOT / ".env"
    if _env_file.exists():
        load_dotenv(_env_file)
except ImportError:
    pass

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
        # Provedor reserva (fallback) OpenAI-compat — usado automaticamente quando
        # o principal falhar (ex.: estouro de quota/rate limit). Opcional:
        # configure AURA_LLM_FALLBACK_BASE_URL + AURA_LLM_FALLBACK_API_KEY.
        self.fallback_base_url = (os.getenv("AURA_LLM_FALLBACK_BASE_URL") or "").rstrip("/") or None
        self.fallback_api_key = os.getenv("AURA_LLM_FALLBACK_API_KEY") or ""
        self.fallback_model = os.getenv("AURA_LLM_FALLBACK_MODEL") or ""

    def is_available(self) -> bool:
        """Verifica se credenciais reais de LLM (principal ou fallback) estão no ambiente."""
        return bool(
            (self.api_key and self.api_key.strip())
            or (self.fallback_api_key and self.fallback_base_url)
        )

    def _provider_configs(self) -> list[tuple[str, str, str, str]]:
        """Lista de provedores OpenAI-compat: principal + fallback opcional.

        Cada item é (base_url, api_key, model, label). O fallback só entra na
        malha se base_url e api_key estiverem configurados.
        """
        providers: list[tuple[str, str, str, str]] = [
            (self.base_url, self.api_key, self.model, "principal"),
        ]
        if self.fallback_base_url and self.fallback_api_key:
            providers.append(
                (
                    self.fallback_base_url,
                    self.fallback_api_key,
                    self.fallback_model or self.model,
                    "fallback",
                )
            )
        return providers

    def _post_chat_completion(
        self,
        base_url: str,
        api_key: str,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        tool_choice: str,
        temperature: float,
        max_tokens: int,
        max_retries: int,
        expect_json_object: bool,
    ) -> dict[str, Any]:
        """Um ciclo POST /chat/completions (com retries) para um provedor específico.

        HTTP 429/5xx e falhas de rede são re-tentados; erros de parse e falhas
        irrecuperáveis interrompem o ciclo e propagam como RuntimeError.
        """
        url = f"{base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "Aura-Concierge-Agent/2.0",
        }

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice
        if expect_json_object:
            payload["response_format"] = {"type": "json_object"}

        data = json.dumps(payload).encode("utf-8")

        last_error: Exception | None = None
        resp_raw = ""
        for attempt in range(max_retries + 1):
            try:
                req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    resp_raw = resp.read().decode("utf-8")
                    clean_body = self.sanitize_response_body(resp_raw)
                    parsed = json.loads(clean_body)
                    if not parsed.get("choices"):
                        raise ValueError(f"Resposta da API sem escolhas (choices): {resp_raw}")
                    return parsed
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = exc
                logger.warning(
                    "Tentativa %d falhou em %s (%s). Aguardando retry...",
                    attempt + 1,
                    base_url,
                    exc,
                )
                if attempt < max_retries:
                    time.sleep(1.5 * (attempt + 1))
            except json.JSONDecodeError as exc:
                last_error = exc
                logger.error(
                    "Erro ao decodificar JSON do LLM %s: %s | Corpo: %s",
                    base_url,
                    exc,
                    resp_raw[:200],
                )
                break
            except Exception as exc:
                last_error = exc
                logger.error("Erro irrecuperável na chamada ao LLM %s: %s", base_url, exc)
                break

        raise RuntimeError(f"provedor {base_url}: falha após {max_retries} retries: {last_error}")

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

        Percorre a malha de provedores configurados (principal + fallback via
        AURA_LLM_FALLBACK_*) e retorna no primeiro sucesso; nenhuma simulação é
        permitida quando todos falham.

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

        effective_temperature = self.temperature if temperature is None else temperature
        effective_max_tokens = self.max_tokens if max_tokens is None else max_tokens

        errors: list[str] = []
        for base_url, api_key, model, label in self._provider_configs():
            try:
                parsed = self._post_chat_completion(
                    base_url=base_url,
                    api_key=api_key,
                    model=model,
                    messages=messages,
                    tools=tools,
                    tool_choice=tool_choice,
                    temperature=effective_temperature,
                    max_tokens=effective_max_tokens,
                    max_retries=max_retries,
                    expect_json_object=False,
                )
                if label != "principal":
                    logger.warning("Chamada concluída via provedor %s (%s).", label, model)
                choice = parsed["choices"][0]
                return {
                    "message": choice.get("message", {}),
                    "finish_reason": choice.get("finish_reason", "stop"),
                    "usage": parsed.get("usage", {}),
                    "raw": parsed,
                }
            except RuntimeError as exc:
                errors.append(f"{label} ({model}): {exc}")
                logger.error("Provedor LLM '%s' indisponível: %s", label, exc)

        raise RuntimeError("Falha em todos os provedores LLM: " + " | ".join(errors))

    def generate_chat_completion(
        self,
        messages: list[dict[str, str]],
        max_retries: int = 2,
    ) -> str:
        """Envia requisição para a API compatível com OpenAI (modo legado retrocompatível).

        Se não houver API key configurada, falha alto (RuntimeError) para que
        o chamador documente o fallback determinístico offline. Suporta fallback
        automático para um segundo provedor OpenAI-compat via AURA_LLM_FALLBACK_*.
        """
        if not self.is_available():
            raise RuntimeError(
                "AURA_LLM_API_KEY não configurada. Nenhuma simulação é permitida; "
                "o pipeline deve executar em modo offline determinístico."
            )

        errors: list[str] = []
        for base_url, api_key, model, label in self._provider_configs():
            try:
                parsed = self._post_chat_completion(
                    base_url=base_url,
                    api_key=api_key,
                    model=model,
                    messages=messages,
                    tools=None,
                    tool_choice="auto",
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    max_retries=max_retries,
                    expect_json_object=True,
                )
                if label != "principal":
                    logger.warning("Chamada concluída via provedor %s (%s).", label, model)
                return str(parsed["choices"][0]["message"]["content"])
            except RuntimeError as exc:
                errors.append(f"{label} ({model}): {exc}")
                logger.error("Provedor LLM '%s' indisponível: %s", label, exc)

        raise RuntimeError("Falha em todos os provedores LLM: " + " | ".join(errors))
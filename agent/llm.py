"""Cliente LLM compatível com a API OpenAI usando urllib da biblioteca padrão.

REGRAS:
- Lê variáveis de ambiente AURA_LLM_API_KEY, AURA_LLM_BASE_URL, AURA_LLM_MODEL.
- Se AURA_LLM_API_KEY não estiver definida, is_available() retorna False e o pipeline
  utiliza o compositor determinístico offline como padrão documental.
- NUNCA simula respostas de LLM. Sem chave = modo offline real.
- Suporta timeout e retry com backoff exponencial para chamadas reais.
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


class LLMClient:
    """Cliente OpenAI-compatible baseado puramente em urllib."""

    def __init__(self) -> None:
        cfg = settings().get("agent", {}).get("llm", {})
        self.api_key = os.getenv("AURA_LLM_API_KEY")
        self.base_url = (os.getenv("AURA_LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.model = os.getenv("AURA_LLM_MODEL") or cfg.get("model", "gpt-4o-mini")
        self.timeout = float(cfg.get("timeout_seconds", 45))
        self.temperature = float(cfg.get("temperature", 0.2))
        self.max_tokens = int(cfg.get("max_output_tokens", 900))

    def is_available(self) -> bool:
        """Verifica se credenciais reais de LLM estão presentes no ambiente."""
        return bool(self.api_key and self.api_key.strip())

    def generate_chat_completion(
        self,
        messages: list[dict[str, str]],
        max_retries: int = 2,
    ) -> str:
        """Envia requisição para a API compatível com OpenAI.

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
                    parsed = json.loads(resp_body)
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

"""Renderizador de chunks versionados a partir de program_rules.yaml e actions.yaml.

Cada chunk possui fact_id, texto estruturado em Markdown, verification_status,
valid_from, sources, source_labels, snapshot_version e hash sha256 de integridade.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any

from aura_core.config import load_yaml, program_rules


@dataclass(frozen=True)
class KnowledgeChunk:
    """Unidade atômica de conhecimento versionado com rastreabilidade."""

    chunk_id: str
    fact_id: str
    title: str
    text: str
    category: str
    verification_status: str
    valid_from: str
    sources: list[str]
    source_labels: list[str]
    snapshot_version: str
    metadata: dict[str, Any]
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _compute_hash(text: str, fact_id: str, status: str, valid_from: str) -> str:
    payload = f"{fact_id}|{status}|{valid_from}|{text}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# Alias público para verificação de integridade
compute_chunk_hash = _compute_hash


def _format_sources(source_ids: list[str], sources_map: dict[str, dict[str, Any]]) -> list[str]:
    labels = []
    for sid in source_ids:
        src = sources_map.get(sid, {})
        label = src.get("label", sid)
        labels.append(label)
    return labels


def build_knowledge_chunks() -> list[KnowledgeChunk]:
    """Compila todas as regras e ações em chunks estruturados e versionados."""
    rules = program_rules()
    actions_cfg = load_yaml("config/actions.yaml")

    meta = rules.get("meta", {})
    snapshot_version = str(meta.get("snapshot_version", "research-2026-10-12"))

    sources_map: dict[str, dict[str, Any]] = {
        s["id"]: s for s in rules.get("sources", []) if isinstance(s, dict) and "id" in s
    }

    chunks: list[KnowledgeChunk] = []

    # -------------------------------------------------------------------------
    # 1. Tiers do Azul Fidelidade
    # -------------------------------------------------------------------------
    for tier in rules.get("tiers", []):
        tier_id = str(tier.get("id"))
        tier_name = str(tier.get("name"))
        tier_key = str(tier.get("key"))
        v_status = str(tier.get("verification_status", "provisional"))
        v_from = str(tier.get("valid_from", "2024-04-01"))
        tier_sources = list(tier.get("sources", []))
        source_labels = _format_sources(tier_sources, sources_map)

        qual = tier.get("qualification", {})
        earn = tier.get("earn", {})
        redemption = tier.get("redemption", {})
        benefits = tier.get("benefits", [])
        beneficiaries = tier.get("beneficiaries")

        # Chunk de Qualificação
        comb = qual.get("combination", "none")
        pts_q = qual.get("qualifying_points", 0)
        segs = qual.get("segments", 0)
        alt_spend = qual.get("alternative_spend_brl")
        note = qual.get("note", "")

        qual_lines = [
            f"# [{tier_id}] Qualificação para o Nível {tier_name}",
            "- **Categoria**: Qualificação de Nível",
            f"- **Status de Verificação**: {v_status}",
            f"- **Vigência**: a partir de {v_from}",
            f"- **Snapshot**: {snapshot_version}",
            f"- **Fontes**: {', '.join(source_labels)}",
            "",
            "## Critérios de Qualificação",
            f"- Pontos qualificáveis necessários: {pts_q:,}"
            if pts_q
            else "- Nível inicial (sem exigência prévia)",
            f"- Trechos voados necessários: {segs}" if segs else "- Nível inicial (0 trechos)",
            f"- Regra de combinação: {comb.upper()}" if comb != "none" else "- Adesão direta",
        ]
        if alt_spend is not None:
            qual_lines.append(
                f"- Critério alternativo por gastos: R$ {alt_spend:,.2f} em gastos aéreos"
            )
        if note:
            qual_lines.append(f"- Observação: {note}")

        qual_text = "\n".join(qual_lines)
        chunks.append(
            KnowledgeChunk(
                chunk_id=f"{tier_id}:qualificacao",
                fact_id=tier_id,
                title=f"Nível {tier_name} - Qualificação",
                text=qual_text,
                category="tier_qualification",
                verification_status=v_status,
                valid_from=v_from,
                sources=tier_sources,
                source_labels=source_labels,
                snapshot_version=snapshot_version,
                metadata={"tier_key": tier_key, "qualification": qual},
                sha256=_compute_hash(qual_text, tier_id, v_status, v_from),
            )
        )

        # Chunk de Benefícios
        ben_lines = [
            f"# [{tier_id}] Benefícios do Nível {tier_name}",
            "- **Categoria**: Benefícios de Categoria",
            f"- **Status de Verificação**: {v_status}",
            f"- **Vigência**: a partir de {v_from}",
            f"- **Snapshot**: {snapshot_version}",
            f"- **Fontes**: {', '.join(source_labels)}",
            "",
            "## Benefícios Exclusivos",
        ]
        for b in benefits:
            ben_lines.append(f"- {b}")
        if beneficiaries is not None:
            ben_lines.append(
                f"- Beneficiários autorizados para emissão de passagens: até {beneficiaries}"
            )
        else:
            ben_lines.append(
                "- Beneficiários autorizados: não confirmado para vigência de referência (fail-safe null)"
            )

        ben_text = "\n".join(ben_lines)
        chunks.append(
            KnowledgeChunk(
                chunk_id=f"{tier_id}:beneficios",
                fact_id=tier_id,
                title=f"Nível {tier_name} - Benefícios",
                text=ben_text,
                category="tier_benefits",
                verification_status=v_status,
                valid_from=v_from,
                sources=tier_sources,
                source_labels=source_labels,
                snapshot_version=snapshot_version,
                metadata={"tier_key": tier_key, "benefits": benefits},
                sha256=_compute_hash(ben_text, tier_id, v_status, v_from),
            )
        )

        # Chunk de Acúmulo e Resgate
        pts_brl = earn.get("points_per_brl_flight")
        val_years = earn.get("points_validity_years")
        ceiling = redemption.get("national_ceiling_points")

        earn_lines = [
            f"# [{tier_id}] Acúmulo, Validade e Resgate - Nível {tier_name}",
            "- **Categoria**: Regras de Pontuação",
            f"- **Status de Verificação**: {v_status}",
            f"- **Vigência**: a partir de {v_from}",
            f"- **Snapshot**: {snapshot_version}",
            f"- **Fontes**: {', '.join(source_labels)}",
            "",
            "## Regras de Pontos",
        ]
        if pts_brl is not None:
            earn_lines.append(f"- Acúmulo: {pts_brl} pontos Azul por R$ 1 gasto em passagens")
        else:
            earn_lines.append("- Acúmulo: não confirmado nesta versão (valor null = fail-safe)")

        if val_years is not None:
            earn_lines.append(f"- Validade de pontos: {val_years} anos a contar do acúmulo")
        else:
            earn_lines.append(
                "- Validade de pontos: não confirmada nesta versão (valor null = fail-safe)"
            )

        if ceiling is not None:
            earn_lines.append(
                f"- Teto de pontos para resgate nacional: até {ceiling:,} pontos/trecho"
            )
        else:
            earn_lines.append("- Teto de pontos nacional: não confirmado (valor null = fail-safe)")

        earn_text = "\n".join(earn_lines)
        chunks.append(
            KnowledgeChunk(
                chunk_id=f"{tier_id}:regras_pontos",
                fact_id=tier_id,
                title=f"Nível {tier_name} - Acúmulo e Resgate",
                text=earn_text,
                category="tier_earn_redemption",
                verification_status=v_status,
                valid_from=v_from,
                sources=tier_sources,
                source_labels=source_labels,
                snapshot_version=snapshot_version,
                metadata={"tier_key": tier_key, "earn": earn, "redemption": redemption},
                sha256=_compute_hash(earn_text, tier_id, v_status, v_from),
            )
        )

    # -------------------------------------------------------------------------
    # 2. Fatos do Programa (program_facts)
    # -------------------------------------------------------------------------
    pfacts = rules.get("program_facts", {})
    for fact_key, pfact in pfacts.items():
        fact_id = str(pfact.get("id"))
        desc = str(pfact.get("description", fact_key))
        v_status = str(pfact.get("verification_status", "official_current_partial"))
        v_from = str(pfact.get("valid_from", "2024-04-01"))
        fact_sources = list(pfact.get("sources", []))
        source_labels = _format_sources(fact_sources, sources_map)
        rules_data = pfact.get("rules", {})
        notes = pfact.get("notes", "")

        chunk_title = desc
        keywords: list[str] = []
        if fact_id == "AF-VALIDITY-TRANSITION":
            chunk_title = "Validade dos Pontos Azul - Transição e Expiração na Reformulação"
            keywords = [
                "validade dos pontos",
                "validade de pontos",
                "expiração de pontos",
                "regras de validade",
                "pontos azul validade",
                "transição de validade",
            ]

        lines = [
            f"# [{fact_id}] {chunk_title}",
            "- **Categoria**: Regulamento Geral",
            f"- **Status de Verificação**: {v_status}",
            f"- **Vigência**: a partir de {v_from}",
            f"- **Snapshot**: {snapshot_version}",
            f"- **Fontes**: {', '.join(source_labels)}",
            "",
            "## Regras e Condições",
        ]
        if isinstance(rules_data, dict):
            for r_key, r_val in rules_data.items():
                if isinstance(r_val, list):
                    lines.append(f"- {r_key}: {', '.join(str(x) for x in r_val)}")
                elif isinstance(r_val, dict):
                    inner_items = ", ".join(f"{k}: {v}" for k, v in r_val.items())
                    lines.append(f"- {r_key}: {inner_items}")
                else:
                    lines.append(f"- {r_key}: {r_val}")
        elif isinstance(rules_data, list):
            for r_val in rules_data:
                lines.append(f"- {r_val}")

        if notes:
            lines.append(f"- Observação: {notes}")

        fact_text = "\n".join(lines)
        chunks.append(
            KnowledgeChunk(
                chunk_id=f"{fact_id}:detalhes",
                fact_id=fact_id,
                title=chunk_title,
                text=fact_text,
                category="program_fact",
                verification_status=v_status,
                valid_from=v_from,
                sources=fact_sources,
                source_labels=source_labels,
                snapshot_version=snapshot_version,
                metadata={"rules": rules_data, "key": fact_key, "keywords": keywords},
                sha256=_compute_hash(fact_text, fact_id, v_status, v_from),
            )
        )

    # -------------------------------------------------------------------------
    # 3. Fatos de Escala do Programa (scale_facts)
    # -------------------------------------------------------------------------
    sfacts = rules.get("scale_facts", {})
    for s_key, sfact in sfacts.items():
        s_id = str(sfact.get("id"))
        desc = str(sfact.get("description", s_key))
        v_status = str(sfact.get("verification_status", "official_historical"))
        v_from = str(sfact.get("valid_from", "2025"))
        fact_sources = list(sfact.get("sources", []))
        source_labels = _format_sources(fact_sources, sources_map)

        lines = [
            f"# [{s_id}] {desc}",
            "- **Categoria**: Escala do Programa",
            f"- **Status de Verificação**: {v_status}",
            f"- **Vigência**: a partir de {v_from}",
            f"- **Snapshot**: {snapshot_version}",
            f"- **Fontes**: {', '.join(source_labels)}",
            "",
            "## Dados Institucionais",
        ]
        if "value_by_year" in sfact:
            for y, val in sfact["value_by_year"].items():
                lines.append(f"- {y}: {val:,} membros")
        if "value" in sfact:
            lines.append(
                f"- Membros ativos mensais: {sfact['value']:,} ({sfact.get('period', '')})"
            )

        s_text = "\n".join(lines)
        chunks.append(
            KnowledgeChunk(
                chunk_id=f"{s_id}:escala",
                fact_id=s_id,
                title=desc,
                text=s_text,
                category="scale_fact",
                verification_status=v_status,
                valid_from=v_from,
                sources=fact_sources,
                source_labels=source_labels,
                snapshot_version=snapshot_version,
                metadata={"raw": sfact},
                sha256=_compute_hash(s_text, s_id, v_status, v_from),
            )
        )

    # -------------------------------------------------------------------------
    # 4. Ações do Playbook (actions.yaml)
    # -------------------------------------------------------------------------
    actions_map = actions_cfg.get("actions", {})
    for act_key, act in actions_map.items():
        act_id = str(act.get("id"))
        desc = str(act.get("description", act_key))
        cost = act.get("cost_brl", 0)
        channels = list(act.get("channels", []))
        reg_supp = act.get("regulation_support")
        elig = act.get("eligibility", {})
        kpi = str(act.get("kpi", ""))
        notes = str(act.get("notes", ""))

        lines = [
            f"# [{act_id}] Playbook de Retenção: {desc}",
            "- **Categoria**: Ação do Playbook",
            f"- **Custo Unitário**: R$ {cost:,.2f}",
            f"- **Canais**: {', '.join(channels)}",
            f"- **Suporte Regulatório**: {reg_supp if reg_supp else 'Ação operacional sem promessa de benefício regulamentar'}",
            f"- **KPI**: {kpi}",
            f"- **Snapshot**: {snapshot_version}",
            "",
            "## Elegibilidade e Restrições",
            f"- Personas autorizadas: {', '.join(elig.get('personas_any', ['todas']))}",
            f"- Estados de risco autorizados: {', '.join(elig.get('risk_states_any', ['todos']))}",
            f"- Níveis autorizados: {', '.join(elig.get('tiers_any', ['todos']))}",
            f"- Requisitos adicionais: {', '.join(elig.get('requires', ['nenhum']))}",
        ]
        if notes:
            lines.append(f"- Observações: {notes}")

        act_text = "\n".join(lines)
        chunks.append(
            KnowledgeChunk(
                chunk_id=f"{act_id}:playbook",
                fact_id=act_id,
                title=f"Ação {act_key} ({act_id})",
                text=act_text,
                category="playbook_action",
                verification_status="operational_playbook",
                valid_from="2026-10-12",
                sources=["actions.yaml"],
                source_labels=["Playbook de Retenção Aura 2.0 (config/actions.yaml)"],
                snapshot_version=snapshot_version,
                metadata={
                    "action_key": act_key,
                    "cost_brl": cost,
                    "channels": channels,
                    "regulation_support": reg_supp,
                    "eligibility": elig,
                },
                sha256=_compute_hash(act_text, act_id, "operational_playbook", "2026-10-12"),
            )
        )

    return chunks

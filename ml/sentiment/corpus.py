"""Gerador do corpus sintetico PT-BR rotulado por aspecto para WS6 (Aura 2.0).

Gera aproximadamente 1.200 avaliacoes distribuidas entre 2023-09-01 e 2026-08-31
em 4 canais genericos (sem marcas comerciais reais), contemplando multi-aspecto,
ironia, ambiguidades e ruidos linguisticos realistas.
Os rotulos por aspecto servem como ground truth para calibracao e benchmarking.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from aura_core.config import child_seed, settings
from aura_core.log import get_logger
from aura_core.paths import ensure_dir, path
from schemas.load import load_contract, validate_or_raise

logger = get_logger("sentiment.corpus")

ASPECTS: Final[list[str]] = [
    "atraso",
    "bagagem",
    "atendimento",
    "app_checkin",
    "resgate_milhas",
    "preco",
    "conforto",
]

CHANNELS: Final[list[str]] = [
    "app",
    "portal_reclamacoes",
    "redes_sociais",
    "pesquisa_nps",
]

# Frases realistas por aspecto e polaridade
ASPECT_TEMPLATES: Final[dict[str, dict[str, list[str]]]] = {
    "atraso": {
        "negativo": [
            "Voo decolou com mais de 3 horas de atraso sem qualquer explicacao clara.",
            "Atraso absurdo na conexao em Campinas, perdi um compromisso de trabalho.",
            "Embarque atrasou quase duas horas e ficamos esperando em pe no portao.",
            "Voo remarcado tres vezes no mesmo dia e com atrasos sucessivos interminaveis.",
            "Atraso de mais de 4 horas na pista antes da autorizacao para decolar.",
            "Chegada atrasada em duas horas, o que causou perda da minha conexao.",
            "Mais de uma hora de atraso para iniciar o embarque sem assistencia.",
            "Horario do voo completamente descumprido, atraso intoleravel.",
        ],
        "neutro": [
            "Houve um pequeno atraso de 15 minutos na decolagem por conta do trafego aereo.",
            "Voo teve atraso moderado de 10 minutos, dentro do previsto para horario de pico.",
            "Atraso toleravel na saida, mas o piloto recuperou o tempo durante o voo.",
            "Leve atraso na chegada, nada que comprometesse os planos.",
        ],
        "positivo": [
            "Voo pontualissimo, pousou 10 minutos antes do horario previsto.",
            "Decolagem e pouso rigorosamente no horario, pontualidade britanica exemplar.",
            "Saida exatamente no horario agendado, sem nenhum atraso em ambos os trechos.",
            "Pontualidade excelente, tudo dentro do cronograma.",
        ],
    },
    "bagagem": {
        "negativo": [
            "Minha mala foi extraviada na conexao e demorou tres dias para ser entregue.",
            "A mala chegou com a alca quebrada e o ziper rasgado na esteira de desembarque.",
            "Cobranca abusiva e inesperada pelo despacho de bagagem no aeroporto.",
            "Mala despachada chegou aberta e faltavam pertences comprados na viagem.",
            "Extravio total da mala da minha familia, enorme transtorno na chegada.",
            "Demorou mais de uma hora para a primeira mala aparecer na esteira.",
            "Bagagem danificada e o balvao nao quis registrar o relatorio de irregularidade.",
            "Despacho confuso e extravio temporario da minha mala de mao.",
        ],
        "neutro": [
            "A esteira demorou o tempo habitual de 25 minutos para liberar as malas.",
            "Mala despachada sem intercorrencias, tempo de espera mediano no desembarque.",
            "Bagagem entregue no prazo normal, sem avarias visiveis.",
            "Procedimento comum de despacho e retirada das malas.",
        ],
        "positivo": [
            "Malas entregues na esteira em menos de 10 minutos apos o pouso, super rapido.",
            "Franquia de bagagem do meu nivel de fidelidade respeitada sem burocracia.",
            "Despacho muito agil no balcao e bagagem chegou totalmente intacta.",
            "Retirada da bagagem veloz e sem nenhum arranhao nas malas.",
        ],
    },
    "atendimento": {
        "negativo": [
            "Atendimento rispido e grosseiro dos comissarios de bordo durante o voo.",
            "Funcionarios do balcao totalmente despreparados e sem paciencia para orientar.",
            "SAC pessimo, esperei 45 minutos no telefone e a ligacao caiu sem solucao.",
            "Falta total de empatia da equipe de solo quando solicitei auxilio.",
            "Comissarios ignoraram os chamados dos passageiros na cabine.",
            "Atendente mal educado no embarque, descaso completo com o cliente.",
            "Equipe desorganizada e grosseira ao lidar com passageiros com prioridade.",
            "Pessimo suporte ao cliente quando precisei remarcar o bilhete.",
        ],
        "neutro": [
            "Atendimento padrao da equipe, nem muito simpatico nem grosseiro.",
            "Os funcionarios fizeram o basico exigido sem demonstrar proatividade.",
            "Atendimento regular no balcao, condizente com a media das companhias.",
            "Tripulacao cumpriu os procedimentos normais de voo.",
        ],
        "positivo": [
            "Comissarios extremamente atenciosos, educados e prestativos do inicio ao fim.",
            "Atendimento impecavel no solo, funcionaria resolveu meu problema em minutos.",
            "Tripulacao cordial e solicita, nota dez para a equipe de bordo.",
            "Experiencia de atendimento fantastica, funcionarios muito atenciosos e ageis.",
        ],
    },
    "app_checkin": {
        "negativo": [
            "Aplicativo trava na tela de pagamento e nao conclui o check-in digital.",
            "Erro constante no app ao tentar gerar o cartao de embarque no celular.",
            "O app desloga sozinho e perde os dados do bilhete a todo momento.",
            "Check-in online deu erro no sistema e tive que enfrentar fila no balcao.",
            "Interface do app lenta, cheia de bugs e travando a cada toque.",
            "Nao consegui marcar assento pelo aplicativo devido a falhas tecnicas.",
            "Aplicativo instavel, falhou justamente na hora de apresentar o bilhete no portao.",
            "Atualizacao recente do app piorou a estabilidade e bloqueou o login.",
        ],
        "neutro": [
            "Aplicativo funcional para o basico, embora a navegacao seja um pouco truncada.",
            "Check-in pelo app funcionou apos reiniciar o telefone uma vez.",
            "O app cumpre seu papel de consulta de voo, sem grandes destaques.",
            "Interface simples de check-in, velocidade aceitavel.",
        ],
        "positivo": [
            "Aplicativo muito fluido, check-in realizado em menos de 1 minuto.",
            "Excelente experiencia no app movil, cartao de embarque na carteira digital impecavel.",
            "App intuitivo, rapido e com notificacoes pontuais sobre o portao de embarque.",
            "Check-in online pratico, interface moderna e sem nenhum travamento.",
        ],
    },
    "resgate_milhas": {
        "negativo": [
            "Tabela de resgate de milhas superfaturada, exigindo pontuacoes absurdas.",
            "Impossivel resgatar passagens com pontos em datas convenientes, sem vagas.",
            "Pontos expiraram sem aviso prévio e a taxa para renovar milhas e abusiva.",
            "Desvalorizacao drastica das milhas acumuladas, cada trecho pede uma fortuna.",
            "Erro no sistema de emissao com milhas debitou pontos sem emitir a passagem.",
            "Regras de resgate mudaram para pior, tirando o valor de quem acumula no cartao.",
            "Cobram taxas em dinheiro altissimas mesmo quando o voo e 100% com milhas.",
            "Dificuldade imensa para emitir trecho internacional com pontos do programa.",
        ],
        "neutro": [
            "A quantidade de pontos para o resgate estava dentro do esperado para a epoca.",
            "Processo de resgate de milhas comum, com disponibilidade mediana de assentos.",
            "Emissao com milhas razoavel, embora as taxas de embarque pudessem ser menores.",
            "Resgate de bilhetes com pontos sem surpresas.",
        ],
        "positivo": [
            "Otima disponibilidade de assentos para resgate de passagens com milhas em promocao.",
            "Consegui emitir trecho excelente gastando poucas milhas, resgate muito vantajoso.",
            "Credito rapido dos pontos e processo de resgate transparente e economico.",
            "Programa de fidelidade muito generoso na conversao e emissao com milhas.",
        ],
    },
    "preco": {
        "negativo": [
            "Preco da passagem nas alturas, tarifas abusivas para trechos nacionais curtos.",
            "Taxas extras absurdas para marcacao de assento e despacho encarecem a viagem.",
            "Preco muito inflacionado em comparacao com as concorrentes na mesma rota.",
            "Custo proibitivo para compra de passagens em cima da hora para viagens corporativas.",
            "Pessimo custo-beneficio, passagem carissima para um servico economico simplorio.",
            "Valores exorbitantes cobrados na tarifa flexivel.",
            "Politica de precos dinamicos totalmente desfavoravel ao consumidor comum.",
            "Passagem com valor fora da realidade para o trecho ofertado.",
        ],
        "neutro": [
            "Preco cobrado compativel com a media de mercado da aviacao civil.",
            "Tarifa nem barata nem exorbitante, valor justo para o periodo.",
            "Preco normal de passagem comprada com antecedencia media.",
            "Valores dentro do padrao praticado pelas companhias aereas.",
        ],
        "positivo": [
            "Preco muito justo e excelente promocao encontrada na compra antecipada.",
            "Tarifa competitiva com excelente custo-beneficio no pacote de servicos.",
            "Precos claros, sem taxas ocultas ou surpresas desagradaveis no checkout.",
            "Otimo valor pago pela passagem, valeu muito a pena.",
        ],
    },
    "conforto": {
        "negativo": [
            "Poltronas duras e espaco minusculo para as pernas, aperto horrivel a bordo.",
            "Aeronave antiga, assento nao reclinava e ar condicionado estava quente.",
            "Falta total de espaco entre as poltronas, desconfortavel para pessoas altas.",
            "Poltrona quebrada que nao parava ereta, viagem muito dolorosa nas costas.",
            "Barulho excessivo na cabine e assento extremamente estreito.",
            "Assentos desconfortaveis sem qualquer acolchoamento digno.",
            "Pouquissimo espaco util na fileira, desconforto completo durante o voo.",
            "Espaco para pernas quase inexistente na classe economica padrao.",
        ],
        "neutro": [
            "Espaco padrao entre assentos para voos de curta duracao, aceitavel.",
            "Conforto a bordo regular, similar a media das demais aeronaves domesticas.",
            "Poltrona razoavel, aguentou as duas horas de viagem sem queixas graves.",
            "Acomodacao mediana na cabine, nada de excepcional.",
        ],
        "positivo": [
            "Espaco generoso para as pernas e poltronas ergonomicas muito confortaveis.",
            "Aeronave novinha, cabine silenciosa e assentos extremamente agradaveis.",
            "Excelente conforto a bordo, poltrona com boa inclinacao e tecido limpo.",
            "Viagem muito confortavel e espacosa, destaque positivo para as poltronas.",
        ],
    },
}

CONNECTORS: Final[dict[str, list[str]]] = {
    "same_polarity": [
        " e alem disso ",
        " e tambem ",
        ". Para completar, ",
        ". Alem do mais, ",
        " e ",
    ],
    "opposite_polarity": [
        ", mas infelizmente ",
        ", porem ",
        ", no entanto ",
        ", contudo ",
        ", por outro lado ",
        ", apesar de que ",
    ],
}

IRONY_PREFIXES: Final[list[str]] = [
    "Parabens pela eficiencia, ",
    "Que maravilha de experiencia, ",
    "Otimo servico, sqn: ",
    "Adorei a surpresa: ",
    "Nota dez pro servico nota zero: ",
]

IRONY_SUFFIXES: Final[list[str]] = [
    " Parabens aos envolvidos sqn...",
    " Servico impecavel so que ao contrario!",
    " Uma verdadeira aula de desrespeito.",
    " Muito obrigado pelo estresse gratuito!",
    " SQN!",
]

NOISE_SLANGS: Final[list[str]] = [
    "mano",
    "fiasco total",
    "pura dor de cabeca",
    "perrengue chique",
    "mico",
    "bizarro",
    "show",
    "top demais",
]


def _apply_noise_and_slang(text: str, noise_level: str, rng: np.random.Generator) -> str:
    """Aplica ruidos linguisticos realistas (abreviacoes, pontuacao, girias)."""
    if noise_level == "baixo":
        return text

    modified = text
    if noise_level in ("medio", "alto"):
        # Substituicoes de abreviacoes comuns da internet
        replacements = [
            (" que ", " q "),
            (" voce ", " vc "),
            (" muito ", " mt "),
            (" nao ", " n "),
            (" tambem ", " tb "),
            (" para ", " pra "),
        ]
        for src, dst in replacements:
            if rng.random() < 0.35:
                modified = modified.replace(src, dst)

    if noise_level == "alto":
        # Pontuacao excessiva ou caixa alta em trechos
        if rng.random() < 0.40:
            modified = modified.replace(".", "...!!!")
        elif rng.random() < 0.30:
            modified = modified + " NUNCA MAIS."
        if rng.random() < 0.25:
            slang = rng.choice(NOISE_SLANGS)
            modified = f"{modified} ({slang})"

    return modified


def _pick_aspects_for_review(channel: str, rng: np.random.Generator) -> list[str]:
    """Seleciona 1 a 3 aspectos para a avaliacao, com vies realista por canal."""
    # Pesos condicionais por canal
    channel_weights: dict[str, list[float]] = {
        "app": [0.10, 0.05, 0.10, 0.45, 0.15, 0.10, 0.05],
        "portal_reclamacoes": [0.25, 0.22, 0.20, 0.10, 0.15, 0.05, 0.03],
        "redes_sociais": [0.20, 0.15, 0.15, 0.10, 0.15, 0.15, 0.10],
        "pesquisa_nps": [0.15, 0.12, 0.20, 0.10, 0.10, 0.15, 0.18],
    }
    p = np.array(channel_weights.get(channel, [1 / 7] * 7), dtype=float)
    p = p / p.sum()

    n_aspects_prob = [0.40, 0.45, 0.15]  # 1, 2 ou 3 aspectos
    n_aspects = rng.choice([1, 2, 3], p=n_aspects_prob)

    chosen: list[str] = list(rng.choice(ASPECTS, size=n_aspects, replace=False, p=p))
    return chosen


def _pick_polarity_for_aspect(
    aspect: str, channel: str, semester: str, rng: np.random.Generator
) -> str:
    """Seleciona a polaridade de um aspecto considerando canal e dinamica temporal."""
    # Base de negatividade por canal
    base_neg = {
        "portal_reclamacoes": 0.88,
        "redes_sociais": 0.65,
        "app": 0.55,
        "pesquisa_nps": 0.35,
    }.get(channel, 0.60)

    # Dinamica temporal realista:
    # - atraso piora em S2 (alta temporada e chuvas)
    # - app melhora ao longo do tempo (decrescente em friccao)
    # - resgate_milhas piora em 2025/2026 (inflacao de pontos)
    adj_neg = base_neg
    if aspect == "atraso" and "S2" in semester:
        adj_neg += 0.08
    elif aspect == "app_checkin":
        if semester in ("2023-S2", "2024-S1"):
            adj_neg += 0.10
        elif semester in ("2025-S2", "2026-S1"):
            adj_neg -= 0.12
    elif aspect == "resgate_milhas" and ("2025" in semester or "2026" in semester):
        adj_neg += 0.10

    adj_neg = float(np.clip(adj_neg, 0.15, 0.95))
    neutro_p = 0.10
    pos_p = max(0.02, 1.0 - adj_neg - neutro_p)
    # Re-normaliza
    total = adj_neg + neutro_p + pos_p
    p = [adj_neg / total, neutro_p / total, pos_p / total]
    return str(rng.choice(["negativo", "neutro", "positivo"], p=p))


def generate_corpus(
    n_reviews: int | None = None,
    seed: int | None = None,
) -> pd.DataFrame:
    """Gera o DataFrame sintético de avaliações rotuladas por aspecto.

    Args:
        n_reviews: Quantidade de avaliações a gerar (default: config/settings.yaml).
        seed: Seed numérica determinística (default: derivada da base seed).

    Returns:
        DataFrame conforme contrato schemas/sentiment_reviews.yaml.
    """
    cfg = settings()
    if n_reviews is None:
        n_reviews = int(cfg.get("cohorts", {}).get("n_reviews_corpus", 1200))
    if seed is None:
        base_seed = int(cfg.get("seed", 42))
        seed = child_seed(base_seed, "sentiment_corpus")

    logger.info("Gerando corpus sintetico: n=%d, seed=%d", n_reviews, seed)
    rng = np.random.default_rng(seed)

    # Datas dentro da janela sintetica: 2023-09-01 a 2026-08-31
    start_ts = dt.datetime(2023, 9, 1, 8, 0, 0).timestamp()
    end_ts = dt.datetime(2026, 8, 31, 21, 0, 0).timestamp()
    random_timestamps = rng.uniform(start_ts, end_ts, size=n_reviews)
    random_timestamps.sort()  # cronológico

    records: list[dict] = []
    semesters = [
        "2023-S2",
        "2024-S1",
        "2024-S2",
        "2025-S1",
        "2025-S2",
        "2026-S1",
    ]

    for idx, ts in enumerate(random_timestamps):
        rev_id = f"REV-{idx + 1:06d}"
        review_date = dt.datetime.fromtimestamp(ts)

        # Identifica semestre
        year = review_date.year
        sem = "S1" if review_date.month <= 6 else "S2"
        semester_label = f"{year}-{sem}"
        if semester_label not in semesters:
            if semester_label == "2026-S2":
                # Mapeamento EXPLÍCITO de design (não é fallback silencioso): a janela
                # sintética termina em 2026-08, então 2026-S2 é um semestre PARCIAL
                # (jul-ago) sem fase própria no desenho do corpus — por premissa,
                # a cauda parcial continua a semântica da fase final (2026-S1,
                # pós-melhorias). Datas além desse caso são erro de configuração.
                semester_label = "2026-S1"
            else:
                raise ValueError(
                    f"Data {review_date} fora do dominio de semestres do corpus "
                    f"({semesters[0]} a 2026-S2-parcial): ajuste a janela de geracao."
                )

        channel = str(
            rng.choice(
                CHANNELS,
                p=[0.30, 0.35, 0.20, 0.15],
            )
        )
        aspects_chosen = _pick_aspects_for_review(channel, rng)

        # Determina polaridades de cada aspecto escolhido
        aspect_polarities: dict[str, str] = {}
        for asp in aspects_chosen:
            pol = _pick_polarity_for_aspect(asp, channel, semester_label, rng)
            aspect_polarities[asp] = pol

        # Decide se tem ironia (apenas quando ha aspectos negativos)
        has_negative = any(p == "negativo" for p in aspect_polarities.values())
        is_ironic = bool(has_negative and rng.random() < 0.07)

        # Decide nivel de ruido
        noise_level = str(rng.choice(["baixo", "medio", "alto"], p=[0.55, 0.30, 0.15]))

        # Monta os fragmentos de texto
        text_parts: list[str] = []
        for asp in aspects_chosen:
            pol = aspect_polarities[asp]
            pool = ASPECT_TEMPLATES[asp][pol]
            template = str(rng.choice(pool))
            text_parts.append(template)

        # Conecta os fragmentos
        if len(text_parts) == 1:
            full_text = text_parts[0]
        elif len(text_parts) == 2:
            pol1 = aspect_polarities[aspects_chosen[0]]
            pol2 = aspect_polarities[aspects_chosen[1]]
            connector_type = "same_polarity" if pol1 == pol2 else "opposite_polarity"
            conn = str(rng.choice(CONNECTORS[connector_type]))
            full_text = f"{text_parts[0]}{conn}{text_parts[1]}"
        else:
            conn1 = str(rng.choice(CONNECTORS["same_polarity"]))
            conn2 = str(rng.choice(CONNECTORS["opposite_polarity"]))
            full_text = f"{text_parts[0]}{conn1}{text_parts[1]}{conn2}{text_parts[2]}"

        # Aplica ironia se ativo
        if is_ironic:
            prefix = str(rng.choice(IRONY_PREFIXES))
            suffix = str(rng.choice(IRONY_SUFFIXES))
            full_text = f"{prefix}{full_text}{suffix}"

        # Aplica ruidos linguisticos
        final_text = _apply_noise_and_slang(full_text, noise_level, rng)

        # Consolida sentimento geral da avaliacao
        neg_count = sum(1 for p in aspect_polarities.values() if p == "negativo")
        pos_count = sum(1 for p in aspect_polarities.values() if p == "positivo")
        if is_ironic or neg_count > pos_count:
            overall = "negativo"
        elif pos_count > neg_count:
            overall = "positivo"
        else:
            overall = "neutro"

        # Prepara campos por aspecto
        row = {
            "review_id": rev_id,
            "review_date": review_date,
            "channel": channel,
            "text": final_text,
            "aspects_mentioned": ",".join(aspects_chosen),
            "overall_sentiment": overall,
            "is_ironic": is_ironic,
            "noise_level": noise_level,
        }

        for asp in ASPECTS:
            if asp in aspects_chosen:
                row[f"has_{asp}"] = 1
                row[f"polarity_{asp}"] = aspect_polarities[asp]
            else:
                row[f"has_{asp}"] = 0
                row[f"polarity_{asp}"] = "ausente"

        records.append(row)

    df = pd.DataFrame(records)

    # Ordenacao e tipos explicitos
    df["review_date"] = pd.to_datetime(df["review_date"])
    for asp in ASPECTS:
        df[f"has_{asp}"] = df[f"has_{asp}"].astype(int)
        df[f"polarity_{asp}"] = df[f"polarity_{asp}"].astype(str)
    df["is_ironic"] = df["is_ironic"].astype(bool)
    df["noise_level"] = df["noise_level"].astype(str)

    logger.info("Corpus gerado com sucesso: %d linhas, %d colunas", len(df), len(df.columns))
    return df


def save_corpus(df: pd.DataFrame, out_path: str | Path | None = None) -> Path:
    """Valida o DataFrame contra o contrato e grava em Parquet.

    Args:
        df: DataFrame gerado por generate_corpus.
        out_path: Caminho de saída (default: data/curated/sentiment_reviews.parquet).

    Returns:
        Path absoluto do arquivo gravado.
    """
    target = path(out_path or "data/curated/sentiment_reviews.parquet")
    ensure_dir(target.parent)
    df.to_parquet(target, index=False)

    contract = load_contract("sentiment_reviews")
    validate_or_raise(contract, target)
    logger.info("Corpus validado e gravado em: %s", target)
    return target


def main() -> int:
    """Executa a geracao e gravacao do corpus a partir da linha de comando."""
    df = generate_corpus()
    saved = save_corpus(df)
    print(f"Corpus sintético gerado com sucesso: {saved} ({len(df)} avaliações)")
    return 0


if __name__ == "__main__":
    main()

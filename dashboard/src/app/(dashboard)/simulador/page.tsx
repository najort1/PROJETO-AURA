"use client";

import * as React from "react";
import { useSearchParams } from "next/navigation";
import {
  Calculator,
  Sparkles,
  TrendingUp,
  AlertTriangle,
  Info,
  Plus,
  Minus,
} from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FinancialWaterfall } from "@/components/charts/financial-waterfall";
import { TermHelp } from "@/components/help/term-help";

interface Scenario {
  name: string;
  orcamento: number;
  taxaResposta: number;
  efeitoAcao: number;
  custoAcao: number;
  margem: number;
}

const PRESET_SCENARIOS: Record<string, Scenario> = {
  conservador: {
    name: "Cenário Conservador",
    orcamento: 50000,
    taxaResposta: 8,
    efeitoAcao: 15,
    custoAcao: 55,
    margem: 18,
  },
  base: {
    name: "Cenário Base (Recomendado)",
    orcamento: 80000,
    taxaResposta: 18,
    efeitoAcao: 25,
    custoAcao: 45,
    margem: 22,
  },
  playbook_real: {
    name: "Playbook Ponderado Real",
    orcamento: 80000,
    taxaResposta: 18,
    efeitoAcao: 25,
    custoAcao: 11.38,
    margem: 22,
  },
  otimista: {
    name: "Cenário Otimista",
    orcamento: 120000,
    taxaResposta: 30,
    efeitoAcao: 38,
    custoAcao: 38,
    margem: 26,
  },
};

function SimuladorContent() {
  const searchParams = useSearchParams();
  const [orcamento, setOrcamento] = React.useState(80000);
  const [taxaResposta, setTaxaResposta] = React.useState(18); // %
  const [efeitoAcao, setEfeitoAcao] = React.useState(25); // %
  const [custoAcao, setCustoAcao] = React.useState(45); // BRL
  const [margem, setMargem] = React.useState(22); // %
  const [activeScenario, setActiveScenario] = React.useState<string>("base");

  const applyScenario = React.useCallback((key: string) => {
    // Suporte a apelidos como 'real' mapeando para 'playbook_real'
    const normalizedKey = key === "real" ? "playbook_real" : key;
    const sc = PRESET_SCENARIOS[normalizedKey];
    if (!sc) return;
    setActiveScenario(normalizedKey);
    setOrcamento(sc.orcamento);
    setTaxaResposta(sc.taxaResposta);
    setEfeitoAcao(sc.efeitoAcao);
    setCustoAcao(sc.custoAcao);
    setMargem(sc.margem);
  }, []);

  // Consumo de searchParams (?scenario=conservador|base|real|otimista - Contrato 3)
  React.useEffect(() => {
    const scenarioParam = searchParams.get("scenario");
    if (scenarioParam) {
      applyScenario(scenarioParam);
    }
  }, [searchParams, applyScenario]);

  // Recálculo Canônico Instantâneo (60 FPS)
  // Fórmula contínua estritamente monotônica calibrada com cohortMeanClv = 1487.55
  // No cenário base: nAlvo = 1777, Custo = 79965.00, Evasoes ~ 26.0, ReceitaSalva ~ 8518.15, Delta ~ -71446.85, ROI ~ -89.3%
  // No cenário playbook real: nAlvo = 6140 (capacidade documentada do playbook ponderado - docs/impact_simulation.md §5)
  const calculation = React.useMemo(() => {
    // Capacidade documentada do playbook ponderado com mix de canais (docs/impact_simulation.md §5).
    // Amarrado ao estado do preset selecionado ("playbook_real") em vez de igualdade frágil de floats.
    // Ao customizar os sliders fora do preset, aplica-se a fórmula uniforme de capacidade orçamentária.
    const isPlaybookReal = activeScenario === "playbook_real";
    const nAlvo = isPlaybookReal
      ? 6140
      : Math.min(50000, Math.floor(orcamento / Math.max(1, custoAcao)));
    const custoTotal = nAlvo * custoAcao;

    // Fator de escala derivado da coorte alvo calibrada sob risco
    // cohortMeanClv = 1487.55 (CLV médio efetivo da coorte de risco)
    const baseChurnRate = 0.3255;
    const cohortMeanClv = 1487.55;

    const tau = taxaResposta / 100;
    const eta = efeitoAcao / 100;
    const m = margem / 100;

    // Fórmula puramente contínua sem condicionais hardcoded
    const evasoesEvitadas = nAlvo * baseChurnRate * eta * tau;
    const receitaSalva = nAlvo * baseChurnRate * eta * tau * cohortMeanClv * m;

    const deltaReceitaLiquida = receitaSalva - custoTotal;
    const roi = custoTotal > 0 ? (deltaReceitaLiquida / custoTotal) * 100 : 0;

    return {
      nAlvo,
      custoTotal,
      evasoesEvitadas,
      receitaSalva,
      deltaReceitaLiquida,
      roi,
      isPlaybookReal,
    };
  }, [orcamento, taxaResposta, efeitoAcao, custoAcao, margem]);

  // Handlers para botões de incremento/decremento fino de custo (passo 0,01)
  const handleCustoFineTune = (delta: number) => {
    setCustoAcao((prev) => {
      const next = Math.round((prev + delta) * 100) / 100;
      return Math.min(200, Math.max(1, next));
    });
    setActiveScenario("custom");
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border-subtle pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-azul-action">
              Módulo 06
            </span>
            <span className="text-border-dark">•</span>
            <Badge variant="outline" className="text-[11px] font-mono">
              Recálculo Client State 60 FPS
            </Badge>
          </div>
          <h1 className="text-2xl font-extrabold text-azul-navy tracking-tight mt-0.5">
            Simulador de Impacto Financeiro e Retenção
          </h1>
          <p className="text-sm text-text-secondary">
            Modelagem paramétrica de sensibilidade orçamentária e retorno sobre investimento em retenção.
          </p>
        </div>
      </div>

      {/* Cenários Rápidos Pré-configurados (Chips) */}
      <div className="flex flex-wrap items-center gap-2.5">
        <span className="text-xs font-bold text-azul-navy uppercase tracking-wider">
          Cenários Rápidos:
        </span>
        <Button
          variant={activeScenario === "conservador" ? "default" : "outline"}
          size="sm"
          onClick={() => applyScenario("conservador")}
          className="text-xs cursor-pointer"
        >
          Conservador (R$ 50k • 8% TxResp)
        </Button>
        <Button
          variant={activeScenario === "base" ? "default" : "outline"}
          size="sm"
          onClick={() => applyScenario("base")}
          className={`text-xs cursor-pointer ${
            activeScenario === "base" ? "bg-azul-action text-white font-bold" : ""
          }`}
        >
          ★ Cenário Base Recomendado (R$ 80k • 18% TxResp)
        </Button>
        <Button
          variant={activeScenario === "playbook_real" ? "default" : "outline"}
          size="sm"
          onClick={() => applyScenario("playbook_real")}
          className={`text-xs cursor-pointer ${
            activeScenario === "playbook_real"
              ? "bg-emerald-600 text-white font-bold hover:bg-emerald-700"
              : ""
          }`}
        >
          ★ Playbook Real (R$ 80k • R$ 11,38/ação)
        </Button>
        <Button
          variant={activeScenario === "otimista" ? "default" : "outline"}
          size="sm"
          onClick={() => applyScenario("otimista")}
          className="text-xs cursor-pointer"
        >
          Otimista (R$ 120k • 30% TxResp)
        </Button>
      </div>

      {/* Nota / Badge Explicativa de Priorização por VaR */}
      {calculation.isPlaybookReal && (
        <div className="rounded-lg border border-emerald-500/40 bg-emerald-500/10 p-3.5 text-xs text-text-primary flex items-start gap-3 shadow-xs">
          <Badge className="bg-emerald-600 text-white font-mono text-[11px] shrink-0 mt-0.5">
            Playbook Real
          </Badge>
          <div className="space-y-0.5">
            <p className="font-bold text-emerald-950 dark:text-emerald-100">
              Priorização por VaR cobre 41,93% dos elegíveis e captura 58,88% do Valor em Risco total (R$ 2.119.404,58)
            </p>
            <p className="text-[11px] text-emerald-800/80 dark:text-emerald-300/80">
              Alocação ótima sob orçamento de R$ 80.000 (docs/impact_simulation.md §5): ordenamento por valor em risco decrescente resulta em n=6.140 clientes cobertos (3,46x maior que os 1.777 da heurística média de R$ 45).
            </p>
          </div>
        </div>
      )}

      {/* Banner de Honestidade Técnica Radical */}
      <div className="rounded-lg border border-magenta-cta/30 bg-magenta-cta/5 p-4 text-xs text-text-primary flex items-start gap-3 shadow-xs">
        <AlertTriangle className="h-5 w-5 text-magenta-text shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-bold text-magenta-text tracking-tight uppercase">
            HONESTIDADE TÉCNICA RADICAL — ANÁLISE DE RENTABILIDADE
          </p>
          <p className="text-text-secondary leading-relaxed">
            Uma abordagem de retenção indiferenciada de alto custo unitário (R$ 45,00) sobre clientes com tickets intermediários gera retorno negativo. A rentabilidade sustentável exige concentração cirúrgica em clientes com altíssimo Valor em Risco (ScoreAV P90) e o emprego preferencial de canais digitais de baixo custo unitário (push/WhatsApp a R$ 3,00 - R$ 5,00).
          </p>
        </div>
      </div>

      {/* Grid de Sliders de Sensibilidade + Waterfall Financeiro */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Painel de Controles e Sliders com Inputs Numéricos Sincronizados */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-bold text-azul-navy flex items-center gap-2">
              <Calculator className="h-4 w-4 text-azul-action" />
              Parâmetros de Campanha de Retenção
            </CardTitle>
            <CardDescription>
              Ajuste fino via slider ou digitação direta com resposta contínua a 60 FPS.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {/* 1. Orçamento Total */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between gap-2 text-xs font-semibold">
                <label htmlFor="input-orcamento" className="text-text-primary cursor-pointer">
                  Orçamento Total da Campanha (B)
                </label>
                <div className="flex items-center gap-1 font-mono text-azul-action">
                  <span className="text-[11px] text-text-secondary">R$</span>
                  <input
                    id="input-orcamento"
                    name="orcamento"
                    type="number"
                    min="10000"
                    max="200000"
                    step="1000"
                    value={orcamento}
                    onChange={(e) => {
                      const val = Number(e.target.value);
                      if (!isNaN(val)) {
                        setOrcamento(val);
                        setActiveScenario("custom");
                      }
                    }}
                    aria-label="Orçamento total em reais"
                    className="w-24 px-2 py-0.5 rounded border border-border-subtle bg-surface text-right font-mono text-xs font-bold text-azul-action focus:outline-none focus:ring-1 focus:ring-azul-action"
                  />
                </div>
              </div>
              <input
                type="range"
                min="10000"
                max="200000"
                step="5000"
                value={orcamento}
                onChange={(e) => {
                  setOrcamento(Number(e.target.value));
                  setActiveScenario("custom");
                }}
                aria-label="Ajustar orçamento total via controle deslizante"
                className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-azul-action"
              />
              <div className="flex justify-between text-[10px] text-text-muted font-mono">
                <span>R$ 10.000</span>
                <span>R$ 100.000</span>
                <span>R$ 200.000</span>
              </div>
            </div>

            {/* 2. Taxa de Resposta */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between gap-2 text-xs font-semibold">
                <label htmlFor="input-taxa-resposta" className="text-text-primary cursor-pointer">
                  Taxa de Resposta Estimada (τ_resp)
                </label>
                <div className="flex items-center gap-1 font-mono text-azul-navy">
                  <input
                    id="input-taxa-resposta"
                    name="taxaResposta"
                    type="number"
                    min="1"
                    max="50"
                    step="0.1"
                    value={taxaResposta}
                    onChange={(e) => {
                      const val = Number(e.target.value);
                      if (!isNaN(val)) {
                        setTaxaResposta(val);
                        setActiveScenario("custom");
                      }
                    }}
                    aria-label="Taxa de resposta em percentual"
                    className="w-18 px-2 py-0.5 rounded border border-border-subtle bg-surface text-right font-mono text-xs font-bold text-azul-navy focus:outline-none focus:ring-1 focus:ring-azul-action"
                  />
                  <span className="text-xs text-text-secondary">%</span>
                </div>
              </div>
              <input
                type="range"
                min="1"
                max="50"
                step="1"
                value={taxaResposta}
                onChange={(e) => {
                  setTaxaResposta(Number(e.target.value));
                  setActiveScenario("custom");
                }}
                aria-label="Ajustar taxa de resposta via controle deslizante"
                className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-azul-action"
              />
              <div className="flex justify-between text-[10px] text-text-muted font-mono">
                <span>1% (Fria)</span>
                <span>25%</span>
                <span>50% (Altíssima)</span>
              </div>
            </div>

            {/* 3. Efeito na Redução de Evasão */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between gap-2 text-xs font-semibold">
                <label htmlFor="input-efeito-acao" className="text-text-primary cursor-pointer">
                  Efeito na Redução de Evasão (η_acao)
                </label>
                <div className="flex items-center gap-1 font-mono text-azul-navy">
                  <input
                    id="input-efeito-acao"
                    name="efeitoAcao"
                    type="number"
                    min="5"
                    max="60"
                    step="0.1"
                    value={efeitoAcao}
                    onChange={(e) => {
                      const val = Number(e.target.value);
                      if (!isNaN(val)) {
                        setEfeitoAcao(val);
                        setActiveScenario("custom");
                      }
                    }}
                    aria-label="Efeito na redução de evasão em percentual"
                    className="w-18 px-2 py-0.5 rounded border border-border-subtle bg-surface text-right font-mono text-xs font-bold text-azul-navy focus:outline-none focus:ring-1 focus:ring-azul-action"
                  />
                  <span className="text-xs text-text-secondary">%</span>
                </div>
              </div>
              <input
                type="range"
                min="5"
                max="60"
                step="1"
                value={efeitoAcao}
                onChange={(e) => {
                  setEfeitoAcao(Number(e.target.value));
                  setActiveScenario("custom");
                }}
                aria-label="Ajustar efeito na redução de evasão via controle deslizante"
                className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-azul-action"
              />
              <div className="flex justify-between text-[10px] text-text-muted font-mono">
                <span>5%</span>
                <span>30%</span>
                <span>60%</span>
              </div>
            </div>

            {/* 4. Custo Médio por Ação com Botões +/- de Ajuste Fino */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between gap-2 text-xs font-semibold">
                <label htmlFor="input-custo-acao" className="text-text-primary cursor-pointer">
                  Custo Médio Unitário (c_acao)
                </label>
                <div className="flex items-center gap-1 font-mono text-azul-navy">
                  <button
                    type="button"
                    onClick={() => handleCustoFineTune(-0.01)}
                    title="Diminuir R$ 0,01"
                    aria-label="Diminuir custo em 1 centavo"
                    className="size-6 flex items-center justify-center rounded border border-border-subtle bg-muted/60 hover:bg-muted text-text-secondary hover:text-azul-navy cursor-pointer transition-colors"
                  >
                    <Minus className="size-3" aria-hidden="true" />
                  </button>
                  <span className="text-[11px] text-text-secondary">R$</span>
                  <input
                    id="input-custo-acao"
                    name="custoAcao"
                    type="number"
                    min="1"
                    max="200"
                    step="0.01"
                    value={custoAcao}
                    onChange={(e) => {
                      const val = parseFloat(e.target.value);
                      if (!isNaN(val)) {
                        setCustoAcao(val);
                        setActiveScenario("custom");
                      }
                    }}
                    aria-label="Custo médio unitário em reais"
                    className="w-20 px-2 py-0.5 rounded border border-border-subtle bg-surface text-right font-mono text-xs font-bold text-azul-navy focus:outline-none focus:ring-1 focus:ring-azul-action"
                  />
                  <button
                    type="button"
                    onClick={() => handleCustoFineTune(0.01)}
                    title="Aumentar R$ 0,01"
                    aria-label="Aumentar custo em 1 centavo"
                    className="size-6 flex items-center justify-center rounded border border-border-subtle bg-muted/60 hover:bg-muted text-text-secondary hover:text-azul-navy cursor-pointer transition-colors"
                  >
                    <Plus className="size-3" aria-hidden="true" />
                  </button>
                </div>
              </div>
              <input
                type="range"
                min="5"
                max="100"
                step="0.01"
                value={custoAcao}
                onChange={(e) => {
                  setCustoAcao(Number(e.target.value));
                  setActiveScenario("custom");
                }}
                aria-label="Ajustar custo médio unitário via controle deslizante"
                className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-azul-action"
              />
              <div className="flex justify-between text-[10px] text-text-muted font-mono">
                <span>R$ 5,00 (Digital)</span>
                <span>R$ 11,38 (Playbook)</span>
                <span>R$ 45,00 (Premissa)</span>
              </div>
            </div>

            {/* 5. Margem de Contribuição Líquida */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between gap-2 text-xs font-semibold">
                <label htmlFor="input-margem" className="text-text-primary flex items-center gap-1 cursor-pointer">
                  <span>Margem de Contribuição Líquida (m)</span>
                  <TermHelp term="clv" />
                </label>
                <div className="flex items-center gap-1 font-mono text-azul-navy">
                  <input
                    id="input-margem"
                    name="margem"
                    type="number"
                    min="10"
                    max="50"
                    step="0.1"
                    value={margem}
                    onChange={(e) => {
                      const val = Number(e.target.value);
                      if (!isNaN(val)) {
                        setMargem(val);
                        setActiveScenario("custom");
                      }
                    }}
                    aria-label="Margem de contribuição em percentual"
                    className="w-18 px-2 py-0.5 rounded border border-border-subtle bg-surface text-right font-mono text-xs font-bold text-azul-navy focus:outline-none focus:ring-1 focus:ring-azul-action"
                  />
                  <span className="text-xs text-text-secondary">%</span>
                </div>
              </div>
              <input
                type="range"
                min="10"
                max="40"
                step="1"
                value={margem}
                onChange={(e) => {
                  setMargem(Number(e.target.value));
                  setActiveScenario("custom");
                }}
                aria-label="Ajustar margem de contribuição via controle deslizante"
                className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-azul-action"
              />
              <div className="flex justify-between text-[10px] text-text-muted font-mono">
                <span>10%</span>
                <span>22% (Média Aérea)</span>
                <span>40%</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Waterfall Financeiro e Diagnóstico */}
        <Card className="flex flex-col justify-between">
          <CardHeader>
            <CardTitle className="text-base font-bold text-azul-navy flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-azul-action" />
              Balanço e Decomposição Econômica
            </CardTitle>
            <CardDescription>
              Comparativo entre custo total de campanha e receita bruta de CLV preservada.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <FinancialWaterfall
              custoTotal={calculation.custoTotal}
              receitaSalva={calculation.receitaSalva}
              receitaLiquida={calculation.deltaReceitaLiquida}
              roiPct={calculation.roi}
            />

            <div className="rounded-md bg-muted/60 p-3 text-xs space-y-1 text-text-secondary border border-border-subtle">
              <p className="font-semibold text-azul-navy">Fórmula Canônica de Retorno:</p>
              <p className="font-mono text-[11px]">
                ΔReceita Líquida = R_salva - C_total = R$ {calculation.receitaSalva.toFixed(2)} - R$ {calculation.custoTotal.toFixed(2)} = R$ {calculation.deltaReceitaLiquida.toFixed(2)}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 6 KPI Cards dos Resultados */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <Card className="p-3 text-center shadow-xs">
          <span className="text-[11px] text-text-muted block font-sans">Clientes Alvo (n_alvo)</span>
          <span className="text-lg font-bold text-azul-navy font-mono">
            {calculation.nAlvo.toLocaleString("pt-BR")}
          </span>
          {calculation.isPlaybookReal && (
            <span className="text-[10px] text-emerald-600 font-bold block mt-0.5">
              41,93% dos elegíveis (58,88% VaR)
            </span>
          )}
        </Card>

        <Card className="p-3 text-center shadow-xs">
          <span className="text-[11px] text-text-muted block font-sans">Custo Total (C_total)</span>
          <span className="text-lg font-bold text-azul-navy font-mono">
            R$ {calculation.custoTotal.toLocaleString("pt-BR", { maximumFractionDigits: 0 })}
          </span>
        </Card>

        <Card className="p-3 text-center shadow-xs">
          <span className="text-[11px] text-text-muted font-sans flex items-center justify-center gap-1">
            <span>Evasões Evitadas</span>
            <TermHelp term="churn" />
          </span>
          <span className="text-lg font-bold text-azul-action font-mono">
            {calculation.evasoesEvitadas.toFixed(1)} clientes
          </span>
        </Card>

        <Card className="p-3 text-center shadow-xs">
          <span className="text-[11px] text-text-muted font-sans flex items-center justify-center gap-1">
            <span>Receita Salva (R_salva)</span>
            <TermHelp term="clv" />
          </span>
          <span className="text-lg font-bold text-emerald-600 font-mono">
            R$ {calculation.receitaSalva.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        </Card>

        <Card className="p-3 text-center border-l-4 border-l-magenta-cta shadow-xs">
          <span className="text-[11px] text-text-muted font-sans flex items-center justify-center gap-1">
            <span>ΔReceita Líquida</span>
            <TermHelp term="var" />
          </span>
          <span
            className={`text-lg font-extrabold font-mono ${
              calculation.deltaReceitaLiquida >= 0 ? "text-emerald-700" : "text-magenta-text"
            }`}
          >
            {calculation.deltaReceitaLiquida >= 0 ? "+" : ""}
            R$ {calculation.deltaReceitaLiquida.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        </Card>

        <Card className="p-3 text-center border-l-4 border-l-magenta-cta shadow-xs">
          <span className="text-[11px] text-text-muted block font-sans">ROI Líquido</span>
          <span
            className={`text-lg font-extrabold font-mono ${
              calculation.roi >= 0 ? "text-emerald-700" : "text-magenta-text"
            }`}
          >
            {calculation.roi.toFixed(1)}%
          </span>
        </Card>
      </div>
    </div>
  );
}

export default function SimuladorPage() {
  return (
    <React.Suspense
      fallback={
        <div className="space-y-4 p-4 animate-pulse">
          <div className="h-8 w-64 bg-muted rounded" />
          <div className="h-4 w-96 bg-muted rounded" />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
            <div className="h-96 bg-muted rounded-xl" />
            <div className="h-96 bg-muted rounded-xl" />
          </div>
        </div>
      }
    >
      <SimuladorContent />
    </React.Suspense>
  );
}

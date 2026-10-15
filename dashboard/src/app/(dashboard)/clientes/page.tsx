"use client";

import * as React from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import {
  Search,
  X,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  ArrowRight,
  TableProperties,
  Sparkles,
  AlertCircle,
  RefreshCw,
} from "lucide-react";
import {
  Card,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { TierBadge } from "@/components/branding/tier-badge";
import { TermHelp } from "@/components/help/term-help";
import { cn } from "@/lib/utils";
import type { CustomerScore } from "@/types/analytics";

const PERSONA_LABELS: Record<string, { label: string; color: string }> = {
  executivo_recorrente: { label: "Executivo Recorrente", color: "#033774" },
  lazer_premium: { label: "Lazer Premium", color: "#E832A5" },
  maximizador_milhas: { label: "Maximizador de Milhas", color: "#0874B5" },
  regional_dependente: { label: "Regional Dependente", color: "#0B3558" },
  eventual_ascendente: { label: "Eventual Ascendente", color: "#008BC4" },
  eventual_promocional: { label: "Eventual Promocional", color: "#657681" },
};

const TIER_OPTIONS = [
  { value: "", label: "Todas as Categorias (Tiers)" },
  { value: "azul", label: "Azul" },
  { value: "topazio", label: "Topázio" },
  { value: "safira", label: "Safira" },
  { value: "diamante", label: "Diamante" },
  { value: "unique", label: "Diamante Unique" },
];

const PERSONA_OPTIONS = [
  { value: "", label: "Todas as Personas" },
  { value: "executivo_recorrente", label: "Executivo Recorrente" },
  { value: "lazer_premium", label: "Lazer Premium" },
  { value: "maximizador_milhas", label: "Maximizador de Milhas" },
  { value: "regional_dependente", label: "Regional Dependente" },
  { value: "eventual_ascendente", label: "Eventual Ascendente" },
  { value: "eventual_promocional", label: "Eventual Promocional" },
];

type SortField =
  | "customer_id"
  | "valor_em_risco"
  | "clv_12m_previsto"
  | "churn_prob"
  | "score_av";

function ClientesTableContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Estados dos filtros inicializados a partir da URL
  const [searchInput, setSearchInput] = React.useState<string>(
    searchParams.get("search") || ""
  );
  const [debouncedSearch, setDebouncedSearch] = React.useState<string>(
    searchParams.get("search") || ""
  );
  const [tierFilter, setTierFilter] = React.useState<string>(
    searchParams.get("tier") || ""
  );
  const [personaFilter, setPersonaFilter] = React.useState<string>(
    searchParams.get("persona") || ""
  );
  const [altoValorFilter, setAltoValorFilter] = React.useState<boolean>(
    searchParams.get("alto_valor") === "true"
  );

  // Estados da paginação e ordenação
  const [page, setPage] = React.useState<number>(
    parseInt(searchParams.get("page") || "1", 10)
  );
  const [pageSize, setPageSize] = React.useState<number>(
    parseInt(searchParams.get("page_size") || "20", 10)
  );
  const [sortBy, setSortBy] = React.useState<SortField>(
    (searchParams.get("sort_by") as SortField) || "valor_em_risco"
  );
  const [sortOrder, setSortOrder] = React.useState<"asc" | "desc">(
    searchParams.get("sort_order") === "asc" ? "asc" : "desc"
  );

  // Dados carregados da API e controle de status/erro
  const [customers, setCustomers] = React.useState<CustomerScore[]>([]);
  const [total, setTotal] = React.useState<number>(0);
  const [totalPages, setTotalPages] = React.useState<number>(1);
  const [isLoading, setIsLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);
  const [retryTrigger, setRetryTrigger] = React.useState<number>(0);

  // Debounce da busca textual (~300ms)
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchInput.trim());
      setPage(1); // Retorna à primeira página em nova busca
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  // Clamp defensivo de página
  React.useEffect(() => {
    if (totalPages > 0 && page > totalPages) {
      setPage(1);
    }
  }, [totalPages, page]);

  // Busca dados na API ao alterar filtros, ordenação ou página, com AbortController e Sincronização de URL
  React.useEffect(() => {
    const controller = new AbortController();
    setIsLoading(true);
    setError(null);

    const params = new URLSearchParams();
    params.set("page", String(page));
    params.set("page_size", String(pageSize));
    if (debouncedSearch) params.set("search", debouncedSearch);
    if (tierFilter) params.set("tier", tierFilter);
    if (personaFilter) params.set("persona", personaFilter);
    if (altoValorFilter) params.set("alto_valor", "true");
    params.set("sort_by", sortBy);
    params.set("sort_order", sortOrder);

    // Sincroniza parâmetros na URL do navegador
    router.replace(`?${params.toString()}`, { scroll: false });

    fetch(`/api/customers?${params.toString()}`, { signal: controller.signal })
      .then((res) => {
        if (!res.ok) throw new Error("Falha ao buscar dados de clientes na API");
        return res.json();
      })
      .then((data) => {
        const receivedData = data.data || [];
        const receivedTotal = data.total || 0;
        const calculatedTotalPages = data.total_pages || 1;

        setCustomers(receivedData);
        setTotal(receivedTotal);
        setTotalPages(calculatedTotalPages);

        if (calculatedTotalPages > 0 && page > calculatedTotalPages) {
          setPage(1);
        }
        setError(null);
      })
      .catch((err) => {
        if (err.name !== "AbortError") {
          console.error("Erro na busca de clientes:", err);
          setError(err.message || "Erro inesperado ao consultar a base de clientes.");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      });

    return () => {
      controller.abort();
    };
  }, [
    page,
    pageSize,
    debouncedSearch,
    tierFilter,
    personaFilter,
    altoValorFilter,
    sortBy,
    sortOrder,
    retryTrigger,
    router,
  ]);

  // Handler para alternar ordenação ao clicar no cabeçalho
  const handleSort = (field: SortField) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(field);
      setSortOrder("desc"); // Maior para menor por padrão em novas métricas
    }
    setPage(1);
  };

  const hasActiveFilters = Boolean(
    debouncedSearch || tierFilter || personaFilter || altoValorFilter
  );

  const resetFilters = () => {
    setSearchInput("");
    setDebouncedSearch("");
    setTierFilter("");
    setPersonaFilter("");
    setAltoValorFilter(false);
    setPage(1);
  };

  const startIndex = (page - 1) * pageSize;
  const endIndex = Math.min(total, page * pageSize);

  const renderSortIcon = (field: SortField) => {
    if (sortBy !== field) {
      return <ArrowUpDown className="h-3 w-3 opacity-30 group-hover:opacity-70 transition-opacity" />;
    }
    return sortOrder === "asc" ? (
      <ArrowUp className="h-3.5 w-3.5 text-azul-action font-bold" />
    ) : (
      <ArrowDown className="h-3.5 w-3.5 text-azul-action font-bold" />
    );
  };

  return (
    <div className="space-y-6">
      {/* Header da Tela */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border-subtle pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-azul-action">
              Módulo 00
            </span>
            <span className="text-border-dark">•</span>
            <Badge variant="outline" className="text-[11px] font-mono bg-muted/50">
              50.000 Registros Coorte Calibrada
            </Badge>
          </div>
          <h1 className="text-2xl font-extrabold text-azul-navy tracking-tight mt-0.5 flex items-center gap-2">
            <TableProperties className="h-6 w-6 text-azul-action" />
            <span>Base Completa de Clientes</span>
          </h1>
          <p className="text-sm text-text-secondary">
            Visão granular dos 50k clientes com filtros multicritério, ordenação por risco e acesso direto ao Cliente 360°.
          </p>
        </div>

        {/* Contador Rápido */}
        <div className="flex items-center gap-3">
          <div className="rounded-lg border border-border-subtle bg-surface px-3 py-1.5 shadow-2xs text-right">
            <span className="text-[10px] text-text-muted uppercase font-sans font-semibold block">
              Total Encontrado
            </span>
            <span className="text-lg font-bold font-mono text-azul-navy">
              {total.toLocaleString("pt-BR")}
            </span>
          </div>
        </div>
      </div>

      {/* Barra de Filtros Integrada */}
      <Card className="shadow-xs border border-border-subtle">
        <CardContent className="p-4 space-y-3">
          <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
            {/* Input de Busca Textual por ID */}
            <div className="relative flex-1 min-w-[240px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted pointer-events-none" />
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Buscar por ID do cliente (ex: C038454)..."
                aria-label="Buscar clientes por ID ou rota"
                className="w-full h-9 pl-9 pr-8 rounded-md border border-border-subtle bg-surface text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-azul-action focus:border-azul-action"
              />
              {searchInput && (
                <button
                  type="button"
                  onClick={() => setSearchInput("")}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary p-0.5 rounded cursor-pointer"
                  title="Limpar busca"
                  aria-label="Limpar campo de busca"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>

            {/* Dropdown de Categoria / Tier */}
            <div className="w-full sm:w-52">
              <select
                value={tierFilter}
                onChange={(e) => {
                  setTierFilter(e.target.value);
                  setPage(1);
                }}
                aria-label="Filtrar por Categoria ou Tier"
                className="w-full h-9 px-3 rounded-md border border-border-subtle bg-surface text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-azul-action focus:border-azul-action cursor-pointer"
              >
                {TIER_OPTIONS.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Dropdown de Persona */}
            <div className="w-full sm:w-56">
              <select
                value={personaFilter}
                onChange={(e) => {
                  setPersonaFilter(e.target.value);
                  setPage(1);
                }}
                aria-label="Filtrar por Persona"
                className="w-full h-9 px-3 rounded-md border border-border-subtle bg-surface text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-azul-action focus:border-azul-action cursor-pointer"
              >
                {PERSONA_OPTIONS.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Toggle de Apenas Alto Valor */}
            <button
              type="button"
              onClick={() => {
                setAltoValorFilter(!altoValorFilter);
                setPage(1);
              }}
              aria-label="Alternar filtro apenas clientes de alto valor P90"
              className={cn(
                "h-9 px-3.5 rounded-md border text-xs font-semibold flex items-center justify-center gap-2 transition-all cursor-pointer whitespace-nowrap",
                altoValorFilter
                  ? "bg-azul-navy text-white border-azul-navy shadow-xs"
                  : "bg-surface border-border-subtle text-text-secondary hover:bg-muted/60"
              )}
            >
              <Sparkles
                className={cn(
                  "h-3.5 w-3.5",
                  altoValorFilter ? "text-lime-campaign" : "text-text-muted"
                )}
              />
              <span>Apenas Alto Valor (P90)</span>
            </button>

            {/* Botão Limpar Filtros */}
            {hasActiveFilters && (
              <Button
                variant="ghost"
                size="sm"
                onClick={resetFilters}
                aria-label="Limpar todos os filtros ativos"
                className="h-9 px-2.5 text-xs text-magenta-cta hover:bg-magenta-cta/10 hover:text-magenta-cta cursor-pointer gap-1"
              >
                <X className="h-3.5 w-3.5" />
                <span>Limpar</span>
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Tabela de Clientes */}
      <Card className="shadow-xs border border-border-subtle overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse">
            <thead className="bg-muted text-azul-navy font-semibold uppercase tracking-wider text-[11px] border-b border-border-subtle select-none">
              <tr>
                <th
                  className="p-3.5"
                  aria-sort={
                    sortBy === "customer_id"
                      ? sortOrder === "asc"
                        ? "ascending"
                        : "descending"
                      : "none"
                  }
                >
                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={() => handleSort("customer_id")}
                      aria-label="Ordenar por Cliente ID"
                      className="group inline-flex items-center gap-1.5 hover:text-azul-action cursor-pointer"
                    >
                      <span>Cliente (ID)</span>
                      {renderSortIcon("customer_id")}
                    </button>
                  </div>
                </th>

                <th className="p-3.5">Categoria / Tier</th>

                <th className="p-3.5">
                  <div className="flex items-center gap-1.5">
                    <span>Persona</span>
                    <TermHelp term="personas" />
                  </div>
                </th>

                <th
                  className="p-3.5 text-right"
                  aria-sort={
                    sortBy === "valor_em_risco"
                      ? sortOrder === "asc"
                        ? "ascending"
                        : "descending"
                      : "none"
                  }
                >
                  <div className="flex items-center justify-end gap-1.5">
                    <button
                      type="button"
                      onClick={() => handleSort("valor_em_risco")}
                      aria-label="Ordenar por VaR Total"
                      className="group inline-flex items-center gap-1.5 hover:text-azul-action cursor-pointer"
                    >
                      <span>VaR Total</span>
                      {renderSortIcon("valor_em_risco")}
                    </button>
                    <TermHelp term="var" />
                  </div>
                </th>

                <th
                  className="p-3.5 text-right"
                  aria-sort={
                    sortBy === "clv_12m_previsto"
                      ? sortOrder === "asc"
                        ? "ascending"
                        : "descending"
                      : "none"
                  }
                >
                  <div className="flex items-center justify-end gap-1.5">
                    <button
                      type="button"
                      onClick={() => handleSort("clv_12m_previsto")}
                      aria-label="Ordenar por CLV 12M"
                      className="group inline-flex items-center gap-1.5 hover:text-azul-action cursor-pointer"
                    >
                      <span>CLV 12M</span>
                      {renderSortIcon("clv_12m_previsto")}
                    </button>
                    <TermHelp term="clv" />
                  </div>
                </th>

                <th
                  className="p-3.5 text-right"
                  aria-sort={
                    sortBy === "churn_prob"
                      ? sortOrder === "asc"
                        ? "ascending"
                        : "descending"
                      : "none"
                  }
                >
                  <div className="flex items-center justify-end gap-1.5">
                    <button
                      type="button"
                      onClick={() => handleSort("churn_prob")}
                      aria-label="Ordenar por Probabilidade de Churn"
                      className="group inline-flex items-center gap-1.5 hover:text-azul-action cursor-pointer"
                    >
                      <span>Prob. Churn</span>
                      {renderSortIcon("churn_prob")}
                    </button>
                    <TermHelp term="churn" />
                  </div>
                </th>

                <th
                  className="p-3.5 text-right"
                  aria-sort={
                    sortBy === "score_av"
                      ? sortOrder === "asc"
                        ? "ascending"
                        : "descending"
                      : "none"
                  }
                >
                  <div className="flex items-center justify-end gap-1.5">
                    <button
                      type="button"
                      onClick={() => handleSort("score_av")}
                      aria-label="Ordenar por Score Alto Valor"
                      className="group inline-flex items-center gap-1.5 hover:text-azul-action cursor-pointer"
                    >
                      <span>Score AV</span>
                      {renderSortIcon("score_av")}
                    </button>
                    <TermHelp term="score_av" />
                  </div>
                </th>

                <th className="p-3.5 text-center">Ações</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-border-subtle bg-surface">
              {isLoading ? (
                // Skeleton Rows durante carregamento
                Array.from({ length: Math.min(10, pageSize) }).map((_, idx) => (
                  <tr key={idx} className="animate-pulse">
                    <td className="p-3.5">
                      <div className="h-4 w-20 bg-muted rounded" />
                    </td>
                    <td className="p-3.5">
                      <div className="h-4 w-16 bg-muted rounded" />
                    </td>
                    <td className="p-3.5">
                      <div className="h-4 w-32 bg-muted rounded" />
                    </td>
                    <td className="p-3.5 text-right">
                      <div className="h-4 w-20 bg-muted rounded ml-auto" />
                    </td>
                    <td className="p-3.5 text-right">
                      <div className="h-4 w-20 bg-muted rounded ml-auto" />
                    </td>
                    <td className="p-3.5 text-right">
                      <div className="h-4 w-12 bg-muted rounded ml-auto" />
                    </td>
                    <td className="p-3.5 text-right">
                      <div className="h-4 w-12 bg-muted rounded ml-auto" />
                    </td>
                    <td className="p-3.5 text-center">
                      <div className="h-7 w-20 bg-muted rounded mx-auto" />
                    </td>
                  </tr>
                ))
              ) : error ? (
                // Estado de Erro com Ação de Retry
                <tr>
                  <td colSpan={8} className="p-12 text-center">
                    <div className="flex flex-col items-center justify-center gap-3 max-w-md mx-auto">
                      <div className="p-3 bg-magenta-cta/10 text-magenta-cta rounded-full">
                        <AlertCircle className="h-7 w-7" />
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm font-semibold text-text-primary">
                          Falha ao carregar a base de clientes
                        </p>
                        <p className="text-xs text-text-secondary">
                          {error}
                        </p>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setRetryTrigger((prev) => prev + 1)}
                        className="mt-2 text-xs gap-1.5 cursor-pointer text-azul-navy hover:text-azul-action border-border-subtle hover:bg-accent"
                        aria-label="Tentar carregar os clientes novamente"
                      >
                        <RefreshCw className="h-3.5 w-3.5" />
                        <span>Tentar novamente</span>
                      </Button>
                    </div>
                  </td>
                </tr>
              ) : customers.length === 0 ? (
                // Estado Vazio
                <tr>
                  <td colSpan={8} className="p-12 text-center text-text-muted">
                    <div className="flex flex-col items-center justify-center gap-2">
                      <AlertCircle className="h-8 w-8 text-text-muted" />
                      <p className="text-sm font-semibold text-text-primary">
                        Nenhum cliente encontrado
                      </p>
                      <p className="text-xs text-text-secondary max-w-sm">
                        Nenhum registro corresponde aos filtros selecionados. Tente ajustar os parâmetros ou limpe os filtros.
                      </p>
                      {hasActiveFilters && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={resetFilters}
                          aria-label="Limpar todos os filtros da tabela"
                          className="mt-2 text-xs"
                        >
                          Limpar todos os filtros
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ) : (
                // Linhas da Tabela
                customers.map((c) => {
                  const personaInfo = PERSONA_LABELS[c.persona] || {
                    label: c.persona,
                    color: "#5E6F7A",
                  };

                  return (
                    <tr
                      key={c.customer_id}
                      className="hover:bg-muted/40 transition-colors group"
                    >
                      {/* ID do Cliente */}
                      <td className="p-3.5 font-mono">
                        <div className="flex items-center gap-1.5">
                          <Link
                            href={`/cliente-360?id=${c.customer_id}`}
                            className="font-bold text-azul-navy group-hover:text-azul-action transition-colors hover:underline"
                          >
                            {c.customer_id}
                          </Link>
                          {c.alto_valor && (
                            <Badge
                              variant="outline"
                              className="text-[10px] font-mono py-0 px-1 border-azul-action/40 bg-accent text-azul-action"
                            >
                              P90
                            </Badge>
                          )}
                        </div>
                      </td>

                      {/* Tier Badge */}
                      <td className="p-3.5">
                        <TierBadge tier={c.tier} showNewBadge={false} />
                      </td>

                      {/* Persona */}
                      <td className="p-3.5">
                        <div className="flex items-center gap-2">
                          <span
                            className="h-2.5 w-2.5 rounded-full shrink-0 shadow-2xs"
                            style={{ backgroundColor: personaInfo.color }}
                          />
                          <span className="text-text-primary font-medium truncate max-w-[170px]">
                            {personaInfo.label}
                          </span>
                        </div>
                      </td>

                      {/* VaR Total */}
                      <td className="p-3.5 text-right font-mono font-bold text-magenta-cta">
                        R${" "}
                        {c.valor_em_risco.toLocaleString("pt-BR", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </td>

                      {/* CLV 12M */}
                      <td className="p-3.5 text-right font-mono font-semibold text-azul-action">
                        R${" "}
                        {c.clv_12m_previsto.toLocaleString("pt-BR", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </td>

                      {/* Probabilidade de Churn */}
                      <td className="p-3.5 text-right font-mono font-semibold">
                        <span
                          className={
                            c.churn_prob >= 0.5
                              ? "text-magenta-cta"
                              : c.churn_prob >= 0.3
                              ? "text-amber-600"
                              : "text-emerald-700"
                          }
                        >
                          {(c.churn_prob * 100).toFixed(1)}%
                        </span>
                      </td>

                      {/* Score Alto Valor */}
                      <td className="p-3.5 text-right font-mono text-azul-navy">
                        {c.score_av.toFixed(3)}
                      </td>

                      {/* Ações */}
                      <td className="p-3.5 text-center">
                        <Link
                          href={`/cliente-360?id=${c.customer_id}`}
                          className="inline-flex items-center gap-1 rounded-md px-2.5 py-1 text-[11px] font-semibold text-azul-action hover:bg-accent transition-colors"
                        >
                          <span>Ver 360</span>
                          <ArrowRight className="h-3 w-3" />
                        </Link>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Rodapé de Paginação */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-3.5 border-t border-border-subtle bg-muted/20 text-xs">
          {/* Lado Esquerdo: Intervalo exibido e seletor de itens */}
          <div className="flex items-center gap-4 text-text-secondary">
            <span>
              Mostrando <strong className="font-mono text-azul-navy">{total > 0 ? startIndex + 1 : 0}</strong> a{" "}
              <strong className="font-mono text-azul-navy">{endIndex}</strong> de{" "}
              <strong className="font-mono text-azul-navy">{total.toLocaleString("pt-BR")}</strong> registros
            </span>

            <div className="flex items-center gap-1.5">
              <span className="text-text-muted">Por página:</span>
              <select
                value={pageSize}
                onChange={(e) => {
                  setPageSize(Number(e.target.value));
                  setPage(1);
                }}
                aria-label="Selecionar quantidade de registros por página"
                className="h-7 px-2 rounded border border-border-subtle bg-surface text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-azul-action cursor-pointer"
              >
                <option value={20}>20</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
            </div>
          </div>

          {/* Lado Direito: Navegação de Páginas */}
          <div className="flex items-center gap-1.5">
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8 cursor-pointer disabled:pointer-events-none"
              onClick={() => setPage(1)}
              disabled={page <= 1 || isLoading}
              title="Primeira página"
              aria-label="Ir para a primeira página"
            >
              <ChevronsLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8 cursor-pointer disabled:pointer-events-none"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1 || isLoading}
              title="Página anterior"
              aria-label="Ir para a página anterior"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>

            <span className="px-3 font-medium text-azul-navy">
              Página <strong className="font-mono">{page}</strong> de{" "}
              <strong className="font-mono">{totalPages}</strong>
            </span>

            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8 cursor-pointer disabled:pointer-events-none"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages || isLoading}
              title="Próxima página"
              aria-label="Ir para a próxima página"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8 cursor-pointer disabled:pointer-events-none"
              onClick={() => setPage(totalPages)}
              disabled={page >= totalPages || isLoading}
              title="Última página"
              aria-label="Ir para a última página"
            >
              <ChevronsRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}

export default function ClientesPage() {
  return (
    <React.Suspense
      fallback={
        <div className="p-8 text-center text-xs text-text-muted space-y-2">
          <div className="h-8 w-8 rounded-full border-2 border-azul-action border-t-transparent animate-spin mx-auto" />
          <p>Carregando Base de Clientes...</p>
        </div>
      }
    >
      <ClientesTableContent />
    </React.Suspense>
  );
}

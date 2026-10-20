"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Search, Loader2, X, User } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { TierBadge } from "@/components/branding/tier-badge";
import { cn } from "@/lib/utils";
import type { CustomerScore, TierLevel } from "@/types/analytics";

export interface TopCustomerShortcut {
  customer_id: string;
  valor_em_risco: number;
  tier?: TierLevel | string;
}

interface CustomerSearchComboboxProps {
  currentCustomerId?: string;
  topCustomers?: TopCustomerShortcut[];
  className?: string;
}

export function CustomerSearchCombobox({
  currentCustomerId,
  topCustomers = [],
  className,
}: CustomerSearchComboboxProps) {
  const router = useRouter();
  const [query, setQuery] = React.useState<string>("");
  const [debouncedQuery, setDebouncedQuery] = React.useState<string>("");
  const [results, setResults] = React.useState<CustomerScore[]>([]);
  const [isLoading, setIsLoading] = React.useState<boolean>(false);
  const [isOpen, setIsOpen] = React.useState<boolean>(false);
  const [activeIndex, setActiveIndex] = React.useState<number>(-1);

  const containerRef = React.useRef<HTMLDivElement>(null);
  const inputRef = React.useRef<HTMLInputElement>(null);
  const listRef = React.useRef<HTMLUListElement>(null);

  // Debounce de 300ms para a consulta na API
  React.useEffect(() => {
    const trimmed = query.trim();
    if (!trimmed) {
      setDebouncedQuery("");
      setResults([]);
      setIsLoading(false);
      setIsOpen(false);
      return;
    }

    setIsLoading(true);
    const timer = setTimeout(() => {
      setDebouncedQuery(trimmed);
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  // Consulta API /api/customers quando debouncedQuery mudar
  React.useEffect(() => {
    if (!debouncedQuery) return;

    const controller = new AbortController();
    setIsLoading(true);

    fetch(
      `/api/customers?search=${encodeURIComponent(debouncedQuery)}&page_size=10`,
      { signal: controller.signal }
    )
      .then((res) => {
        if (!res.ok) throw new Error("Erro na busca de clientes");
        return res.json();
      })
      .then((data) => {
        setResults(data.data || []);
        setIsOpen(true);
        setActiveIndex(-1);
      })
      .catch((err) => {
        if (err.name !== "AbortError") {
          console.error("Falha ao buscar clientes no combobox:", err);
          setResults([]);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      });

    return () => controller.abort();
  }, [debouncedQuery]);

  // Fecha dropdown ao clicar fora
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
        setActiveIndex(-1);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelectCustomer = (customerId: string) => {
    setIsOpen(false);
    setActiveIndex(-1);
    setQuery("");
    router.push(`/cliente-360?id=${encodeURIComponent(customerId)}`);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen || results.length === 0) {
      if (e.key === "ArrowDown" && results.length > 0) {
        setIsOpen(true);
        setActiveIndex(0);
        e.preventDefault();
      }
      return;
    }

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setActiveIndex((prev) => (prev < results.length - 1 ? prev + 1 : 0));
        break;
      case "ArrowUp":
        e.preventDefault();
        setActiveIndex((prev) => (prev > 0 ? prev - 1 : results.length - 1));
        break;
      case "Enter":
        e.preventDefault();
        if (activeIndex >= 0 && activeIndex < results.length) {
          handleSelectCustomer(results[activeIndex].customer_id);
        } else if (results.length > 0) {
          handleSelectCustomer(results[0].customer_id);
        }
        break;
      case "Escape":
        e.preventDefault();
        setIsOpen(false);
        setActiveIndex(-1);
        break;
      case "Tab":
        setIsOpen(false);
        break;
    }
  };

  // Garante que o item com foco via teclado role para dentro da visualização
  React.useEffect(() => {
    if (activeIndex >= 0 && listRef.current) {
      const activeElement = listRef.current.children[activeIndex] as HTMLElement;
      if (activeElement) {
        activeElement.scrollIntoView({ block: "nearest" });
      }
    }
  }, [activeIndex]);

  const top5Shortcuts = topCustomers.slice(0, 5);

  return (
    <div ref={containerRef} className={cn("space-y-3", className)}>
      {/* Combobox de Busca */}
      <div className="relative">
        <label
          htmlFor="customer-search-combobox-input"
          className="block text-xs font-semibold text-azul-navy mb-1"
        >
          Pesquisar Cliente no Cockpit 360°
        </label>
        <div className="relative">
          <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none text-text-muted">
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin text-azul-action" />
            ) : (
              <Search className="h-4 w-4" />
            )}
          </div>

          <input
            ref={inputRef}
            id="customer-search-combobox-input"
            name="customer_search"
            type="text"
            role="combobox"
            aria-expanded={isOpen}
            aria-autocomplete="list"
            aria-controls="customer-search-combobox-list"
            aria-activedescendant={
              activeIndex >= 0 ? `customer-option-${activeIndex}` : undefined
            }
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              if (!isOpen && e.target.value.trim().length > 0) {
                setIsOpen(true);
              }
            }}
            onFocus={() => {
              if (results.length > 0) setIsOpen(true);
            }}
            onKeyDown={handleKeyDown}
            placeholder="Digite o ID do cliente (ex: C038454) ou rota favorita..."
            autoComplete="off"
            className="w-full h-10 pl-9 pr-9 rounded-lg border border-border-subtle bg-surface text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-azul-action/30 focus:border-azul-action shadow-2xs"
          />

          {query && (
            <button
              type="button"
              onClick={() => {
                setQuery("");
                setDebouncedQuery("");
                setResults([]);
                setIsOpen(false);
                inputRef.current?.focus();
              }}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary p-1 rounded-md transition-colors cursor-pointer"
              title="Limpar busca"
              aria-label="Limpar campo de busca de cliente"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {/* Dropdown de Resultados */}
        {isOpen && (
          <div className="absolute left-0 right-0 top-full mt-1.5 z-50 rounded-lg border border-border-subtle bg-surface shadow-lg overflow-hidden animate-in fade-in-0 zoom-in-95">
            {isLoading && results.length === 0 ? (
              <div className="p-4 text-center text-xs text-text-muted flex items-center justify-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-azul-action" />
                <span>Buscando clientes na base analítica...</span>
              </div>
            ) : results.length === 0 ? (
              <div className="p-4 text-center text-xs text-text-muted space-y-1">
                <p className="font-semibold text-text-primary">
                  Nenhum cliente localizado
                </p>
                <p className="text-[11px] text-text-secondary">
                  Nenhum registro para &quot;{debouncedQuery}&quot;. Tente outro ID.
                </p>
              </div>
            ) : (
              <ul
                ref={listRef}
                id="customer-search-combobox-list"
                role="listbox"
                aria-label="Resultados de busca de clientes"
                className="max-h-72 overflow-y-auto divide-y divide-border-subtle/50 py-1"
              >
                {results.map((cust, idx) => {
                  const isSelected = activeIndex === idx;
                  const isCurrent = cust.customer_id === currentCustomerId;

                  return (
                    <li
                      key={cust.customer_id}
                      id={`customer-option-${idx}`}
                      role="option"
                      aria-selected={isSelected}
                      onClick={() => handleSelectCustomer(cust.customer_id)}
                      onMouseEnter={() => setActiveIndex(idx)}
                      className={cn(
                        "px-3.5 py-2.5 flex items-center justify-between gap-3 text-xs cursor-pointer transition-colors",
                        isSelected
                          ? "bg-accent/70 text-azul-navy"
                          : "hover:bg-muted/40 text-text-primary",
                        isCurrent && "border-l-3 border-l-azul-action bg-accent/30"
                      )}
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        <div className="h-7 w-7 rounded-md bg-muted flex items-center justify-center shrink-0">
                          <User className="h-3.5 w-3.5 text-azul-navy" />
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-bold text-azul-navy">
                              {cust.customer_id}
                            </span>
                            <TierBadge tier={cust.tier} showNewBadge={false} />
                            {cust.alto_valor && (
                              <Badge
                                variant="outline"
                                className="text-[9px] font-mono py-0 px-1 border-azul-action/40 bg-accent text-azul-action"
                              >
                                P90
                              </Badge>
                            )}
                            {isCurrent && (
                              <span className="text-[10px] text-azul-action font-semibold">
                                (Atual)
                              </span>
                            )}
                          </div>
                          <p className="text-[11px] text-text-secondary truncate mt-0.5">
                            Persona: {cust.persona}
                            {cust.rota_favorita && ` • Rota: ${cust.rota_favorita}`}
                          </p>
                        </div>
                      </div>

                      <div className="text-right shrink-0">
                        <span className="block text-[10px] text-text-muted uppercase font-sans font-semibold">
                          Valor em Risco
                        </span>
                        <span className="font-mono font-bold text-magenta-text">
                          R${" "}
                          {cust.valor_em_risco.toLocaleString("pt-BR", {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </span>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        )}
      </div>

      {/* Chips Rápidos dos Top 5 VaR */}
      {top5Shortcuts.length > 0 && (
        <div className="space-y-1.5 pt-1">
          <span className="text-[11px] font-semibold text-text-secondary block">
            Atalhos Rápidos — Top 5 Valor em Risco da Carteira:
          </span>
          <div className="flex flex-wrap items-center gap-2">
            {top5Shortcuts.map((c, idx) => {
              const isCurrent = c.customer_id === currentCustomerId;
              return (
                <Link
                  key={c.customer_id}
                  href={`/cliente-360?id=${encodeURIComponent(c.customer_id)}`}
                  className={cn(
                    "inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-mono transition-all cursor-pointer",
                    isCurrent
                      ? "border-azul-action bg-azul-action text-white font-bold shadow-xs"
                      : "border-border-subtle bg-muted/40 hover:bg-muted text-azul-navy"
                  )}
                >
                  <span>{c.customer_id}</span>
                  <span
                    className={
                      isCurrent ? "text-lime-campaign" : "text-magenta-text"
                    }
                  >
                    R${" "}
                    {c.valor_em_risco.toLocaleString("pt-BR", {
                      maximumFractionDigits: 0,
                    })}
                  </span>
                  {idx === 0 && (
                    <span
                      className={cn(
                        "text-[10px] px-1 rounded font-sans font-bold",
                        isCurrent
                          ? "bg-white text-azul-action"
                          : "bg-magenta-cta text-white"
                      )}
                    >
                      Top 1
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

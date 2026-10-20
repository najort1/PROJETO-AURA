"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  UserCheck,
  Bot,
  AlertOctagon,
  Calculator,
  ShieldCheck,
  Search,
  ArrowRight,
  Sparkles,
  FileText,
  TableProperties,
  Loader2,
} from "lucide-react";
import {
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandSeparator,
  CommandShortcut,
} from "@/components/ui/command";
import { TierBadge } from "@/components/branding/tier-badge";
import type { CustomerScore } from "@/types/analytics";

interface CommandMenuProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export function CommandMenu({ open: externalOpen, onOpenChange }: CommandMenuProps) {
  const router = useRouter();
  const [internalOpen, setInternalOpen] = React.useState(false);

  const [query, setQuery] = React.useState("");
  const [debouncedQuery, setDebouncedQuery] = React.useState("");
  const [customers, setCustomers] = React.useState<CustomerScore[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);

  const isOpen = externalOpen !== undefined ? externalOpen : internalOpen;
  const setIsOpen = onOpenChange !== undefined ? onOpenChange : setInternalOpen;

  // Atalho global Cmd+K / Ctrl+K
  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setIsOpen(!isOpen);
      }
    };

    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, [isOpen, setIsOpen]);

  // Debounce do input (~280ms)
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query.trim());
    }, 280);
    return () => clearTimeout(timer);
  }, [query]);

  // Limpeza ao fechar
  React.useEffect(() => {
    if (!isOpen) {
      setQuery("");
      setDebouncedQuery("");
      setCustomers([]);
      setIsLoading(false);
    }
  }, [isOpen]);

  // Busca assíncrona na API de 50k clientes com 2+ caracteres
  React.useEffect(() => {
    if (debouncedQuery.length < 2) {
      setCustomers([]);
      setIsLoading(false);
      return;
    }

    const controller = new AbortController();
    setIsLoading(true);

    fetch(`/api/customers?search=${encodeURIComponent(debouncedQuery)}&page_size=6`, {
      signal: controller.signal,
    })
      .then((res) => {
        if (!res.ok) throw new Error("Falha ao consultar clientes");
        return res.json();
      })
      .then((data) => {
        if (data?.data) {
          setCustomers(data.data);
        }
      })
      .catch((err) => {
        if (err.name !== "AbortError") {
          console.error("Erro na busca do CommandMenu:", err);
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
  }, [debouncedQuery]);

  const runCommand = React.useCallback(
    (command: () => void) => {
      setIsOpen(false);
      command();
    },
    [setIsOpen]
  );

  // Validação de formato de ID de cliente: ex: C038454 ou C1234567
  const customerIdRegex = /^C\d{4,7}$/i;
  const cleanQuery = query.trim().toUpperCase();
  const directCustomerId = customerIdRegex.test(cleanQuery) ? cleanQuery : null;
  const isPending =
    (query.trim().length >= 2 && query.trim() !== debouncedQuery) || isLoading;

  return (
    <CommandDialog open={isOpen} onOpenChange={setIsOpen}>
      <CommandInput
        placeholder="Digite rota, cliente (ex: C038454) ou comando..."
        value={query}
        onValueChange={setQuery}
      />
      <CommandList>
        <CommandEmpty>
          {isPending ? (
            <span className="flex items-center justify-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin text-azul-action" />
              Buscando na base de 50.000 clientes...
            </span>
          ) : (
            "Nenhum resultado encontrado."
          )}
        </CommandEmpty>

        {/* Opção Destacada Imediata para ID de Cliente Válido */}
        {directCustomerId && (
          <CommandGroup heading="Acesso Direto ao Cliente">
            <CommandItem
              value={`abrir-cliente-360-${directCustomerId} ${directCustomerId}`}
              onSelect={() =>
                runCommand(() => router.push(`/cliente-360?id=${directCustomerId}`))
              }
              className="bg-accent/80 hover:bg-accent text-azul-navy font-semibold border border-azul-action/40"
            >
              <UserCheck className="mr-2 h-4 w-4 text-azul-action" />
              <span>
                Abrir Cliente 360 para{" "}
                <strong className="font-mono text-azul-action font-bold">
                  {directCustomerId}
                </strong>
              </span>
              <CommandShortcut>Enter ↵</CommandShortcut>
            </CommandItem>
          </CommandGroup>
        )}

        {/* Clientes Encontrados via API */}
        {customers.length > 0 && (
          <CommandGroup heading={`Clientes Encontrados na Base (${customers.length})`}>
            {customers.map((c) => (
              <CommandItem
                key={c.customer_id}
                value={`${c.customer_id} ${c.tier} ${c.persona} ${c.valor_em_risco}`}
                onSelect={() =>
                  runCommand(() => router.push(`/cliente-360?id=${c.customer_id}`))
                }
                className="flex items-center justify-between"
              >
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-azul-navy">
                    {c.customer_id}
                  </span>
                  <TierBadge tier={c.tier} showNewBadge={false} className="text-[10px] py-0 px-1" />
                  <span className="text-xs text-text-secondary">{c.persona}</span>
                </div>
                <span className="font-mono text-xs font-bold text-magenta-text">
                  VaR R${" "}
                  {c.valor_em_risco.toLocaleString("pt-BR", {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </span>
              </CommandItem>
            ))}
          </CommandGroup>
        )}

        {directCustomerId || customers.length > 0 ? <CommandSeparator /> : null}

        <CommandGroup heading="Módulos & Telas Analíticas">
          <CommandItem
            onSelect={() => runCommand(() => router.push("/clientes"))}
          >
            <TableProperties className="mr-2 h-4 w-4 text-azul-primary" />
            <span>00 · Base de Clientes (50k) & Filtros Avançados</span>
            <CommandShortcut>G B</CommandShortcut>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/carteira"))}
          >
            <LayoutDashboard className="mr-2 h-4 w-4 text-azul-action" />
            <span>01 · Visão da Carteira e VaR Total</span>
            <CommandShortcut>G C</CommandShortcut>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/personas"))}
          >
            <Users className="mr-2 h-4 w-4 text-azul-deep" />
            <span>02 · Personas & Segmentação Comportamental</span>
            <CommandShortcut>G P</CommandShortcut>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/cliente-360"))}
          >
            <UserCheck className="mr-2 h-4 w-4 text-azul-primary" />
            <span>03 · Cliente 360 & Explicabilidade SHAP</span>
            <CommandShortcut>G 3</CommandShortcut>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/concierge"))}
          >
            <Sparkles className="mr-2 h-4 w-4 text-magenta-cta" />
            <span>Aura Concierge · Chat com IA & Tools em Tempo Real</span>
            <CommandShortcut>G A</CommandShortcut>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/agente"))}
          >
            <Bot className="mr-2 h-4 w-4 text-azul-action" />
            <span>04 · Cockpit Agente NBA & Kanban de Retenção</span>
            <CommandShortcut>G K</CommandShortcut>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/atritos"))}
          >
            <AlertOctagon className="mr-2 h-4 w-4 text-amber-500" />
            <span>05 · Mapa de Sentimento & Atritos</span>
            <CommandShortcut>G S</CommandShortcut>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/simulador"))}
          >
            <Calculator className="mr-2 h-4 w-4 text-azul-action" />
            <span>06 · Simulador de Impacto Financeiro</span>
            <CommandShortcut>G F</CommandShortcut>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/ia-responsavel"))}
          >
            <ShieldCheck className="mr-2 h-4 w-4 text-emerald-600" />
            <span>07 · IA Responsável & Governança LGPD</span>
            <CommandShortcut>G I</CommandShortcut>
          </CommandItem>
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Clientes Prioritários (Amostra Rápida)">
          <CommandItem
            onSelect={() => runCommand(() => router.push("/cliente-360?id=C038454"))}
          >
            <span className="font-mono text-xs font-bold text-magenta-text mr-2">C038454</span>
            <span>Topázio • Top 1 VaR (R$ 3.109,29) • Eventual Ascendente</span>
            <CommandShortcut>Enter</CommandShortcut>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/cliente-360?id=C019283"))}
          >
            <span className="font-mono text-xs font-bold text-azul-action mr-2">C019283</span>
            <span>Topázio • Regional Dependente • VaR R$ 339,64</span>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/cliente-360?id=C044129"))}
          >
            <span className="font-mono text-xs font-bold text-azul-action mr-2">C044129</span>
            <span>Topázio • Eventual Ascendente • CLV R$ 1.214,15</span>
          </CommandItem>
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Atalhos Rápidos de Operação">
          <CommandItem
            onSelect={() => runCommand(() => router.push("/simulador?scenario=base"))}
          >
            <Sparkles className="mr-2 h-4 w-4 text-lime-campaign" />
            <span>Abrir Simulador no Cenário Base (R$ 80.000)</span>
          </CommandItem>
          <CommandItem
            onSelect={() => runCommand(() => router.push("/agente?filter=hitl"))}
          >
            <FileText className="mr-2 h-4 w-4 text-text-secondary" />
            <span>Filtrar Casos Pendentes de Aprovação Humana (HITL)</span>
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}

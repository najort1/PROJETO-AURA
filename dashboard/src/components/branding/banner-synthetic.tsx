import * as React from "react";
import { ShieldCheck, Info } from "lucide-react";

export function BannerSynthetic() {
  return (
    <div className="flex items-center justify-between border-b border-border-subtle bg-slate-900 px-4 py-1.5 text-xs text-slate-200">
      <div className="flex items-center gap-2">
        <ShieldCheck className="h-4 w-4 text-lime-campaign" />
        <span className="font-semibold text-lime-campaign tracking-wide uppercase">
          Ambiente Analítico Homologado
        </span>
        <span className="text-slate-400">|</span>
        <span className="text-slate-300">
          Base Sintética Calibrada — Em conformidade estrita com a LGPD (Lei nº 13.709/2018)
        </span>
      </div>
      <div className="hidden sm:flex items-center gap-1.5 text-slate-400 text-[11px]">
        <Info className="h-3.5 w-3.5 text-azul-primary" />
        <span>PROJETO AURA 2.0 • Azul Fidelidade</span>
      </div>
    </div>
  );
}

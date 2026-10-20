import * as React from "react";
import { cn } from "@/lib/utils";

export type TierType = "Azul" | "Topázio" | "Safira" | "Diamante" | "Diamante Unique" | string;

interface TierBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tier: TierType;
  showNewBadge?: boolean;
}

const tierStyles: Record<string, { bg: string; text: string; border: string }> = {
  azul: {
    bg: "bg-[#9AE0E8]",
    text: "text-[#0B4760]",
    border: "border-[#78D8F3]",
  },
  topazio: {
    bg: "bg-[#39B4DB]",
    text: "text-[#073C62]",
    border: "border-[#2DA6D4]",
  },
  safira: {
    bg: "bg-[#0F74A8]",
    text: "text-white",
    border: "border-[#08648F]",
  },
  diamante: {
    bg: "bg-[#064C82]",
    text: "text-white",
    border: "border-[#083E5B]",
  },
  "diamante unique": {
    bg: "bg-[#062B52]",
    text: "text-white",
    border: "border-[#032943]",
  },
};

export function TierBadge({ tier, showNewBadge = true, className, ...props }: TierBadgeProps) {
  const normalizedTier = (tier || "").toLowerCase().trim();
  const isUnique = normalizedTier.includes("unique");
  const isDiamante = normalizedTier === "diamante" || (normalizedTier.includes("diamante") && !isUnique);
  const isSafira = normalizedTier.includes("safira");
  const isTopazio = normalizedTier.includes("topazio") || normalizedTier.includes("topázio");
  const isAzul = normalizedTier.includes("azul") || (!isUnique && !isDiamante && !isSafira && !isTopazio);

  const styleKey = isUnique
    ? "diamante unique"
    : isDiamante
    ? "diamante"
    : isSafira
    ? "safira"
    : isTopazio
    ? "topazio"
    : "azul";

  const style = tierStyles[styleKey] || tierStyles.azul;

  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        className={cn(
          "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold tracking-wide shadow-xs transition-colors",
          style.bg,
          style.text,
          style.border,
          className
        )}
        {...props}
      >
        {tier}
      </span>
      {isUnique && showNewBadge && (
        <span className="inline-flex items-center rounded-full bg-magenta-cta px-1.5 py-0.2 text-[10px] font-extrabold uppercase tracking-wider text-white shadow-xs">
          NOVO
        </span>
      )}
    </span>
  );
}

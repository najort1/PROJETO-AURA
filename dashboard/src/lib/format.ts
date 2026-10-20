/**
 * Shared formatting utilities with module-level cached Intl instances.
 * Eliminates per-render and per-row allocations of Intl.NumberFormat.
 */

const currencyBRLFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const decimalBRLFormatter = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const integerBRLFormatter = new Intl.NumberFormat("pt-BR", {
  maximumFractionDigits: 0,
});

/** Formats a numeric value as Brazilian Real currency (e.g., "R$ 1.234,56") */
export function formatCurrencyBRL(value: number): string {
  return currencyBRLFormatter.format(value);
}

/** Formats a decimal number with pt-BR separators and 2 fraction digits (e.g., "1.234,56") */
export function formatDecimalBRL(value: number): string {
  return decimalBRLFormatter.format(value);
}

/** Formats an integer number with pt-BR separators and 0 fraction digits (e.g., "1.235") */
export function formatIntegerBRL(value: number): string {
  return integerBRLFormatter.format(value);
}

import * as React from "react";
import { Card, CardHeader, CardContent } from "@/components/ui/card";

export default function Cliente360Loading() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Header Skeleton */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border-subtle pb-4">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <div className="h-4 w-16 bg-muted rounded" />
            <div className="h-4 w-28 bg-muted rounded" />
          </div>
          <div className="h-7 w-72 bg-muted rounded" />
          <div className="h-4 w-96 bg-muted/60 rounded" />
        </div>
      </div>

      {/* Card de Busca Rápida / Combobox Skeleton */}
      <Card className="shadow-2xs border-border-subtle">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="h-4 w-48 bg-muted rounded" />
            <div className="h-3 w-32 bg-muted/60 rounded" />
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="h-10 w-full bg-muted/50 rounded-lg" />
          <div className="flex items-center gap-2 pt-1">
            <div className="h-3 w-40 bg-muted/60 rounded" />
            <div className="flex gap-2">
              <div className="h-7 w-24 bg-muted/40 rounded-lg" />
              <div className="h-7 w-24 bg-muted/40 rounded-lg" />
              <div className="h-7 w-24 bg-muted/40 rounded-lg" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Card Principal do Cliente 360 Skeleton */}
      <Card className="border-t-4 border-t-azul-action/40 shadow-xs">
        <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border-subtle pb-4">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <div className="h-8 w-32 bg-muted rounded" />
              <div className="h-6 w-20 bg-muted rounded-full" />
              <div className="h-6 w-28 bg-muted rounded-full" />
            </div>
            <div className="h-4 w-64 bg-muted/60 rounded" />
          </div>

          <div className="flex items-center gap-4 bg-muted/30 p-2.5 rounded-lg border border-border-subtle">
            <div className="space-y-1 text-right">
              <div className="h-3 w-24 bg-muted rounded ml-auto" />
              <div className="h-6 w-28 bg-muted rounded ml-auto" />
            </div>
            <div className="h-8 w-px bg-border-subtle" />
            <div className="space-y-1 text-right">
              <div className="h-3 w-16 bg-muted rounded ml-auto" />
              <div className="h-6 w-16 bg-muted rounded ml-auto" />
            </div>
          </div>
        </CardHeader>

        <CardContent className="pt-6 space-y-6">
          {/* 4 KPIs Grid Skeleton */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {Array.from({ length: 4 }).map((_, idx) => (
              <div
                key={idx}
                className="rounded-lg border border-border-subtle bg-muted/30 p-3 space-y-2"
              >
                <div className="h-3 w-24 bg-muted rounded" />
                <div className="h-6 w-28 bg-muted rounded" />
              </div>
            ))}
          </div>

          {/* Oportunidades & Alavancas CRM Skeleton */}
          <div className="rounded-lg border border-border-subtle bg-surface p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-border-subtle pb-2">
              <div className="h-4 w-56 bg-muted rounded" />
              <div className="h-4 w-24 bg-muted/60 rounded" />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="h-20 bg-muted/30 rounded-md border border-border-subtle/50" />
              <div className="h-20 bg-muted/30 rounded-md border border-border-subtle/50" />
              <div className="h-20 bg-muted/30 rounded-md border border-border-subtle/50" />
            </div>
          </div>

          {/* Gráfico SHAP Waterfall Skeleton */}
          <div className="rounded-lg border border-border-subtle bg-surface p-4 space-y-4">
            <div className="flex items-center justify-between border-b border-border-subtle pb-2">
              <div className="h-4 w-60 bg-muted rounded" />
              <div className="h-4 w-32 bg-muted/60 rounded" />
            </div>
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, idx) => (
                <div key={idx} className="space-y-1.5">
                  <div className="flex justify-between">
                    <div className="h-3 w-40 bg-muted rounded" />
                    <div className="h-3 w-20 bg-muted rounded" />
                  </div>
                  <div className="h-4 w-full bg-muted/30 rounded-full" />
                </div>
              ))}
            </div>
            <div className="h-8 w-full bg-muted/40 rounded-md" />
          </div>

          {/* Linha do Tempo Skeleton */}
          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between border-b border-border-subtle pb-2">
              <div className="h-4 w-52 bg-muted rounded" />
              <div className="h-5 w-44 bg-muted/60 rounded" />
            </div>
            <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-border-subtle">
              {Array.from({ length: 3 }).map((_, idx) => (
                <div key={idx} className="relative space-y-1">
                  <div className="absolute -left-6 top-1 h-4 w-4 rounded-full bg-muted border-2 border-border-subtle" />
                  <div className="rounded-lg border border-border-subtle bg-muted/20 p-3 space-y-2">
                    <div className="flex justify-between">
                      <div className="h-3 w-36 bg-muted rounded" />
                      <div className="h-3 w-20 bg-muted/60 rounded" />
                    </div>
                    <div className="h-3 w-72 bg-muted/40 rounded" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

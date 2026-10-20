import * as React from "react";

export default function DashboardLoading() {
  return (
    <div className="space-y-6 animate-in fade-in-50 duration-200">
      {/* Header Skeleton */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-border-subtle pb-4">
        <div className="space-y-2">
          <div className="h-7 w-64 rounded-md bg-muted/80 animate-pulse" />
          <div className="h-4 w-96 max-w-full rounded-md bg-muted/60 animate-pulse" />
        </div>
        <div className="flex items-center gap-2">
          <div className="h-9 w-28 rounded-md bg-muted/70 animate-pulse" />
          <div className="h-9 w-32 rounded-md bg-muted/70 animate-pulse" />
        </div>
      </div>

      {/* KPI Metric Cards Skeleton (4 cards) */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="rounded-xl border border-border-subtle bg-surface p-5 shadow-xs space-y-3"
          >
            <div className="flex items-center justify-between">
              <div className="h-3.5 w-24 rounded bg-muted/70 animate-pulse" />
              <div className="h-7 w-7 rounded-lg bg-muted/50 animate-pulse" />
            </div>
            <div className="h-8 w-36 rounded bg-muted/80 animate-pulse" />
            <div className="h-3 w-48 max-w-full rounded bg-muted/50 animate-pulse" />
          </div>
        ))}
      </div>

      {/* Main Analytical Section Skeleton */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Primary Chart / Table Card */}
        <div className="rounded-xl border border-border-subtle bg-surface p-6 shadow-xs lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between border-b border-border-subtle pb-3">
            <div className="space-y-1.5">
              <div className="h-5 w-48 rounded bg-muted/80 animate-pulse" />
              <div className="h-3.5 w-64 rounded bg-muted/50 animate-pulse" />
            </div>
            <div className="h-8 w-24 rounded bg-muted/60 animate-pulse" />
          </div>
          <div className="h-64 rounded-lg bg-muted/30 border border-border-subtle/60 flex items-center justify-center">
            <div className="h-32 w-3/4 rounded bg-muted/50 animate-pulse" />
          </div>
        </div>

        {/* Secondary Detail Card */}
        <div className="rounded-xl border border-border-subtle bg-surface p-6 shadow-xs space-y-4">
          <div className="border-b border-border-subtle pb-3 space-y-1.5">
            <div className="h-5 w-36 rounded bg-muted/80 animate-pulse" />
            <div className="h-3.5 w-44 rounded bg-muted/50 animate-pulse" />
          </div>
          <div className="space-y-3 pt-2">
            {[1, 2, 3, 4, 5].map((item) => (
              <div key={item} className="flex items-center justify-between py-1.5 border-b border-border-subtle/40 last:border-0">
                <div className="h-3.5 w-28 rounded bg-muted/60 animate-pulse" />
                <div className="h-4 w-16 rounded bg-muted/70 animate-pulse" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

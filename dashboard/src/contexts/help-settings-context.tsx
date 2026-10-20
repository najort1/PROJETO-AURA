"use client";

import * as React from "react";

interface HelpSettingsContextType {
  showTooltips: boolean;
  toggleTooltips: () => void;
  setShowTooltips: (show: boolean) => void;
}

const HelpSettingsContext = React.createContext<HelpSettingsContextType | undefined>(
  undefined
);

const STORAGE_KEY = "aura_show_help_tooltips";

export function HelpSettingsProvider({ children }: { children: React.ReactNode }) {
  const [showTooltips, setShowTooltipsState] = React.useState<boolean>(true);
  const [isMounted, setIsMounted] = React.useState<boolean>(false);

  React.useEffect(() => {
    setIsMounted(true);
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored !== null) {
        setShowTooltipsState(stored === "true");
      }
    } catch {
      // Silently fall back if localStorage is unavailable
    }
  }, []);

  const setShowTooltips = React.useCallback((show: boolean) => {
    setShowTooltipsState(show);
    try {
      window.localStorage.setItem(STORAGE_KEY, String(show));
    } catch {
      // Silently fall back
    }
  }, []);

  const toggleTooltips = React.useCallback(() => {
    setShowTooltipsState((prev) => {
      const next = !prev;
      try {
        window.localStorage.setItem(STORAGE_KEY, String(next));
      } catch {
        // Silently fall back
      }
      return next;
    });
  }, []);

  const value = React.useMemo(
    () => ({
      showTooltips: isMounted ? showTooltips : true,
      toggleTooltips,
      setShowTooltips,
    }),
    [isMounted, showTooltips, toggleTooltips, setShowTooltips]
  );

  return (
    <HelpSettingsContext.Provider value={value}>
      {children}
    </HelpSettingsContext.Provider>
  );
}

export function useHelpSettings(): HelpSettingsContextType {
  const context = React.useContext(HelpSettingsContext);
  if (!context) {
    throw new Error("useHelpSettings must be used within a HelpSettingsProvider");
  }
  return context;
}

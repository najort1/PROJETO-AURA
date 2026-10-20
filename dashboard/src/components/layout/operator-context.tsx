"use client";

import * as React from "react";

export interface OperatorProfile {
  id: string;
  name: string;
  role: string;
  avatarColor: string;
}

export interface OperatorContextValue {
  currentProfile: OperatorProfile;
  setProfile: (profile: OperatorProfile) => void;
  availableProfiles: OperatorProfile[];
}

export const OPERATOR_PROFILES: OperatorProfile[] = [
  {
    id: "operador_crm",
    name: "Carolina Silva",
    role: "Analista de Retenção CRM (HITL)",
    avatarColor: "bg-azul-action",
  },
  {
    id: "lideranca_fidelidade",
    name: "Rodrigo Mendes",
    role: "Diretoria de Fidelidade & Parcerias",
    avatarColor: "bg-azul-deep",
  },
  {
    id: "gerente_contas",
    name: "Mariana Alencar",
    role: "Gerente de Contas Diamante Unique",
    avatarColor: "bg-magenta-cta",
  },
  {
    id: "auditor_lgpd",
    name: "Fernando Bastos",
    role: "Auditor de Ética Algorítmica & LGPD",
    avatarColor: "bg-emerald-600",
  },
];

const STORAGE_KEY = "aura_operator_profile_id";

export const OperatorContext = React.createContext<OperatorContextValue | undefined>(undefined);

export function OperatorProvider({ children }: { children: React.ReactNode }): React.JSX.Element {
  const [currentProfile, setCurrentProfile] = React.useState<OperatorProfile>(OPERATOR_PROFILES[0]);

  // Carregar perfil salvo no localStorage após montagem
  React.useEffect(() => {
    try {
      const savedId = localStorage.getItem(STORAGE_KEY);
      if (savedId) {
        const found = OPERATOR_PROFILES.find((p) => p.id === savedId);
        if (found) {
          setCurrentProfile(found);
        }
      }
    } catch {
      // Ignorar erros de acesso a localStorage
    }
  }, []);

  const setProfile = React.useCallback((profile: OperatorProfile) => {
    setCurrentProfile(profile);
    try {
      localStorage.setItem(STORAGE_KEY, profile.id);
    } catch {
      // Ignorar erros de gravação em localStorage
    }
  }, []);

  const value = React.useMemo<OperatorContextValue>(
    () => ({
      currentProfile,
      setProfile,
      availableProfiles: OPERATOR_PROFILES,
    }),
    [currentProfile, setProfile]
  );

  return <OperatorContext.Provider value={value}>{children}</OperatorContext.Provider>;
}

export function useOperator(): OperatorContextValue {
  const context = React.useContext(OperatorContext);
  if (!context) {
    throw new Error("useOperator must be used within an OperatorProvider");
  }
  return context;
}

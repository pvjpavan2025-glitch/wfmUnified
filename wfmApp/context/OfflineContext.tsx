"use client";
import React, { createContext, useContext, useState, useCallback } from 'react';

export interface OfflineContextState {
  backendOnline: boolean;
  offlineModeActive: boolean;
  pendingSyncCount: number;
  lastSyncAttempt: number | null;
  triggerSync?: () => Promise<void> | void;
  setBackendOnline?: (v: boolean) => void;
  setOfflineModeActive?: (v: boolean) => void;
  setPendingSyncCount?: (n: number) => void;
  setLastSyncAttempt?: (ts: number | null) => void;
}

const OfflineContext = createContext<OfflineContextState>({
  backendOnline: true,
  offlineModeActive: false,
  pendingSyncCount: 0,
  lastSyncAttempt: null,
});

export const OfflineProvider: React.FC<React.PropsWithChildren<{}>> = ({ children }) => {
  const [backendOnline, setBackendOnline] = useState(true);
  const [offlineModeActive, setOfflineModeActive] = useState(false);
  const [pendingSyncCount, setPendingSyncCount] = useState(0);
  const [lastSyncAttempt, setLastSyncAttempt] = useState<number | null>(null);

  const value: OfflineContextState = {
    backendOnline,
    offlineModeActive,
    pendingSyncCount,
    lastSyncAttempt,
    setBackendOnline,
    setOfflineModeActive,
    setPendingSyncCount,
    setLastSyncAttempt,
  };
  return <OfflineContext.Provider value={value}>{children}</OfflineContext.Provider>;
};

export const useOfflineContext = () => useContext(OfflineContext);

// Optional helper HOC
export const withOfflineProvider = (Component: React.ComponentType<any>) => (props: any) => (
  <OfflineProvider>
    <Component {...props} />
  </OfflineProvider>
);

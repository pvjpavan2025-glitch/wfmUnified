"use client";
import React from 'react';
import { useOfflineContext } from '@/context/OfflineContext';

export const OfflineBadge: React.FC = () => {
  const ctx = (() => { try { return useOfflineContext(); } catch { return null; } })();
  if (!ctx) return null;
  const { backendOnline, offlineModeActive, pendingSyncCount } = ctx;
  const offline = !backendOnline || offlineModeActive;
  if (!offline && pendingSyncCount === 0) return null;
  return (
    <div className="fixed top-2 left-1/2 -translate-x-1/2 z-50 flex items-center space-x-2">
      {offline && (
        <span className="px-3 py-1 rounded-md text-xs font-medium bg-red-100 text-red-700 border border-red-300 shadow-sm">
          Offline Mode
        </span>
      )}
      {pendingSyncCount > 0 && (
        <span className="px-3 py-1 rounded-md text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-300 shadow-sm" title="Diagrams queued for sync">
          Queue: {pendingSyncCount}
        </span>
      )}
    </div>
  );
};

export default OfflineBadge;

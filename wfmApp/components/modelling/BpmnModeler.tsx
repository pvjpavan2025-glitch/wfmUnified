import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useOfflineContext } from '@/context/OfflineContext';
import { processApiService } from '@/services/processApi';
import { workflowApiService } from '@/services/workflowApi';
import BpmnModeler from 'bpmn-js/lib/Modeler';
import {
  BpmnPropertiesPanelModule,
  BpmnPropertiesProviderModule,
  CamundaPlatformPropertiesProviderModule
} from 'bpmn-js-properties-panel';
import ColorPickerModule from 'bpmn-js-color-picker';
import camundaModdleDescriptor from 'camunda-bpmn-moddle/resources/camunda.json';
import MinimapModule from 'diagram-js-minimap';
import { useBpmnModelerSafe } from '@/hooks/useBpmnModelerSafe';
import type { BpmnElement } from '@/types/global';

import 'bpmn-js/dist/assets/diagram-js.css';
import 'bpmn-js/dist/assets/bpmn-font/css/bpmn.css';
import '@bpmn-io/properties-panel/assets/properties-panel.css';
import 'diagram-js-minimap/assets/diagram-js-minimap.css';
import './BpmnModeler.css';

interface BpmnModelerProps {
  onSave?: (xml: string) => void;
  onClose?: () => void;
  autoCreateDiagram?: boolean; // Auto-create diagram when requested
  initialXml?: string;
  onDirtyChange: (isDirty: boolean) => void;
  isDirty: boolean;
}

// Import behavior env flags (build-time via Next.js)
// If true, skip the direct browser fetch and go straight to proxy (useful when CORS or local ports are blocked)
const IMPORT_PROXY_ONLY = process.env.NEXT_PUBLIC_IMPORT_PROXY_ONLY === 'true';
// If true, try proxy first then fallback to direct (inverse of default order)
const IMPORT_PROXY_FIRST = process.env.NEXT_PUBLIC_IMPORT_PROXY_FIRST === 'true';
// Optional custom proxy route (defaults to /api/proxy-bpmn)
const IMPORT_PROXY_ROUTE = process.env.NEXT_PUBLIC_IMPORT_PROXY_ROUTE || '/api/proxy-bpmn';

const BpmnModelerComponent: React.FC<BpmnModelerProps> = ({ 
  onSave, 
  onClose, 
  autoCreateDiagram, 
  initialXml, 
  onDirtyChange, 
  isDirty 
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const propertiesPanelRef = useRef<HTMLDivElement>(null);
  const minimapRef = useRef<HTMLDivElement>(null); // Add minimap container ref
  const modelerRef = useRef<BpmnModeler | null>(null);
  const [xml, setXml] = useState<string>(initialXml || '');
  const [error, setError] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [selectedElement, setSelectedElement] = useState<any>(null);
  const [executionStatus, setExecutionStatus] = useState<string>('');
  const [showTransactionBoundaries, setShowTransactionBoundaries] = useState<boolean>(false);
  const [showMinimap, setShowMinimap] = useState<boolean>(true); // Add minimap visibility state
  const [showImportDialog, setShowImportDialog] = useState<boolean>(false);
  const [importUrl, setImportUrl] = useState<string>('');
  const [isImporting, setIsImporting] = useState<boolean>(false);
  const [importMethod, setImportMethod] = useState<'url' | 'file'>('url');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [toast, setToast] = useState<{message: string, type: 'success' | 'error' | 'info'} | null>(null);
  const [conflictModal, setConflictModal] = useState<null | { local: any; remote: any; onResolve: (action: 'overwrite' | 'skip' | 'merge' | 'rename', opts?: { newFilename?: string }) => void }>(null);
  const [diffPreview, setDiffPreview] = useState<{
    added: number;
    removed: number;
    changed: number;
    summary: string;
    localOnly?: number;
    remoteOnly?: number;
    assigneeFilledCount?: number;
    candidateGroupsFilledCount?: number;
    candidateUsersFilledCount?: number;
    dueDateFilledCount?: number;
    extensionsImportedCount?: number;
  } | null>(null);
  const [isManualImport, setIsManualImport] = useState(false);
  const manualImportRef = useRef(false);
  // Offline + sync state (added)
  const offlineCtx = (() => { try { return useOfflineContext(); } catch { return null; } })();
  const [backendOnline, setBackendOnline] = useState<boolean>(offlineCtx?.backendOnline ?? true);
  const [pendingSyncs, setPendingSyncs] = useState<PendingSyncItem[]>([]);
  const [lastSyncAttempt, setLastSyncAttempt] = useState<number | null>(null);
  const retryIntervalRef = useRef<NodeJS.Timeout | null>(null);
  // Forward declarations for sync logic (defined after function bodies for clarity)
  const attemptSyncRef = useRef<() => Promise<void>>(async () => {});
  const handleManualSync = useCallback(async () => {
    if (attemptSyncRef.current) {
      await attemptSyncRef.current();
      if (pendingSyncs.length === 0 && backendOnline) {
        setToast({ message: 'All pending diagrams synced', type: 'success' });
      } else if (!backendOnline) {
        setToast({ message: 'Backend still offline', type: 'info' });
      } else {
        setToast({ message: 'Some diagrams still pending', type: 'info' });
      }
    }
  }, [pendingSyncs, backendOnline]);

  // Temporary BPMN storage control flags
  const TEMP_STORE_DISABLED = process.env.NEXT_PUBLIC_DISABLE_TEMP_STORE === 'true';
  const tempStoreFailureRef = useRef<number>(0); // count consecutive failures
  const TEMP_STORE_FAILURE_SILENCE_AFTER = 1; // after first shown failure, silence subsequent ones
  const initialOffline = process.env.NEXT_PUBLIC_BPMN_OFFLINE_MODE === 'true';
  const [offlineModeActive, setOfflineModeActive] = useState<boolean>(offlineCtx?.offlineModeActive ?? initialOffline);
  // Queue config / feature flags
  const QUEUE_MAX_SIZE = parseInt(process.env.NEXT_PUBLIC_QUEUE_MAX_SIZE || '20', 10);
  const QUEUE_COMPRESSION = process.env.NEXT_PUBLIC_QUEUE_COMPRESSION === 'true';
  const QUEUE_ENCRYPTION = process.env.NEXT_PUBLIC_QUEUE_ENCRYPTION === 'true';
  const QUEUE_STORAGE_KEY_V1 = 'bpmn_pending_syncs';
  const QUEUE_STORAGE_KEY_V2 = 'bpmn_pending_syncs_v2';

  interface PendingSyncMeta {
    compressed?: boolean;
    encrypted?: boolean;
    algo?: string; // compression algo
    iv?: string;   // base64 IV for encryption
    hash?: string; // sha256 of original xml
    version?: number; // schema version
  }

  type PendingSyncItem = { key: string; filename: string; xml: string; created: number; meta?: PendingSyncMeta };

  // Utility: base64 helpers
  const toBase64 = (bytes: Uint8Array) => (typeof window === 'undefined') ? '' : window.btoa(String.fromCharCode(...bytes));
  const fromBase64 = (b64: string) => {
    if (typeof window === 'undefined') return new Uint8Array();
    const bin = window.atob(b64);
    const arr = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
    return arr;
  };

  // Utility: compute SHA-256 hash (hex)
  const sha256 = async (data: string): Promise<string> => {
    if (typeof window === 'undefined' || !window.crypto?.subtle) return '';
    const enc = new TextEncoder().encode(data);
    const digest = await window.crypto.subtle.digest('SHA-256', enc);
    return Array.from(new Uint8Array(digest)).map(b => b.toString(16).padStart(2, '0')).join('');
  };

  // Encryption: server-assisted key (fallback to local if server unavailable)
  const ensureEncryptionKey = async (): Promise<CryptoKey | null> => {
    if (!QUEUE_ENCRYPTION) return null;
    if (typeof window === 'undefined' || !window.crypto?.subtle) return null;
    const stored = localStorage.getItem('bpmn_queue_enc_key_v2_server');
    if (stored) {
      try {
        const jwk = JSON.parse(stored);
        return await window.crypto.subtle.importKey('jwk', jwk, { name: 'AES-GCM' }, false, ['encrypt', 'decrypt']);
      } catch { /* ignore */ }
    }
    // Try server endpoint
    try {
      const resp = await fetch('/api/security/encryption-key');
      if (resp.ok) {
        const data = await resp.json();
        if (data?.key) {
          localStorage.setItem('bpmn_queue_enc_key_v2_server', JSON.stringify(data.key));
          return await window.crypto.subtle.importKey('jwk', data.key, { name: 'AES-GCM' }, false, ['encrypt', 'decrypt']);
        }
      }
    } catch { /* ignore */ }
    // Fallback generate local if server failed
    try {
      const key = await window.crypto.subtle.generateKey({ name: 'AES-GCM', length: 256 }, true, ['encrypt', 'decrypt']);
      const jwk = await window.crypto.subtle.exportKey('jwk', key);
      localStorage.setItem('bpmn_queue_enc_key_v2_server', JSON.stringify(jwk));
      return key;
    } catch { return null; }
  };
  // --- Semantic BPMN Parsing & Merge ---
  interface SemanticEl { id: string; type: string; name?: string; documentation?: string; assignee?: string; candidateGroups?: string; candidateUsers?: string; dueDate?: string; extensionsHash?: string; raw: Element; }
  const hashExtensions = (el: Element): string | undefined => {
    const ext = Array.from(el.getElementsByTagName('bpmn:extensionElements'))[0];
    if (!ext) return undefined;
    // Simple hash via JSON of child tag names+attributes
    const payload: any[] = [];
    Array.from(ext.children).forEach(c => {
      const attrs: Record<string,string> = {};
      Array.from(c.attributes).forEach(a => attrs[a.name] = a.value);
      payload.push({ tag: c.tagName, attrs });
    });
    try { return btoa(unescape(encodeURIComponent(JSON.stringify(payload)))); } catch { return undefined; }
  };

  const parseSemantic = (xml: string): Map<string, SemanticEl> => {
    const map = new Map<string, SemanticEl>();
    try {
      const doc = new DOMParser().parseFromString(xml, 'application/xml');
      if (doc.getElementsByTagName('parsererror').length) return map;
      const collect = (el: Element) => {
        const id = el.getAttribute('id');
        if (id) {
          const name = el.getAttribute('name') || undefined;
          // documentation child
          let documentation: string | undefined;
          const docs = el.getElementsByTagName('bpmn:documentation');
            if (docs && docs.length) documentation = docs[0].textContent || undefined;
          // camunda:assignee attribute
          const assignee = el.getAttribute('camunda:assignee') || undefined;
          const candidateGroups = el.getAttribute('camunda:candidateGroups') || undefined;
          const candidateUsers = el.getAttribute('camunda:candidateUsers') || undefined;
          const dueDate = el.getAttribute('camunda:dueDate') || undefined;
          const extensionsHash = hashExtensions(el);
          map.set(id, { id, type: el.tagName, name, documentation, assignee, candidateGroups, candidateUsers, dueDate, extensionsHash, raw: el });
        }
        Array.from(el.children).forEach(c => collect(c as Element));
      };
      collect(doc.documentElement);
    } catch { /* ignore */ }
    return map;
  };

  const semanticMerge = (localXml: string, remoteXml: string): { merged: string; diffMeta: any } => {
    try {
      const parser = new DOMParser();
      const localDoc = parser.parseFromString(localXml, 'application/xml');
      const remoteDoc = parser.parseFromString(remoteXml, 'application/xml');
      if (localDoc.getElementsByTagName('parsererror').length) return { merged: localXml, diffMeta: {} };
      if (remoteDoc.getElementsByTagName('parsererror').length) return { merged: localXml, diffMeta: {} };
      const lMap = parseSemantic(localXml); const rMap = parseSemantic(remoteXml);
      const defs = localDoc.documentElement;
  const added: string[] = []; const modified: string[] = []; const remoteOnly: string[] = []; const assigneeFilled: string[] = []; const extensionsImported: string[] = []; const candidateGroupsFilled: string[] = []; const candidateUsersFilled: string[] = []; const dueDateFilled: string[] = [];
      // Merge remote-only
      rMap.forEach((val, id) => { if (!lMap.has(id)) { try { defs.appendChild(localDoc.importNode(val.raw, true)); added.push(id); } catch {} } });
      // Reconcile properties for overlapping
      lMap.forEach((lVal, id) => {
        const rVal = rMap.get(id);
        if (!rVal) return;
        let changed = false;
        if (rVal.name && rVal.name !== lVal.name) {
          if (!lVal.name) { lVal.raw.setAttribute('name', rVal.name); changed = true; }
        }
        if (rVal.documentation && !lVal.documentation) {
            const docEl = localDoc.createElement('bpmn:documentation');
            docEl.textContent = rVal.documentation;
            lVal.raw.appendChild(docEl); changed = true;
        }
  if (rVal.assignee && !lVal.assignee) { lVal.raw.setAttribute('camunda:assignee', rVal.assignee); changed = true; assigneeFilled.push(id); }
  if (rVal.candidateGroups && !lVal.candidateGroups) { lVal.raw.setAttribute('camunda:candidateGroups', rVal.candidateGroups); changed = true; candidateGroupsFilled.push(id); }
  if (rVal.candidateUsers && !lVal.candidateUsers) { lVal.raw.setAttribute('camunda:candidateUsers', rVal.candidateUsers); changed = true; candidateUsersFilled.push(id); }
  if (rVal.dueDate && !lVal.dueDate) { lVal.raw.setAttribute('camunda:dueDate', rVal.dueDate); changed = true; dueDateFilled.push(id); }
        if (rVal.extensionsHash && rVal.extensionsHash !== lVal.extensionsHash) {
          // Bring over extensionElements if local missing
          const hasLocalExt = lVal.raw.getElementsByTagName('bpmn:extensionElements').length > 0;
          if (!hasLocalExt) {
            const remoteExt = rVal.raw.getElementsByTagName('bpmn:extensionElements')[0];
            if (remoteExt) {
              lVal.raw.appendChild(localDoc.importNode(remoteExt, true));
              changed = true; extensionsImported.push(id);
            }
          }
        }
        if (changed) modified.push(id);
      });
      // Track remote-only for diff meta
      rMap.forEach((v, id) => { if (!lMap.has(id)) remoteOnly.push(id); });
      const merged = new XMLSerializer().serializeToString(localDoc);
  return { merged, diffMeta: { added, modified, remoteOnly, assigneeFilled, extensionsImported, candidateGroupsFilled, candidateUsersFilled, dueDateFilled } };
    } catch { return { merged: localXml, diffMeta: {} }; }
  };

  // Visual overlays for diff
  const applyDiffOverlays = (modeler: BpmnModeler, diff: { added?: string[]; modified?: string[]; remoteOnly?: string[] }) => {
    try {
      const overlays = (modeler as any).get('overlays');
      const elementRegistry = modeler.get('elementRegistry');
      const addBadge = (id: string, color: string, title: string) => {
        const el = elementRegistry.get(id); if (!el) return;
        overlays.add(id, {
          position: { bottom: 0, right: 0 },
          html: `<div style="background:${color};color:#fff;padding:2px 4px;border-radius:3px;font-size:9px;opacity:0.85" title="${title}">${title[0]}</div>`
        });
      };
      diff.added?.forEach(id => addBadge(id, '#16a34a', 'Added'));
      diff.modified?.forEach(id => addBadge(id, '#d97706', 'Changed'));
      diff.remoteOnly?.forEach(id => addBadge(id, '#dc2626', 'Remote')); // remote only (not in local before merge)
    } catch { /* ignore */ }
  };

  const clearDiffOverlays = (modeler: BpmnModeler) => {
    try { const overlays = (modeler as any).get('overlays'); overlays.clear(); } catch { /* ignore */ }
  };

  // Audit logging helper
  const logConflictAction = async (data: { filename: string; action: string; diff?: any }) => {
    const sessionId = sessionStorage.getItem('sessionId') || 'session';
    try {
      fetch('/api/audit/conflicts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...data, sessionId })
      }).catch(()=>{});
      // Local copy (append)
      const localKey = 'bpmn_conflict_audit_v1';
      const existing = JSON.parse(localStorage.getItem(localKey) || '[]');
      existing.push({ ts: Date.now(), ...data });
      if (existing.length > 300) existing.splice(0, existing.length - 300);
      localStorage.setItem(localKey, JSON.stringify(existing));
    } catch { /* ignore */ }
  };

  const encryptString = async (plain: string): Promise<{ b64: string; iv: string } | null> => {
    if (!QUEUE_ENCRYPTION) return null;
    const key = await ensureEncryptionKey();
    if (!key) return null;
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const enc = new TextEncoder().encode(plain);
    const ct = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, enc);
    return { b64: toBase64(new Uint8Array(ct)), iv: toBase64(iv) };
  };

  const decryptString = async (payloadB64: string, ivB64: string): Promise<string> => {
    const key = await ensureEncryptionKey();
    if (!key) return '';
    const iv = fromBase64(ivB64);
    const data = fromBase64(payloadB64);
    const pt = await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, key, data);
    return new TextDecoder().decode(pt);
  };

  // Compression helpers (CompressionStream API only; graceful fallback)
  const compressIfNeeded = async (text: string): Promise<{ encoded: string; algo?: string; compressed: boolean }> => {
    if (!QUEUE_COMPRESSION) return { encoded: text, compressed: false };
    try {
      if (typeof CompressionStream === 'undefined') return { encoded: text, compressed: false };
      const cs = new CompressionStream('gzip');
      const writer = (cs.writable as any).getWriter();
      await writer.write(new TextEncoder().encode(text));
      await writer.close();
      const compressed = await new Response(cs.readable).arrayBuffer();
      return { encoded: toBase64(new Uint8Array(compressed)), algo: 'gzip', compressed: true };
    } catch {
      return { encoded: text, compressed: false };
    }
  };

  const decompressIfNeeded = async (payload: PendingSyncItem): Promise<string> => {
    const meta = payload.meta;
    if (!meta?.compressed) return payload.xml; // xml field stores raw or encoded depending on compressed flag
    try {
      if (typeof DecompressionStream === 'undefined') return payload.xml; // can't decompress
      const bin = fromBase64(payload.xml);
  const ds = new DecompressionStream((meta.algo as CompressionFormat) || 'gzip');
      const writer = (ds.writable as any).getWriter();
      await writer.write(bin);
      await writer.close();
      const buf = await new Response(ds.readable).arrayBuffer();
      return new TextDecoder().decode(buf);
    } catch {
      return payload.xml; // fallback
    }
  };

  // Load persisted queue (upgrade v1 to v2)
  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      const v2 = localStorage.getItem(QUEUE_STORAGE_KEY_V2);
      if (v2) {
        const parsed: PendingSyncItem[] = JSON.parse(v2);
        setPendingSyncs(parsed as any);
        return;
      }
      const legacy = localStorage.getItem(QUEUE_STORAGE_KEY_V1);
      if (legacy) {
        const parsed: any[] = JSON.parse(legacy);
        const upgraded: PendingSyncItem[] = parsed.map(it => ({ ...it, meta: { version: 1 } }));
        setPendingSyncs(upgraded as any);
        localStorage.setItem(QUEUE_STORAGE_KEY_V2, JSON.stringify(upgraded));
      }
    } catch { /* ignore */ }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Persist queue v2
  useEffect(() => {
    if (typeof window === 'undefined') return;
    try { localStorage.setItem(QUEUE_STORAGE_KEY_V2, JSON.stringify(pendingSyncs)); } catch { /* ignore */ }
    offlineCtx?.setPendingSyncCount?.(pendingSyncs.length);
  }, [pendingSyncs]);

  // Mirror state to context
  useEffect(() => { offlineCtx?.setBackendOnline?.(backendOnline); }, [backendOnline, offlineCtx]);
  useEffect(() => { offlineCtx?.setOfflineModeActive?.(offlineModeActive); }, [offlineModeActive, offlineCtx]);

  const [queueCollapsed, setQueueCollapsed] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    try { return localStorage.getItem('bpmn_queue_collapsed') === '1'; } catch { return false; }
  });

  // Ensure camunda namespace is present so Camunda properties provider activates element groups
  const ensureCamundaNamespace = useCallback((rawXml: string | undefined | null): string => {
    if (!rawXml) return '';
    if (/xmlns:camunda="http:\/\/camunda.org\/schema\/1.0\/bpmn"/.test(rawXml)) return rawXml;
    return rawXml.replace(/<bpmn:definitions([^>]*)>/, (match, attrs) => {
      if (/xmlns:camunda=/.test(attrs)) return match; // already injected inside tag
      return `<bpmn:definitions${attrs} xmlns:camunda="http://camunda.org/schema/1.0/bpmn">`;
    });
  }, []);

  // Use the safe BPMN modeler hook
  const {
    initializeModelerSafely,
    importXmlSafely,
    createDiagramSafely,
    isModelerReady,
    zoomSafely,
    saveXmlSafely
  } = useBpmnModelerSafe();




  useEffect(() => {
    if (!containerRef.current || !propertiesPanelRef.current) return;

  let newModeler: BpmnModeler | null = null;
  let _resizeObserver: ResizeObserver | null = null;

    const initializeModeler = async () => {
      // Wait for the container to have a computed size. This avoids initializing
      // bpmn-js while the canvas has 0x0 size (common with flex layouts / HMR),
      // which can cause the renderer/palette to compute positions incorrectly.
      const waitForContainerLayout = (el: HTMLElement, timeout = 3000) => {
        return new Promise<void>((resolve) => {
          try {
            const rect = el.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0) return resolve();

            const ro = new ResizeObserver(() => {
              const r = el.getBoundingClientRect();
              if (r.width > 0 && r.height > 0) {
                ro.disconnect();
                resolve();
              }
            });

            ro.observe(el);

            // Fallback: resolve after timeout even if size didn't change to avoid
            // hanging initialization in edge cases.
            setTimeout(() => {
              try { ro.disconnect(); } catch (e) { /* noop */ }
              resolve();
            }, timeout);
          } catch (e) {
            // If anything goes wrong, don't block initialization.
            resolve();
          }
        });
      };

      // Await a stable container size before continuing.
      if (containerRef.current) {
        await waitForContainerLayout(containerRef.current, 2500);
      }
      try {
        // Global pre-cleanup: if another modeler was left running, destroy it
        try {
          const existing = (window as any).__wfm_bpmn_modeler_active as BpmnModeler | undefined;
          if (existing && typeof existing.destroy === 'function') {
            try { existing.destroy(); } catch (e) { console.warn('Error destroying existing global modeler', e); }
            delete (window as any).__wfm_bpmn_modeler_active;
          }
        } catch (e) {
          console.warn('⚠️ Global pre-cleanup check failed:', e);
        }

        // Remove any dangling diagram DOM nodes not belonging to our containers
        try {
          // Clear the properties panel first to prevent duplicates
          if (propertiesPanelRef.current) {
            propertiesPanelRef.current.innerHTML = '';
          }
          
          const selectors = ['.djs-container', '.bpmn-js', '.diagram-js', '.djs-minimap', '.bpmn-js-minimap', '.bio-properties-panel'];
          selectors.forEach(sel => {
            document.querySelectorAll(sel).forEach((el) => {
              if (!containerRef.current?.contains(el) && !propertiesPanelRef.current?.contains(el) && !minimapRef.current?.contains(el)) {
                // Only remove if element is outside our intended containers
                (el as HTMLElement).remove();
              }
            });
          });
        } catch (e) {
          console.warn('⚠️ Dangling DOM cleanup failed:', e);
        }
        // Initialize modeler safely using the hook
        newModeler = await initializeModelerSafely(
          containerRef.current!,
          propertiesPanelRef.current!,
          showMinimap ? minimapRef.current : null, // Pass minimap container only if visible
          [
            BpmnPropertiesPanelModule,
            BpmnPropertiesProviderModule,
            CamundaPlatformPropertiesProviderModule,
            ColorPickerModule,
            ...(showMinimap ? [MinimapModule] : []) // Include MinimapModule only if minimap is shown
          ],
          {
            camunda: camundaModdleDescriptor
          },
          !!initialXml // Skip initial diagram creation if we have XML to import
        );

        if (!newModeler) {
          throw new Error('Failed to create modeler instance');
        }

  // Record active modeler globally so other instances can detect and cleanup
  try { (window as any).__wfm_bpmn_modeler_active = newModeler; } catch (e) { /* ignore */ }

        // Set up event listeners AFTER canvas is ready
        const eventBus = newModeler.get('eventBus') as any;

        // Instrument selection service to trace who calls select() - debug only
        try {
          const selectionService = newModeler.get('selection');
          if (selectionService && !selectionService.__wrappedForDebug) {
            const origSelect = selectionService.select.bind(selectionService);
            selectionService.select = function(...args: any[]) {
              try {
                const arg = args && args[0];
                const id = Array.isArray(arg) ? (arg[0]?.id) : (arg?.id || arg);

                console.log('🔔 selection.select called with:', {
                  args: args,
                  id: id,
                  currentSelection: selectionService.get ? selectionService.get().map((el: any) => ({ id: el.id, type: el.type })) : 'no get method'
                });

                // Prevent clearing selection if current selection contains a task
                if (!arg || (Array.isArray(arg) && arg.length === 0)) {
                  const currentSelection = selectionService.get && selectionService.get();
                  if (currentSelection && currentSelection.length > 0) {
                    const primary = currentSelection[0];
                    if (primary && primary.businessObject &&
                        (primary.businessObject.$type === 'bpmn:UserTask' ||
                         primary.businessObject.$type === 'bpmn:ServiceTask' ||
                         primary.businessObject.$type === 'bpmn:BusinessRuleTask' ||
                         primary.businessObject.$type === 'bpmn:ReceiveTask' ||
                         primary.businessObject.$type === 'bpmn:SendTask' ||
                         primary.businessObject.$type === 'bpmn:ManualTask' ||
                         primary.businessObject.$type === 'bpmn:ScriptTask')) {
                      console.log('🛡️ BLOCKING selection clear - task currently selected:', {
                        taskId: primary.id,
                        taskType: primary.businessObject.$type,
                        taskName: primary.businessObject.name
                      });
                      return; // Don't clear selection
                    }
                  }
                }

                console.log('✅ Allowing selection change');
              } catch (e) {
                console.warn('🔔 selection.select logging failed', e);
              }
              return origSelect(...args);
            };
            (selectionService as any).__wrappedForDebug = true;
          }
        } catch (e) {
          console.warn('⚠️ Could not wrap selection service for debug', e);
        }
        
        // Create a debounced function to prevent excessive events
        let dirtyChangeTimeout: NodeJS.Timeout | null = null;
        const debouncedDirtyChange = () => {
          if (dirtyChangeTimeout) {
            clearTimeout(dirtyChangeTimeout);
          }
          dirtyChangeTimeout = setTimeout(() => {
            console.log('🔄 Debounced dirty change');
            onDirtyChange(true);
          }, 150); // 150ms debounce
        };        // Listen for element selection changes
        eventBus.on('selection.changed', (event: any) => {
          const { newSelection } = event;
          console.log('🎯 selection.changed event fired:', {
            newSelectionCount: newSelection?.length || 0,
            newSelection: newSelection?.map((el: any) => ({
              id: el.id,
              type: el.type,
              businessObjectType: el.businessObject?.$type,
              name: el.businessObject?.name
            })) || []
          });
          try {
            if (newSelection && newSelection.length > 0) {
              const primary = newSelection[0];
              setSelectedElement(primary);
              // Ensure the properties panel remains attached to our container and refreshes
              try {
                if (newModeler) {
                  const propertiesPanelSvc = newModeler.get('propertiesPanel');
                  if (propertiesPanelSvc && propertiesPanelRef.current) {
                    propertiesPanelSvc.attachTo(propertiesPanelRef.current);
                  }
                }
              } catch (e) { /* noop */ }
            } else {
              setSelectedElement(null);
            }
          } catch (e) {
            console.warn('⚠️ selection.changed handler error:', e);
          }
        });        // Primary change detection - command stack is the most reliable
        eventBus.on('commandStack.changed', () => {
          debouncedDirtyChange();
        });

        // Backup change detection for edge cases  
        eventBus.on('elements.changed', () => {
          debouncedDirtyChange();
        });

        console.log('✅ Event listeners attached successfully');

        // Set the modeler ref
        modelerRef.current = newModeler;
        console.log('✅ Modeler ref set successfully');
        // Ensure the viewport fits the canvas after initialization
        try {
          await zoomSafely(newModeler, 'fit-viewport');
        } catch (e) {
          // best-effort only
          console.debug('Could not fit viewport immediately after init', e);
        }
        // Refit viewport when container resizes (debounced)
        try {
          if (containerRef.current) {
            let raf = 0;
            _resizeObserver = new ResizeObserver(() => {
              if (raf) cancelAnimationFrame(raf);
              raf = requestAnimationFrame(() => {
                try { zoomSafely(newModeler!, 'fit-viewport'); } catch (e) { /* noop */ }
              });
            });
            _resizeObserver.observe(containerRef.current);
          }
        } catch (e) {
          console.debug('ResizeObserver setup failed', e);
        }
        
        // Handle initial content based on props
        if (initialXml) {
          console.log('📄 Loading initial XML...');
          const xmlWithNs = ensureCamundaNamespace(initialXml);
          await importXmlSafely(newModeler, xmlWithNs, 'initial-load');
          onDirtyChange(false);
        } else if (autoCreateDiagram) {
          console.log('🆕 Auto-creating new diagram...');
          const newXml = await createDiagramSafely(newModeler);
          setXml(newXml);
          onDirtyChange(false);
        }

        setError('');
        console.log('🎉 BPMN modeler initialization completed successfully');

        // Check for URL parameter for auto-import (with longer delay for safety)
        const urlParams = new URLSearchParams(window.location.search);
        const autoImportUrl = urlParams.get('url');
        if (autoImportUrl) {
          setImportUrl(decodeURIComponent(autoImportUrl));
          console.log('🔗 Auto-import URL detected, scheduling import...');
          setTimeout(() => {
            handleAutoImport(decodeURIComponent(autoImportUrl), newModeler!);
          }, 3000); // Longer delay for auto-import safety
        }

      } catch (err) {
        console.error('💥 BPMN modeler initialization failed:', err);
        setError(`Initialization failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
      } finally {
        setIsLoading(false);
      }
    };

    initializeModeler();

    return () => {
      // Destroy the modeler instance and clean up any leftover DOM
      try {
        if (newModeler && typeof newModeler.destroy === 'function') {
          try { newModeler.destroy(); } catch (destroyErr) { console.warn('⚠️ Error during modeler cleanup:', destroyErr); }
        }
      } catch (e) {
        console.warn('⚠️ Error while cleaning local modeler:', e);
      }

      // Disconnect resize observer if we created one
      try {
        if (_resizeObserver) {
          try { _resizeObserver.disconnect(); } catch (e) { /* noop */ }
          _resizeObserver = null;
        }
      } catch (e) {
        console.warn('⚠️ Error disconnecting resize observer:', e);
      }

      // Clear global pointer if it points to this modeler
      try {
        if ((window as any).__wfm_bpmn_modeler_active === newModeler) {
          delete (window as any).__wfm_bpmn_modeler_active;
        }
      } catch (e) {
        console.warn('⚠️ Could not clear global modeler ref:', e);
      }

      // Remove any dangling diagram-related DOM nodes outside our containers
      try {
        const selectors = ['.djs-container', '.bpmn-js', '.diagram-js', '.djs-minimap', '.bpmn-js-minimap'];
        selectors.forEach(sel => {
          document.querySelectorAll(sel).forEach((el) => {
            if (!containerRef.current?.contains(el) && !propertiesPanelRef.current?.contains(el) && !minimapRef.current?.contains(el)) {
              (el as HTMLElement).remove();
            }
          });
        });
      } catch (e) {
        console.warn('⚠️ Error removing dangling DOM on cleanup:', e);
      }
    };
  }, [initializeModelerSafely, importXmlSafely, createDiagramSafely, autoCreateDiagram, initialXml, onDirtyChange, showMinimap]);

  // Add debug helper as soon as component mounts
  useEffect(() => {
    if (typeof window !== 'undefined') {
      (window as any).__debug_check = () => {
        const modeler = modelerRef.current;
        if (!modeler) {
          console.log('❌ No modeler available');
          return;
        }

        try {
          const elementRegistry = modeler.get('elementRegistry');
          const canvas = modeler.get('canvas');
          const elements = elementRegistry.getAll();

          console.log('🔍 BPMN Debug Check:');
          console.log('📊 Elements in registry:', elements.length);
          console.log('📊 Elements details:', elements.map((el: any) => ({ id: el.id, type: el.type })));
          console.log('🎨 Canvas viewbox:', canvas.viewbox());
          console.log('🎨 Canvas zoom:', canvas.zoom());

          const rootElement = canvas.getRootElement();
          console.log('🌳 Root element:', rootElement);

          // Check DOM rendering
          const canvasContainer = canvas.getContainer();
          const svgElement = canvasContainer?.querySelector('svg');
          const shapeElements = canvasContainer?.querySelectorAll('[data-element-id]');

          console.log('🖼️ DOM RENDERING CHECK:');
          console.log('  - Canvas container:', canvasContainer);
          console.log('  - SVG element:', svgElement);
          console.log('  - SVG dimensions:', svgElement ? `${svgElement.getAttribute('width')}x${svgElement.getAttribute('height')}` : 'No SVG');
          console.log('  - Shape elements found:', shapeElements?.length || 0);

          // Check element positions and visibility
          if (shapeElements && shapeElements.length > 0) {
            console.log('  - First 3 shape elements:');
            Array.from(shapeElements).slice(0, 3).forEach((el, i) => {
              const style = getComputedStyle(el as Element);
              console.log(`    Shape ${i}:`, {
                id: (el as Element).getAttribute('data-element-id'),
                transform: (el as Element).getAttribute('transform'),
                visibility: style.visibility,
                display: style.display,
                opacity: style.opacity
              });
            });
          }

          return {
            elementsCount: elements.length,
            elements: elements,
            viewbox: canvas.viewbox(),
            zoom: canvas.zoom(),
            rootElement: rootElement,
            domElements: shapeElements?.length || 0,
            svgDimensions: svgElement ? `${svgElement.getAttribute('width')}x${svgElement.getAttribute('height')}` : 'No SVG',
            // Add debug actions
            forceRedraw: () => {
              console.log('🔄 Forcing canvas redraw...');
              canvas.viewbox(canvas.viewbox());
            },
            zoomToFit: () => {
              console.log('🔍 Zooming to fit...');
              canvas.zoom('fit-viewport');
            },
            showElementPositions: () => {
              console.log('📍 Element positions:');
              elements.forEach((el: any) => {
                console.log(`  ${el.id}: x=${el.x}, y=${el.y}, width=${el.width}, height=${el.height}`);
              });
            },
            resetViewbox: () => {
              console.log('🔄 Resetting viewbox...');
              canvas.viewbox({ x: 0, y: 0, width: 1200, height: 800 });
              canvas.zoom('fit-viewport');
            },
            forceVisibility: () => {
              console.log('👁️ FORCING VISIBILITY...');
              const canvasContainer = canvas.getContainer();
              const svgElement = canvasContainer?.querySelector('svg');
              const shapeElements = canvasContainer?.querySelectorAll('[data-element-id]');

              // Force container refresh
              if (canvasContainer) {
                canvasContainer.style.transform = 'translateZ(0)';
                setTimeout(() => canvasContainer.style.transform = '', 50);
              }

              // Force SVG refresh
              if (svgElement) {
                svgElement.style.opacity = '0.99';
                setTimeout(() => svgElement.style.opacity = '1', 50);
              }

              // Force shape visibility
              if (shapeElements) {
                Array.from(shapeElements).forEach((el: any) => {
                  el.style.opacity = '1';
                  el.style.visibility = 'visible';
                  el.style.display = 'block';
                });
              }

              canvas.zoom('fit-viewport');
              console.log('✅ Visibility forced!');
            }
          };
        } catch (e) {
          console.error('❌ Debug check failed:', e);
          return null;
        }
      };

      console.log('🛠️ Debug helper __debug_check() available in console');
    }
  }, []);  // Separate effect to handle XML changes without reinitializing modeler
  useEffect(() => {
    // COMPLETELY DISABLE EFFECT DURING MANUAL IMPORTS
    if (isManualImport || manualImportRef.current) {
      return;
    }
    
    // Skip effect if no modeler or XML
    if (!modelerRef.current || !xml || xml === initialXml) {
      return;
    }
    
    // Additional check: Don't run effect within 10 seconds of manual import (increased from 5)
    const now = Date.now();
    if (!window.__lastManualImport) window.__lastManualImport = 0;
    if (now - window.__lastManualImport < 10000) {
      return;
    }
    
    // Additional check: Don't run if we just imported from URL/file
    if (window.__recent_manual_import === true) {
      return;
    }

    // CHECK XML LENGTH TO PREVENT OVERRIDING LARGE IMPORTS
    if (xml.length < 1000 && window.__lastManualImport && (now - window.__lastManualImport < 30000)) {
      return;
    }

    const importXmlContent = async () => {
      try {
        setIsLoading(true);
        setError('');
        
        await importXmlSafely(modelerRef.current!, xml, 'xml-change');
        
        // Ensure proper viewport fitting after import
        try {
          await zoomSafely(modelerRef.current!, 'fit-viewport');
        } catch (e) {
          console.debug('Could not fit viewport after import', e);
        }
        
        onDirtyChange(false);
        
      } catch (err: any) {
        console.error('❌ Error importing XML content:', err);
        setError(`Failed to import diagram: ${err.message}`);
      } finally {
        setIsLoading(false);
      }
    };

    importXmlContent();
  }, [xml, initialXml, onDirtyChange, importXmlSafely, zoomSafely, isManualImport]);


  // Toast notification helper
  const showToast = (message: string, type: 'success' | 'error' | 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000); // Auto-hide after 5 seconds
  };

  // Helper function to completely clear modeler for import override
  const clearModelerForImport = async (modeler: any, operationType: string) => {
    try {
      
      // Get core services
      const canvas = modeler.get('canvas');
      const elementRegistry = modeler.get('elementRegistry');
      
      // Remove root element first
      const rootElement = canvas.getRootElement();
      if (rootElement) {
        canvas.removeRootElement();
      }
      
      // Clear element registry completely
      const allElements = elementRegistry.getAll().slice(); // Create copy to avoid modification during iteration
      
      allElements.forEach((element: any) => {
        try {
          if (element.id !== 'root-0') { // Don't try to remove the root layer itself
            elementRegistry.remove(element);
          }
        } catch (e) {
          // Ignore individual removal errors
          console.debug('Could not remove element:', element.id, e);
        }
      });
      
      // Create a completely new diagram to reset internal state
      await (modeler as any).createDiagram();
      
    } catch (clearError) {
      console.warn(`Could not clear existing diagram, proceeding with ${operationType}:`, clearError);
    }
  };

  // Store BPMN in Redis temporarily
  const storeBpmnInRedis = async (originalXml: string, filename: string) => {
    // Always ensure a session id (even if remote storage disabled)
    const sessionId = sessionStorage.getItem('sessionId') || `session_${Date.now()}`;
    if (!sessionStorage.getItem('sessionId')) {
      sessionStorage.setItem('sessionId', sessionId);
    }

    // Prepare queued item builder with compression/encryption + hash
    const prepareQueuedItem = async (xmlForQueue: string): Promise<PendingSyncItem> => {
      const key = `bpmn_temp_${filename}_${Date.now()}`;
      const hash = await sha256(xmlForQueue).catch(() => '');
      // compression
      const comp = await compressIfNeeded(xmlForQueue);
      let storedXml = comp.encoded;
      const meta: PendingSyncMeta = { compressed: comp.compressed, algo: comp.algo, version: 2, hash };
      // encryption (applied after compression to storedXml)
      if (QUEUE_ENCRYPTION) {
        const enc = await encryptString(storedXml);
        if (enc) {
          storedXml = enc.b64;
          meta.encrypted = true;
          meta.iv = enc.iv;
        }
      }
      return { key, filename, xml: storedXml, created: Date.now(), meta };
    };

    const enqueue = async (xmlToStore: string) => {
      const item = await prepareQueuedItem(xmlToStore);
      // Enforce queue size limit
      setPendingSyncs(prev => {
        let next = [...prev];
        if (next.length >= QUEUE_MAX_SIZE) {
          const removed = next.shift();
          showToast(`Queue full (>${QUEUE_MAX_SIZE}), evicted oldest: ${removed?.filename}`, 'info');
        }
        next.push(item);
        return next as any;
      });
      try { sessionStorage.setItem(item.key, xmlToStore); } catch { /* ignore */ }
      console.info('[TempStore][OfflineQueue] Queued diagram for later sync:', item.key);
      return item;
    };

    // If offline mode active or backend currently offline, queue
    if (offlineModeActive || !backendOnline) {
      const item = await enqueue(originalXml);
      return { key: item.key, offline: true, queued: true };
    }

    // If disabled via env flag, silently fallback to sessionStorage
    if (TEMP_STORE_DISABLED) {
      const key = `bpmn_temp_${filename}_${Date.now()}`;
      sessionStorage.setItem(key, xml);
      console.info('[TempStore] Disabled via NEXT_PUBLIC_DISABLE_TEMP_STORE, used sessionStorage key:', key);
      return { key, disabled: true };
    }

    try {
      const response = await processApiService.storeBpmnTemporarily({
        xml: originalXml,
        filename,
        // Provide both snake & camel case to support either backend expectation
        session_id: sessionId,
        // @ts-ignore add camelCase for possible backend variant
        sessionId,
        overwrite: true,
      });

      if (response.data?.success) {
        tempStoreFailureRef.current = 0; // reset failures
        showToast(`BPMN stored temporarily: ${response.data.message}`, 'success');
        return response.data;
      }
      throw new Error(response.error || 'Failed to store BPMN temporarily');
    } catch (error: any) {
      tempStoreFailureRef.current += 1;
      const isConnRefused = /fetch|connrefused|connection refused|econnrefused/i.test(error?.message || '');
      const item = await enqueue(originalXml);
      setBackendOnline(false);
      setOfflineModeActive(true);
      const baseMsg = isConnRefused ? 'Backend offline, queued locally' : 'Temp storage failed, queued locally';
      if (tempStoreFailureRef.current <= TEMP_STORE_FAILURE_SILENCE_AFTER) {
        showToast(`${baseMsg}. (key ${item.key})`, 'error');
      }
      console.warn('Temporary storage failure (queued):', { error, key: item.key });
      return { key: item.key, fallback: true, queued: true };
    }
  };

  // Attempt background sync of queued diagrams
  const attemptSync = useCallback(async () => {
    if (pendingSyncs.length === 0) return;
    const reachable = await processApiService.pingBackend(2500);
    if (!reachable) {
      setBackendOnline(false);
      return;
    }
    setBackendOnline(true);
    const remaining: typeof pendingSyncs = [];
    // Preload existing remote temp items for conflict detection
    const sessionId = (sessionStorage.getItem('sessionId') || 'session_sync');
    let remoteItems: any[] = [];
    try {
      const remoteResp = await fetch(`/api/bpmn/temp-store?sessionId=${encodeURIComponent(sessionId)}`);
      if (remoteResp.ok) {
        const json = await remoteResp.json();
        if (json?.data && Array.isArray(json.data)) remoteItems = json.data;
      }
    } catch { /* ignore */ }
    const remoteIndex: Record<string, any> = {};
    remoteItems.forEach(it => { if (it.filename) remoteIndex[it.filename] = it; });
    for (const item of pendingSyncs) {
      try {
        // Reconstruct original XML (decompress & decrypt as needed)
        let originalXml = item.xml;
        if (item.meta?.encrypted && item.meta?.iv) {
          try { originalXml = await decryptString(originalXml, item.meta.iv); } catch { /* ignore */ }
        }
        if (item.meta?.compressed) {
          try { originalXml = await decompressIfNeeded(item); } catch { /* ignore */ }
        }
        // Conflict detection: if remote with same filename exists, produce diff metrics
        const remote = remoteIndex[item.filename];
        if (remote) {
          const { merged, diffMeta } = semanticMerge(originalXml, remote.xml || '');
          const added = diffMeta.added?.length || 0;
          const removed = diffMeta.remoteOnly?.length || 0; // remote-only relative to previous local
          const changed = diffMeta.modified?.length || 0;
          const summary = `${added} added, ${removed} remote-only, ${changed} modified elements`;
          setDiffPreview({
            added,
            removed,
            changed,
            summary,
            localOnly: added,
            remoteOnly: removed,
            assigneeFilledCount: diffMeta.assigneeFilled?.length || 0,
            candidateGroupsFilledCount: diffMeta.candidateGroupsFilled?.length || 0,
            candidateUsersFilledCount: diffMeta.candidateUsersFilled?.length || 0,
            dueDateFilledCount: diffMeta.dueDateFilled?.length || 0,
            extensionsImportedCount: diffMeta.extensionsImported?.length || 0
          });
          // Apply overlays (show before modal)
          if (modelerRef.current) {
            clearDiffOverlays(modelerRef.current);
            applyDiffOverlays(modelerRef.current, diffMeta);
          }
          // Pause sync and ask user
          await new Promise<void>((resolve) => {
            setConflictModal({
              local: { filename: item.filename, xml: originalXml },
              remote,
              onResolve: async (action, opts) => {
                setConflictModal(null);
                if (modelerRef.current) clearDiffOverlays(modelerRef.current);
                if (action === 'skip') {
                  remaining.push(item); // keep for later retry
                  logConflictAction({ filename: item.filename, action: 'skip', diff: diffMeta });
                } else if (action === 'overwrite') {
                  try {
                    const res = await processApiService.storeBpmnTemporarily({
                      xml: originalXml, // local wins
                      filename: item.filename,
                      session_id: sessionId,
                      overwrite: true,
                    });
                    if (res.data?.success) {
                      try { sessionStorage.removeItem(item.key); } catch {}
                      console.info('[Sync] Overwrote remote diagram', item.filename);
                      logConflictAction({ filename: item.filename, action: 'overwrite', diff: diffMeta });
                    } else {
                      remaining.push(item);
                    }
                  } catch {
                    remaining.push(item);
                  }
                } else if (action === 'merge') {
                  // Semantic merge (preserve remote-only + reconcile basics)
                  const { merged: mergedXml } = semanticMerge(originalXml, remote.xml || '');
                  try {
                    const res = await processApiService.storeBpmnTemporarily({
                      xml: mergedXml,
                      filename: item.filename,
                      session_id: sessionId,
                      overwrite: true,
                    });
                    if (res.data?.success) {
                      try { sessionStorage.removeItem(item.key); } catch {}
                      console.info('[Sync] Semantic merged diagram', item.filename);
                      logConflictAction({ filename: item.filename, action: 'merge', diff: diffMeta });
                    } else {
                      remaining.push(item);
                    }
                  } catch {
                    remaining.push(item);
                  }
                } else if (action === 'rename') {
                  const newFilename = opts?.newFilename || `copy_${Date.now()}_${item.filename}`;
                  try {
                    const res = await processApiService.storeBpmnTemporarily({
                      xml: originalXml,
                      filename: newFilename,
                      session_id: sessionId,
                      overwrite: true,
                    });
                    if (res.data?.success) {
                      try { sessionStorage.removeItem(item.key); } catch {}
                      console.info('[Sync] Stored renamed diagram', newFilename);
                      logConflictAction({ filename: newFilename, action: 'rename', diff: diffMeta });
                    } else {
                      remaining.push(item);
                    }
                  } catch {
                    remaining.push(item);
                  }
                }
                resolve();
              }
            });
          });
          continue; // move to next item after user resolves
        }
        const res = await processApiService.storeBpmnTemporarily({
          xml: originalXml,
          filename: item.filename,
          session_id: (sessionStorage.getItem('sessionId') || 'session_sync'),
          overwrite: true,
        });
        if (res.data?.success) {
          try { sessionStorage.removeItem(item.key); } catch {}
          console.info('[Sync] Uploaded queued diagram', item.filename);
        } else {
          remaining.push(item);
        }
      } catch (e) {
        remaining.push(item);
      }
    }
    setPendingSyncs(remaining);
  }, [pendingSyncs]);

  attemptSyncRef.current = attemptSync;

  // Poll while offline
  useEffect(() => {
    if (backendOnline || pendingSyncs.length === 0) {
      if (retryIntervalRef.current) {
        clearInterval(retryIntervalRef.current);
        retryIntervalRef.current = null;
      }
      return;
    }
    if (!retryIntervalRef.current) {
      retryIntervalRef.current = setInterval(() => {
        attemptSync();
      }, 10000);
    }
    return () => {
      if (retryIntervalRef.current) {
        clearInterval(retryIntervalRef.current);
        retryIntervalRef.current = null;
      }
    };
  }, [backendOnline, pendingSyncs, attemptSync]);

  const handleToggleTransactionBoundaries = () => {
    // Toggle transaction boundaries visualization
    setShowTransactionBoundaries(!showTransactionBoundaries);
    // This would integrate with actual transaction boundary logic
  };

  const handleApplyColorTheme = (theme: string) => {
    if (modelerRef.current && selectedElement) {
      const modeling = modelerRef.current.get('modeling') as any;
      const colors = {
        'success': { fill: '#E8F5E8', stroke: '#388E3C' },
        'warning': { fill: '#FFF3E0', stroke: '#F57C00' },
        'error': { fill: '#FFEBEE', stroke: '#D32F2F' }
      };
      const color = colors[theme as keyof typeof colors];
      if (color) {
        modeling.setColor(selectedElement, color);
      }
    }
  };

  const handleSetElementColor = (color: { fill?: string; stroke?: string }) => {
    if (modelerRef.current && selectedElement) {
      const modeling = modelerRef.current.get('modeling') as any;
      modeling.setColor(selectedElement, color);
    }
  };

  const getColorPalette = () => {
    return [
      { name: 'Default', fill: undefined, stroke: undefined },
      { name: 'Blue', fill: '#E3F2FD', stroke: '#1976D2' },
      { name: 'Green', fill: '#E8F5E8', stroke: '#388E3C' },
      { name: 'Orange', fill: '#FFF3E0', stroke: '#F57C00' },
      { name: 'Red', fill: '#FFEBEE', stroke: '#D32F2F' },
      { name: 'Purple', fill: '#F3E5F5', stroke: '#7B1FA2' },
      { name: 'Yellow', fill: '#FFFDE7', stroke: '#FBC02D' },
      { name: 'Cyan', fill: '#E0F7FA', stroke: '#00ACC1' },
      { name: 'Pink', fill: '#FCE4EC', stroke: '#C2185B' },
      { name: 'Indigo', fill: '#E8EAF6', stroke: '#303F9F' },
      { name: 'Teal', fill: '#E0F2F1', stroke: '#00796B' },
      { name: 'Gray', fill: '#F5F5F5', stroke: '#757575' }
    ];
  };

  const handleSave = async () => {
    if (!modelerRef.current) return;
    try {
      
      // Force a fresh XML export directly from the modeler
      const freshResult = await (modelerRef.current as any).saveXML({ format: true });
      const freshXml = freshResult.xml || '';
      
      // Use the fresh XML for saving
      const savedXml = freshXml;
      setXml(savedXml);
      
      if (onSave) {
        onSave(savedXml);
      }
      onDirtyChange(false);
      showToast('Workflow changes ready to be saved.', 'success');
    } catch (err: any) {
      console.error('Error saving diagram:', err);
      setError(`Failed to save diagram: ${err.message}`);
      showToast(`Error saving diagram: ${err.message}`, 'error');
    }
  };

  const handleSaveAndExecute = async () => {
    if (!modelerRef.current) return;
    try {
      
      // First save the diagram
      const freshResult = await (modelerRef.current as any).saveXML({ format: true });
      const freshXml = freshResult.xml || '';
      
      if (!freshXml || freshXml.length < 100) {
        throw new Error('Invalid BPMN XML generated');
      }
      
      setXml(freshXml);
      
      // Call onSave if provided
      if (onSave) {
        onSave(freshXml);
      }
      onDirtyChange(false);
      
      // Show saving toast
      showToast('Workflow saved. Creating and executing workflow instance...', 'info');
      
      // Create and execute workflow
      const workflowName = `Workflow_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}`;
      const executionResult = await workflowApiService.createAndExecuteWorkflow({
        bpmn_xml: freshXml,
        workflow_name: workflowName,
        workflow_description: 'Workflow created and executed from BPMN Modeler',
        input_data: {},
        created_by: 'user' // This should come from auth context
      });
      
      showToast(`Workflow executed successfully! Instance ID: ${executionResult.instance.id}`, 'success');
      
      // Optionally navigate to the instance details page
      if (typeof window !== 'undefined') {
        setTimeout(() => {
          window.open(`/instances/${executionResult.instance.id}`, '_blank');
        }, 1000);
      }
      
    } catch (err: any) {
      console.error('Error saving and executing workflow:', err);
      const errorMessage = err.message || 'Unknown error occurred';
      setError(`Failed to save and execute workflow: ${errorMessage}`);
      showToast(`Error: ${errorMessage}`, 'error');
    }
  };

  const handleDownload = () => {
    if (xml) {
      const blob = new Blob([xml], { type: 'application/xml' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'workflow.bpmn';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };

  const handleNewDiagram = async () => {
    if (!modelerRef.current) {
      setError('BPMN Modeler not initialized');
      return;
    }

    try {
      setIsLoading(true);
      setError('');
      
      const newXml = await createDiagramSafely(modelerRef.current);
      setXml(newXml);
      onDirtyChange(false);
      showToast('New diagram created successfully', 'success');
      
    } catch (err: any) {
      console.error('❌ Error creating new diagram via button:', err);
      setError(`Failed to create new diagram: ${err.message}`);
      showToast('Failed to create new diagram', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExecuteWorkflow = async () => {
    if (!xml) {
      alert('Please save the workflow first before executing');
      return;
    }

    setExecutionStatus('Starting workflow execution...');
    
    try {
      // Call the BPMN backend API
      const bpmnBackendUrl = process.env.NEXT_PUBLIC_BPMN_BACKEND_URL || 'http://localhost:8100';
      
      const response = await fetch(`${bpmnBackendUrl}/api/workflows/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/xml',
        },
        body: xml,
      });

      if (response.ok) {
        const result = await response.json();
        setExecutionStatus('Workflow started successfully!');
        
        // Show execution steps from backend response
        if (result.steps) {
          for (let i = 0; i < result.steps.length; i++) {
            await new Promise(resolve => setTimeout(resolve, 1500));
            setExecutionStatus(`Executing: ${result.steps[i]} (${i + 1}/${result.steps.length})`);
          }
        }
        
        setExecutionStatus('Workflow completed successfully!');
      } else {
        throw new Error(`Backend error: ${response.status}`);
      }
      
      // Reset after 3 seconds
      setTimeout(() => setExecutionStatus(''), 3000);
      
    } catch (error) {
      // Fallback to simulation if backend is not available
      console.warn('BPMN backend not available, using simulation:', error);
      
      await new Promise(resolve => setTimeout(resolve, 1000));
      setExecutionStatus('Workflow started successfully! (Simulated)');
      
      const steps = ['Start Event', 'Sample Task', 'End Event'];
      for (let i = 0; i < steps.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 1500));
        setExecutionStatus(`Executing: ${steps[i]} (${i + 1}/${steps.length}) - Simulated`);
      }
      
      setExecutionStatus('Workflow completed successfully! (Simulated)');
      setTimeout(() => setExecutionStatus(''), 3000);
    }
  };

  const handleImport = () => {
    setShowImportDialog(true);
    setImportUrl('');
  };

  const handleImportCancel = () => {
    setShowImportDialog(false);
    setImportUrl('');
    setImportMethod('url');
  };

  const handleFileImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsImporting(true);
    setIsManualImport(true);
    manualImportRef.current = true;
    setError('');

    try {
      const xmlContent = await file.text();
      
      if (!xmlContent || xmlContent.trim().length === 0) {
        throw new Error('The file is empty');
      }

      // Validate that it looks like XML
      if (!xmlContent.trim().startsWith('<?xml') && !xmlContent.trim().startsWith('<')) {
        throw new Error('The file does not contain valid XML content');
      }

      console.log('Successfully loaded file content, length:', xmlContent.length);

      // Validate and normalize the BPMN XML
  const normalizedXml = ensureCamundaNamespace(validateAndNormalizeBpmnXml(xmlContent));

      // Import the XML directly into the modeler (like the working version)
      if (!modelerRef.current) {
        throw new Error('BPMN Modeler not initialized');
      }

      // Completely clear the modeler for override import
      await clearModelerForImport(modelerRef.current, 'file import');
      
      // Import the XML directly
      await (modelerRef.current as any).importXML(normalizedXml);
      
      // Force canvas refresh and ensure elements are visible
      const canvas = modelerRef.current.get('canvas');
      const elementRegistry = modelerRef.current.get('elementRegistry');
      
      // Force canvas to refresh/redraw
      if (canvas.viewbox) {
        canvas.viewbox(canvas.viewbox());
      }      // Zoom to fit the viewport with delay to ensure DOM is ready
      setTimeout(async () => {
        try {
          const canvas = modelerRef.current!.get('canvas');
          canvas.zoom('fit-viewport');
          
          // Force a redraw
          canvas.resize();
        } catch (e) {
          console.debug('Could not fit viewport after file import', e);
        }
      }, 500);
      
      // Reset properties panel to prevent stale businessObject errors
      setSelectedElement(null);
      
      // Force properties panel refresh with delay
      setTimeout(() => {
        const eventBus = modelerRef.current!.get('eventBus');
        eventBus.fire('selection.changed', { newSelection: [] });
      }, 100);
      
      // Update the XML state
      const { xml: importedXml } = await (modelerRef.current as any).saveXML({ format: true });
      setXml(importedXml || '');
      
      // Clear error state and ensure clean display
      setError('');
      setSelectedElement(null);
      
      showToast('BPMN diagram imported successfully!', 'success');
      setShowImportDialog(false);
      setImportUrl('');
      setImportMethod('url');
      onDirtyChange(false);

    } catch (error) {
      console.error('Error importing BPMN from file:', error);
      setError(error instanceof Error ? error.message : 'Unknown error occurred');
    } finally {
      setIsImporting(false);
      // Delay resetting manual import flags to prevent effect interference
      setTimeout(() => {
        setIsManualImport(false);
        manualImportRef.current = false;
      }, 1000);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

    const validateAndNormalizeBpmnXml = (xmlContent: string): string => {
    // Basic XML structure validation
    if (!xmlContent || xmlContent.trim().length === 0) {
      throw new Error('Empty content: The file appears to be empty');
    }
    
    // Check if it starts with XML declaration or root element
    const trimmedContent = xmlContent.trim();
    if (!trimmedContent.startsWith('<?xml') && !trimmedContent.startsWith('<')) {
      throw new Error('Invalid XML format: Content does not appear to be valid XML');
    }
    
    // Check for basic XML well-formedness indicators
    if (!trimmedContent.includes('<') || !trimmedContent.includes('>')) {
      throw new Error('Invalid XML format: Missing basic XML structure');
    }
    
    // Check if it's a valid BPMN XML with proper structure
    if (!xmlContent.includes('bpmn:definitions') && !xmlContent.includes('<definitions')) {
      throw new Error('Invalid BPMN format: Not a BPMN file - missing definitions element');
    }
    
    // Check for process elements (essential for BPMN)
    if (!xmlContent.includes('bpmn:process') && !xmlContent.includes('<process')) {
      throw new Error('Invalid BPMN format: No process elements found - this may not be a valid BPMN diagram');
    }
    
    // Check for diagram elements
    if (!xmlContent.includes('bpmndi:BPMNDiagram') && !xmlContent.includes('BPMNDiagram')) {
      console.warn('No diagram information found - BPMN.js will attempt to create layout automatically');
      // For XML without diagram info, we'll let bpmn-js handle the layout
    }
    
    return xmlContent;
  };

  const handleImportFromUrl = async () => {
    if (!importUrl.trim()) {
      setError('Please enter a valid URL');
      return;
    }

    setIsImporting(true);
    setIsManualImport(true);
    manualImportRef.current = true;
    setError('');

    try {
  let xmlContent = '';
  const isLocalRelative = importUrl.startsWith('/') && !importUrl.startsWith('//');

      const doDirectFetch = async (): Promise<string> => {
        const resp = await fetch(importUrl, {
          method: 'GET',
          headers: { 'Accept': 'application/xml, text/xml, text/plain, */*' },
          // mode 'cors' is fine; same-origin will ignore; remote may need proxy fallback
          mode: 'cors'
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${resp.statusText}`);
        return await resp.text();
      };

      const doProxyFetch = async (): Promise<string> => {
        const proxyUrl = `${IMPORT_PROXY_ROUTE}?url=${encodeURIComponent(importUrl)}`;
        const proxyResp = await fetch(proxyUrl, {
          method: 'GET',
          headers: { 'Accept': 'application/xml, text/xml, text/plain, */*' }
        });
        if (!proxyResp.ok) {
          // Try to parse JSON error from proxy
            let details: any = undefined;
            try { details = await proxyResp.json(); } catch (_) { /* ignore */ }
            const proxyMsg = details?.error || proxyResp.statusText || 'Proxy fetch failed';
            throw new Error(`Proxy error: ${proxyMsg}`);
        }
        return await proxyResp.text();
      };

      const classifyConnRefused = (err: unknown) => {
        const msg = err instanceof Error ? (err.message || '') : String(err);
        return /ECONNREFUSED|ENOTFOUND|ERR_CONNECTION_REFUSED|Failed to fetch/.test(msg);
      };

      // Execution order logic
  const attemptDirectFirst = !IMPORT_PROXY_ONLY && !IMPORT_PROXY_FIRST; // default behavior
  const attemptProxyFirst = IMPORT_PROXY_FIRST || IMPORT_PROXY_ONLY;

      let directErr: any = null;
      let proxyErr: any = null;

      const tryDirect = async () => {
        try { return await doDirectFetch(); } catch (e) { directErr = e; return undefined; }
      };
      const tryProxy = async () => {
        try { return await doProxyFetch(); } catch (e) { proxyErr = e; return undefined; }
      };

      if (isLocalRelative) {
        // Directly fetch from same origin static public folder, skip proxy entirely
        try {
          xmlContent = await doDirectFetch();
        } catch (e) {
          throw new Error(`Local file fetch failed: ${(e as Error).message}`);
        }
      } else if (attemptProxyFirst) {
        const proxyResult = await tryProxy();
        const directResult = !IMPORT_PROXY_ONLY && !proxyResult ? await tryDirect() : undefined;
        xmlContent = proxyResult || directResult || '';
      } else if (attemptDirectFirst) {
        const directResult = await tryDirect();
        const proxyResult = !directResult ? await tryProxy() : undefined;
        xmlContent = directResult || proxyResult || '';
      }

      if (!xmlContent) {
        // Build richer diagnostic
        const messages: string[] = [];
        if (directErr) messages.push(`Direct fetch failed: ${directErr instanceof Error ? directErr.message : directErr}`);
        if (proxyErr) messages.push(`Proxy fetch failed: ${proxyErr instanceof Error ? proxyErr.message : proxyErr}`);

        // Special hint for connection refused to localhost port
        if (classifyConnRefused(directErr) || classifyConnRefused(proxyErr)) {
          messages.push('Hint: Connection refused suggests no server is listening at the specified host/port (e.g., localhost:3080). Start a static server or use a reachable URL.');
        }

        throw new Error(messages.join(' | '));
      }
      
      if (!xmlContent || xmlContent.trim().length === 0) {
        throw new Error('The URL returned empty content');
      }

      // Validate that the response looks like XML
      if (!xmlContent.trim().startsWith('<?xml') && !xmlContent.trim().startsWith('<')) {
        throw new Error('The URL did not return valid XML content');
      }

      // Validate and normalize the BPMN XML
  const normalizedXml = ensureCamundaNamespace(validateAndNormalizeBpmnXml(xmlContent));

      // Import the XML directly into the modeler (like the working version)
      if (!modelerRef.current) {
        throw new Error('BPMN Modeler not initialized');
      }

      // Completely clear the modeler for override import
      await clearModelerForImport(modelerRef.current, 'URL import');
      
      // Mark manual import to prevent effect interference
      setIsManualImport(true);
      manualImportRef.current = true;
      window.__lastManualImport = Date.now();
      window.__recent_manual_import = true;  // Additional protection
      
      // Import the XML directly (bypass safe import for override behavior)
      let importSucceeded = false;
      try {
        await (modelerRef.current as any).importXML(normalizedXml);
        importSucceeded = true;
      } catch (impErr) {
        console.error('❌ importXML failed:', impErr);
        throw new Error(`BPMN parse/import failed: ${(impErr as Error).message || impErr}`);
      }
      
      // Force canvas refresh and ensure elements are visible
      const canvas = modelerRef.current.get('canvas');
      const elementRegistry = modelerRef.current.get('elementRegistry');
      
      // 1. Force multiple redraws with delays
      const forceRedraw = async () => {
        // Force CSS redraw
        if (containerRef.current) {
          containerRef.current.classList.add('force-redraw');
          await new Promise(resolve => setTimeout(resolve, 50));
          containerRef.current.classList.remove('force-redraw');
        }
        
        // Force canvas refresh
        canvas.viewbox(canvas.viewbox());
        await new Promise(resolve => setTimeout(resolve, 50));
        
        try {
          canvas.zoom('fit-viewport', 'auto');
        } catch (e) {
          console.debug('Zoom failed:', e);
        }
      };

      // Multiple redraw attempts with increasing delays
      forceRedraw()
        .then(() => new Promise(resolve => setTimeout(resolve, 100)))
        .then(forceRedraw)
        .then(() => new Promise(resolve => setTimeout(resolve, 200)))
        .then(forceRedraw);
      
      // 2. Force container and element visibility
      const canvasContainer = canvas.getContainer();
      if (canvasContainer) {
        // Force container refresh
        canvasContainer.style.transform = 'translateZ(0)';
        canvasContainer.style.position = 'relative';
        canvasContainer.style.zIndex = '1';
        
        // Force SVG visibility
        const svgElement = canvasContainer.querySelector('svg');
        if (svgElement) {
          Object.assign(svgElement.style, {
            position: 'relative',
            zIndex: '10',
            width: '100%',
            height: '100%',
            opacity: '1',
            visibility: 'visible',
            display: 'block'
          });
        }
        
        // Force all shape elements to be visible and interactive
        const shapeElements = canvasContainer.querySelectorAll('[data-element-id]');
        if (shapeElements) {
          Array.from(shapeElements).forEach((el: any) => {
            Object.assign(el.style, {
              opacity: '1',
              visibility: 'visible',
              display: 'block',
              pointerEvents: 'auto'
            });
          });
        }
        
        // Restore container transform after a delay
        setTimeout(() => {
          canvasContainer.style.transform = '';
        }, 100);
      }
      
      // Force canvas to refresh/redraw
      if (canvas.viewbox) {
        canvas.viewbox(canvas.viewbox());
      }
      
      // Zoom to fit the viewport with delay to ensure DOM is ready
      setTimeout(async () => {
        try {
          const canvas = modelerRef.current!.get('canvas');
          
          canvas.zoom('fit-viewport');
          
          // Force a canvas refresh (no resize method, use alternative)
          try {
            const eventBus = modelerRef.current!.get('eventBus');
            eventBus.fire('canvas.resized');
          } catch (e) {
            console.debug('Canvas refresh not available', e);
          }
          
          // Clear manual import flags after successful display
          setTimeout(() => {
            setIsManualImport(false);
            manualImportRef.current = false;
            window.__recent_manual_import = false;  // Clear additional protection
          }, 5000);  // Extended to 5 seconds
          
        } catch (e) {
          console.error('❌ Error in viewport fitting:', e);
          // Still clear flags even if viewport fails
          setTimeout(() => {
            setIsManualImport(false);
            manualImportRef.current = false;
            window.__recent_manual_import = false;  // Clear additional protection
          }, 5000);  // Extended to 5 seconds
        }
      }, 500);
      
      // Reset properties panel to prevent stale businessObject errors
      setSelectedElement(null);
      
      // Force properties panel refresh with delay
      setTimeout(() => {
        const eventBus = modelerRef.current!.get('eventBus');
        eventBus.fire('selection.changed', { newSelection: [] });
      }, 100);
      
      if (importSucceeded) {
        // Update the XML state only if import actually succeeded
        const { xml: importedXml } = await (modelerRef.current as any).saveXML({ format: true });
        setXml(importedXml || '');

        // Decide whether to attempt remote temp storage (skip for local static assets or if disabled)
        const isLocalStaticRef = importUrl.startsWith('/') && !importUrl.startsWith('//');
        let storageOutcome: any = null;
        if (!isLocalStaticRef) {
          storageOutcome = await storeBpmnInRedis(normalizedXml, `imported_${Date.now()}.bpmn`);
        } else {
          console.info('[Import] Skipping remote temp storage for local static path:', importUrl);
        }

        if (storageOutcome?.fallback) {
          showToast('Imported (remote temp store offline, local session used).', 'info');
        } else if (storageOutcome?.disabled) {
          showToast('Imported (temp store disabled).', 'info');
        } else if (isLocalRelative) {
          showToast('BPMN diagram imported from local public path.', 'success');
        } else if (storageOutcome === null) {
          showToast('BPMN diagram imported (no storage attempted).', 'success');
        } else {
          showToast('BPMN diagram imported successfully!', 'success');
        }

        // Auto zoom fit again (ensures view) and auto select first meaningful element
        try {
          const canvas = modelerRef.current!.get('canvas');
          canvas.zoom('fit-viewport');
        } catch (e) { /* ignore */ }
        try {
          const elementRegistry = modelerRef.current!.get('elementRegistry');
          const selectionSvc = modelerRef.current!.get('selection');
          const all = elementRegistry.getAll();
            const firstTask = all.find((el: any) => /Task$/.test(el.businessObject?.$type || '')) ||
                              all.find((el: any) => el.type === 'bpmn:StartEvent' || el.type === 'bpmn:StartEvent');
          if (firstTask) {
            selectionSvc.select(firstTask);
          }
        } catch (e) {
          console.debug('Auto-select failed', e);
        }
      }
      setShowImportDialog(false);
      setImportUrl('');
      onDirtyChange(false);

    } catch (error) {
      console.error('Error importing BPMN from URL:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      const lower = errorMessage.toLowerCase();

      // Connection refused specific guidance
      const isConnRefused = /connrefused|connection refused|econnrefused|failed to fetch/.test(lower);
      if (isConnRefused) {
        const hint = 'Connection refused. Ensure a server is running at the URL (e.g. run: npx http-server -p 3080 .) or move the file into public/ and use a relative path (e.g. /bpmn/telecom-o2a-camunda.bpmn).';
        showToast(hint, 'error');
        setError(hint);
      } else if (
        lower.includes('no diagram to display') ||
        lower.includes('unparsable content') ||
        lower.includes('unknown type') ||
        lower.includes('invalid bpmn') ||
        lower.includes('empty content') ||
        lower.includes('not return valid xml')
      ) {
        showToast(`Invalid file: ${errorMessage}`, 'error');
        setError(`Please check your file and try again. ${errorMessage}`);
      } else {
        showToast(`Import failed: ${errorMessage}`, 'error');
        setError(`Import failed: ${errorMessage}`);
        setShowImportDialog(false);
        setImportUrl('');
      }
    } finally {
      setIsImporting(false);
      // Delay resetting manual import flags to prevent effect interference
      setTimeout(() => {
        setIsManualImport(false);
        manualImportRef.current = false;
      }, 1000);
    }
  };

  const handleAutoImport = async (url: string, modelerInstance: BpmnModeler) => {
    if (!url.trim() || !modelerInstance) return;

    try {
      // Validate URL format
      const validUrl = new URL(url.trim());
      
      // Fetch the BPMN XML from the URL with better CORS handling
      const response = await fetch(validUrl.toString(), {
        method: 'GET',
        mode: 'cors',
        headers: {
          'Accept': 'application/xml, text/xml, text/plain, */*',
          'Content-Type': 'application/xml',
        },
        credentials: 'omit',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status} - ${response.statusText}`);
      }

      const xmlData = await response.text();
      
      if (!xmlData || xmlData.trim().length === 0) {
        throw new Error('Empty response from URL');
      }

      // Validate that the response looks like XML
      if (!xmlData.trim().startsWith('<?xml') && !xmlData.trim().startsWith('<')) {
        throw new Error('Response does not appear to be valid XML content');
      }

  // Ensure camunda namespace
  const xmlWithNs = ensureCamundaNamespace(xmlData);
  // Use our safe import function
  await importXmlSafely(modelerInstance, xmlWithNs, 'auto-import');
  setXml(xmlWithNs);
      
    } catch (error) {
      console.error('❌ Error auto-importing BPMN from URL:', error);
      // Don't show alert for auto-import failures, just log
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4 flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-900">FSM Process Designer</h2>
        <div className="flex items-center space-x-4">
          {(!backendOnline || pendingSyncs.length > 0) && (
            <div className="flex items-center space-x-2">
              {!backendOnline && (
                <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-red-100 text-red-700 border border-red-300" title="Backend unreachable; storing diagrams locally until it returns">Offline Storage</span>
              )}
              {pendingSyncs.length > 0 && (
                <button
                  onClick={handleManualSync}
                  className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-300 hover:bg-yellow-200"
                  title="Manually try syncing queued diagrams"
                >Sync {pendingSyncs.length}</button>
              )}
            </div>
          )}
          <div className="flex space-x-3">
          <button
            onClick={handleNewDiagram}
            className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded text-sm font-medium"
            disabled={isLoading}
          >
            {isLoading ? 'Loading...' : 'New Diagram'}
          </button>
          <button
            onClick={handleSave}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-50"
            disabled={isLoading || (!isDirty && !xml)}
          >
            Save
          </button>
          <button
            onClick={handleSaveAndExecute}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-50"
            disabled={isLoading || (!isDirty && !xml)}
          >
            Save & Execute
          </button>
          <button
            onClick={handleToggleTransactionBoundaries}
            className={`px-4 py-2 rounded text-sm font-medium ${
              showTransactionBoundaries 
                ? 'bg-orange-600 hover:bg-orange-700 text-white' 
                : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
            }`}
            disabled={isLoading}
          >
            {showTransactionBoundaries ? 'Hide' : 'Show'} Boundaries
          </button>
          <button
            onClick={handleImport}
            className="bg-cyan-600 hover:bg-cyan-700 text-white px-4 py-2 rounded text-sm font-medium"
            disabled={isLoading}
          >
            Import
          </button>
          <button
            onClick={() => setShowMinimap(!showMinimap)}
            className={`px-4 py-2 rounded text-sm font-medium ${
              showMinimap 
                ? 'bg-indigo-600 hover:bg-indigo-700 text-white' 
                : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
            }`}
            disabled={isLoading}
          >
            {showMinimap ? 'Hide' : 'Show'} Minimap
          </button>
          <button
            onClick={handleDownload}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded text-sm font-medium"
            disabled={isLoading || !xml}
          >
            Download
          </button>
          <button
            onClick={onClose}
            className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded text-sm font-medium"
          >
            Close
          </button>
          </div>
        </div>
      </div>

      {/* Execution Status */}
      {executionStatus && (
        <div className="bg-green-50 border-l-4 border-green-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-green-700">{executionStatus}</p>
            </div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-yellow-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Collapsible queued diagrams panel (enhanced) */}
      {pendingSyncs.length > 0 && !queueCollapsed && (
        <div className="fixed bottom-4 left-4 bg-white border border-gray-200 shadow-lg rounded-md p-3 w-72 z-40">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-gray-700">Queued Diagrams ({pendingSyncs.length})</span>
            <div className="flex items-center space-x-2">
              <button onClick={handleManualSync} className="text-xs text-blue-600 hover:underline">Sync Now</button>
              <button onClick={() => setQueueCollapsed(true)} className="text-xs text-gray-500 hover:underline" title="Collapse">×</button>
            </div>
          </div>
          <ul className="max-h-32 overflow-auto space-y-1">
            {pendingSyncs.slice(-10).map(item => (
              <li key={item.key} className="text-[10px] text-gray-600 truncate" title={item.filename}>{new Date(item.created).toLocaleTimeString()} • {item.filename}</li>
            ))}
          </ul>
          <div className="mt-2 text-[10px] text-gray-400">
            {backendOnline ? 'Backend online' : 'Waiting for backend...'}
          </div>
        </div>
      )}
      {pendingSyncs.length > 0 && queueCollapsed && (
        <button
          onClick={() => setQueueCollapsed(false)}
          className="fixed bottom-4 left-4 bg-white border border-gray-300 shadow-md rounded-full px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 z-40"
          title="Expand queued diagrams panel"
        >Queue ({pendingSyncs.length})</button>
      )}
      {/* Toast Notifications */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 max-w-sm w-full ${
          toast.type === 'success' ? 'bg-green-50 border-green-400' :
          toast.type === 'error' ? 'bg-red-50 border-red-400' :
          'bg-blue-50 border-blue-400'
        } border-l-4 p-4 shadow-lg rounded-md`}>
          <div className="flex">
            <div className="flex-shrink-0">
              {toast.type === 'success' && (
                <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              )}
              {toast.type === 'error' && (
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              )}
              {toast.type === 'info' && (
                <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              )}
            </div>
            <div className="ml-3">
              <p className={`text-sm ${
                toast.type === 'success' ? 'text-green-700' :
                toast.type === 'error' ? 'text-red-700' :
                'text-blue-700'
              }`}>{toast.message}</p>
            </div>
            <div className="ml-auto pl-3">
              <button
                onClick={() => setToast(null)}
                className={`text-sm ${
                  toast.type === 'success' ? 'text-green-500 hover:text-green-600' :
                  toast.type === 'error' ? 'text-red-500 hover:text-red-600' :
                  'text-blue-500 hover:text-blue-600'
                }`}
              >
                ×
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Conflict Modal (Enhanced) */}
  {conflictModal && (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full mx-4 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Conflict Detected</h3>
            <p className="text-sm text-gray-600 mb-4">A remote temporary version of <span className="font-medium">{conflictModal.local.filename}</span> exists.</p>
            {diffPreview && (
               <div className="mb-4 p-3 bg-gray-50 rounded border text-xs text-gray-700 space-y-1">
                 <div><span className="font-medium">Structural Diff:</span> {diffPreview.summary} • Local-only: {diffPreview.localOnly} • Remote-only: {diffPreview.remoteOnly}</div>
                 { (diffPreview as any).assigneeFilledCount ? <div>Assignees adopted: {(diffPreview as any).assigneeFilledCount}</div> : null }
                 { (diffPreview as any).candidateGroupsFilledCount ? <div>Candidate Groups adopted: {(diffPreview as any).candidateGroupsFilledCount}</div> : null }
                 { (diffPreview as any).candidateUsersFilledCount ? <div>Candidate Users adopted: {(diffPreview as any).candidateUsersFilledCount}</div> : null }
                 { (diffPreview as any).dueDateFilledCount ? <div>Due Dates adopted: {(diffPreview as any).dueDateFilledCount}</div> : null }
                 { (diffPreview as any).extensionsImportedCount ? <div>Extensions imported: {(diffPreview as any).extensionsImportedCount}</div> : null }
               </div>
             )}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
              <button onClick={() => conflictModal.onResolve('skip')} className="px-3 py-2 rounded bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-medium">Skip</button>
              <button onClick={() => conflictModal.onResolve('overwrite')} className="px-3 py-2 rounded bg-red-600 hover:bg-red-700 text-white text-xs font-medium">Overwrite</button>
              <button onClick={() => conflictModal.onResolve('merge')} className="px-3 py-2 rounded bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium">Merge</button>
              <button onClick={() => { const nf = prompt('New filename:', `copy_${Date.now()}_${conflictModal.local.filename}`); if (nf) (conflictModal.onResolve as any)('rename', { newFilename: nf }); }} className="px-3 py-2 rounded bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium">Rename</button>
              <button onClick={() => conflictModal.onResolve('skip')} className="px-3 py-2 rounded bg-gray-50 hover:bg-gray-100 text-gray-500 text-xs font-medium">Close</button>
            </div>
            <details className="mb-3">
              <summary className="cursor-pointer text-xs text-gray-700">Show Remote / Local Preview (truncated)</summary>
              <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-2 max-h-72 overflow-auto text-[10px] font-mono">
                <div className="border rounded p-2 bg-white">
                  <div className="font-semibold mb-1">Remote</div>
                  <pre className="whitespace-pre-wrap">{(conflictModal.remote?.xml || '').slice(0, 2000)}</pre>
                </div>
                <div className="border rounded p-2 bg-white">
                  <div className="font-semibold mb-1">Local</div>
                  <pre className="whitespace-pre-wrap">{(conflictModal.local?.xml || '').slice(0, 2000)}</pre>
                </div>
              </div>
            </details>
          </div>
        </div>
      )}

      {/* Loading Indicator */}
      {isLoading && (
        <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="animate-spin h-5 w-5 text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-blue-700">Initializing BPMN Editor...</p>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Left Sidebar with Properties Panel */}
        <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Properties</h3>
            {selectedElement && (
              <div className="mt-2">
                <p className="text-sm text-gray-600">
                  Selected: {selectedElement.type || 'Element'}
                </p>
                <p className="text-xs text-gray-500">
                  ID: {selectedElement.businessObject?.id || 'N/A'}
                </p>
              </div>
            )}
          </div>
          
          {/* Color Palette */}
          {selectedElement && (
            <div className="p-3 border-b border-gray-200">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Colors</h4>
              <div className="grid grid-cols-4 gap-1">
                {getColorPalette().slice(0, 12).map((color, index) => (
                  <button
                    key={index}
                    className="w-6 h-6 rounded border border-gray-300 hover:border-gray-400"
                    style={{ 
                      backgroundColor: color.fill || '#ffffff',
                      borderColor: color.stroke || '#cccccc'
                    }}
                    onClick={() => handleSetElementColor(color)}
                    title={color.name}
                  />
                ))}
              </div>
              <div className="mt-2 flex space-x-1">
                <button
                  onClick={() => handleApplyColorTheme('success')}
                  className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200"
                >
                  Success
                </button>
                <button
                  onClick={() => handleApplyColorTheme('warning')}
                  className="text-xs px-2 py-1 bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200"
                >
                  Warning
                </button>
                <button
                  onClick={() => handleApplyColorTheme('error')}
                  className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200"
                >
                  Error
                </button>
              </div>
            </div>
          )}
          
          {/* BPMN Properties Panel Container */}
          <div className="flex-1 overflow-auto">
            <div
              ref={propertiesPanelRef}
              id="properties-panel"
              className="h-full properties-panel-container"
              style={{ minHeight: '300px', width: '100%' }}
            />
          </div>
          
          {/* Workflow Info Section */}
          <div className="border-t border-gray-200 p-4">
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Status
                </label>
                <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                  {isLoading ? 'Loading...' : (error ? 'Error' : 'Ready')}
                </div>
              </div>
              
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  XML Length
                </label>
                <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                  {xml ? `${xml.length} chars` : 'No XML'}
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Execution
                </label>
                <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                  {executionStatus ? 'Running' : 'Ready'}
                </div>
              </div>
              
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Transaction Boundaries
                </label>
                <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                  {showTransactionBoundaries ? 'Visible' : 'Hidden'}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* BPMN Canvas */}
        <div className="flex-1 relative">
          {/* Empty state message when no diagram is loaded and not auto-creating */}
          {!isLoading && !xml && !error && !initialXml && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
              <div className="text-center">
                <svg className="mx-auto h-16 w-16 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to Model</h3>
                <p className="text-gray-500 mb-4">Create a new BPMN diagram or import an existing one</p>
                <div className="space-x-3">
                  <button
                    onClick={handleNewDiagram}
                    className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded text-sm font-medium"
                  >
                    Create New Diagram
                  </button>
                  <button
                    onClick={handleImport}
                    className="bg-cyan-600 hover:bg-cyan-700 text-white px-4 py-2 rounded text-sm font-medium"
                  >
                    Import Diagram
                  </button>
                </div>
              </div>
            </div>
          )}
          <div
            ref={containerRef}
            className="bpmn-canvas-container w-full h-full"
            style={{ minHeight: '600px' }}
          />
          {/* Minimap Container */}
          {showMinimap && (
            <div
              ref={minimapRef}
              className="absolute bottom-4 right-4 w-48 h-32 bg-white border border-gray-300 shadow-lg rounded-md overflow-hidden"
              style={{ zIndex: 10 }}
            />
          )}
        </div>
      </div>

      {/* Import Dialog */}
      {showImportDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4">
            <div className="p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Import BPMN Diagram
              </h3>
              
              {/* Import Method Selector */}
              <div className="mb-4">
                <div className="flex space-x-4 mb-3">
                  <button
                    onClick={() => setImportMethod('url')}
                    className={`px-3 py-2 text-sm font-medium rounded-md ${
                      importMethod === 'url'
                        ? 'bg-blue-100 text-blue-700 border border-blue-300'
                        : 'bg-gray-100 text-gray-700 border border-gray-300 hover:bg-gray-200'
                    }`}
                    disabled={isImporting}
                  >
                    From URL
                  </button>
                  <button
                    onClick={() => setImportMethod('file')}
                    className={`px-3 py-2 text-sm font-medium rounded-md ${
                      importMethod === 'file'
                        ? 'bg-blue-100 text-blue-700 border border-blue-300'
                        : 'bg-gray-100 text-gray-700 border border-gray-300 hover:bg-gray-200'
                    }`}
                    disabled={isImporting}
                  >
                    From File
                  </button>
                </div>
              </div>

              {/* URL Import */}
              {importMethod === 'url' && (
                <div className="mb-4">
                  <label htmlFor="import-url" className="block text-sm font-medium text-gray-700 mb-2">
                    BPMN File URL
                  </label>
                  <input
                    id="import-url"
                    type="url"
                    value={importUrl}
                    onChange={(e) => setImportUrl(e.target.value)}
                    placeholder="https://example.com/diagram.bpmn"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    disabled={isImporting}
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Enter the URL of a BPMN file (.bpmn or .xml). Works with localhost, cloud URLs, and CORS-enabled servers.
                  </p>
                  <p className="mt-1 text-xs text-blue-600">
                    💡 Sample: https://cdn.staticaly.com/gh/bpmn-io/bpmn-js-examples/master/starter/diagram.bpmn
                  </p>
                  {error && (
                    <p className="mt-2 text-xs text-red-600">
                      ⚠️ {error}
                    </p>
                  )}
                  <div className="mt-2 p-2 bg-gray-50 rounded-md border">
                    <p className="text-xs text-gray-600 font-medium">Valid BPMN files must contain:</p>
                    <ul className="text-xs text-gray-600 mt-1 space-y-1">
                      <li>• XML format with proper structure</li>
                      <li>• BPMN definitions element</li>
                      <li>• At least one process element</li>
                      <li>• Valid BPMN 2.0 schema compliance</li>
                    </ul>
                  </div>
                </div>
              )}

              {/* File Import */}
              {importMethod === 'file' && (
                <div className="mb-4">
                  <label htmlFor="import-file" className="block text-sm font-medium text-gray-700 mb-2">
                    BPMN File
                  </label>
                  <input
                    ref={fileInputRef}
                    id="import-file"
                    type="file"
                    accept=".bpmn,.xml"
                    onChange={handleFileImport}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    disabled={isImporting}
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Select a BPMN file (.bpmn or .xml) from your computer to import.
                  </p>
                  {error && (
                    <p className="mt-2 text-xs text-red-600">
                      ⚠️ {error}
                    </p>
                  )}
                  <div className="mt-2 p-2 bg-gray-50 rounded-md border">
                    <p className="text-xs text-gray-600 font-medium">Valid BPMN files must contain:</p>
                    <ul className="text-xs text-gray-600 mt-1 space-y-1">
                      <li>• XML format with proper structure</li>
                      <li>• BPMN definitions element</li>
                      <li>• At least one process element</li>
                      <li>• Valid BPMN 2.0 schema compliance</li>
                    </ul>
                  </div>
                </div>
              )}

              <div className="flex justify-end space-x-3">
                <button
                  onClick={handleImportCancel}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  disabled={isImporting}
                >
                  Cancel
                </button>
                {importMethod === 'url' && (
                  <button
                    onClick={handleImportFromUrl}
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={isImporting || !importUrl.trim()}
                  >
                    {isImporting ? 'Importing...' : 'Import from URL'}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BpmnModelerComponent;

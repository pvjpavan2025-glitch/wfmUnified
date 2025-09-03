// Global type declarations for window object extensions
declare global {
  interface Window {
    __lastManualImport: number;
    __recent_manual_import: boolean;
    __debug_import_started: boolean;
    __debug_check: () => void;
    __debug_bpmn_import: any;
    __debug_bpmn_post_import: any;
    __debug_bpmn_helpers: any;
    __wfm_bpmn_modeler_active: any;
  }
}

// Types for BPMN elements
export interface BpmnElement {
  id: string;
  type: string;
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  businessObject?: any;
}

// This export statement is required to make this file a module
// so that the global declarations work properly
export {};

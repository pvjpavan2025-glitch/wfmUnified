import BpmnModeler from 'bpmn-js/lib/Modeler';
import { useBpmnModelerSafe } from './useBpmnModelerSafe';

/**
 * Wrapper class that enforces safe BPMN operations
 * This ensures developers CANNOT accidentally use unsafe BPMN.js methods
 */
export class SafeBpmnModelerWrapper {
  private modeler: BpmnModeler | null = null;
  private safeOperations: ReturnType<typeof useBpmnModelerSafe>;

  constructor(safeOperations: ReturnType<typeof useBpmnModelerSafe>) {
    this.safeOperations = safeOperations;
  }

  /**
   * Initialize the modeler safely
   */
  async initialize(
    containerElement: HTMLDivElement,
    propertiesPanelElement: HTMLDivElement,
    minimapElement: HTMLDivElement | null,
    modules: any[],
    moddleExtensions: any,
    skipInitialDiagram?: boolean
  ) {
    this.modeler = await this.safeOperations.initializeModelerSafely(
      containerElement,
      propertiesPanelElement,
      minimapElement,
      modules,
      moddleExtensions,
      skipInitialDiagram
    );
    return this.modeler;
  }

  /**
   * Import XML safely
   */
  async importXml(xmlContent: string, operationId?: string) {
    if (!this.modeler) throw new Error('Modeler not initialized');
    return this.safeOperations.importXmlSafely(this.modeler, xmlContent, operationId);
  }

  /**
   * Create diagram safely
   */
  async createDiagram() {
    if (!this.modeler) throw new Error('Modeler not initialized');
    return this.safeOperations.createDiagramSafely(this.modeler);
  }

  /**
   * Save XML safely
   */
  async saveXml(format: boolean = true) {
    if (!this.modeler) throw new Error('Modeler not initialized');
    return this.safeOperations.saveXmlSafely(this.modeler, format);
  }

  /**
   * Zoom safely
   */
  zoom(zoomLevel: number | 'fit-viewport' = 'fit-viewport') {
    if (!this.modeler) return false;
    return this.safeOperations.zoomSafely(this.modeler, zoomLevel);
  }

  /**
   * Select element safely
   */
  selectElement(elementId: string | null) {
    if (!this.modeler) return false;
    return this.safeOperations.selectElementSafely(this.modeler, elementId);
  }

  /**
   * Check if modeler is ready
   */
  isReady() {
    return this.safeOperations.isModelerReady(this.modeler);
  }

  /**
   * Get the underlying modeler instance (use with caution)
   * This should only be used for operations that don't have safe wrappers yet
   */
  getUnsafeModeler(): BpmnModeler | null {
    console.warn('⚠️ WARNING: Using unsafe modeler access. Consider adding a safe wrapper for this operation.');
    return this.modeler;
  }

  /**
   * Cleanup safely
   */
  destroy() {
    const result = this.safeOperations.cleanupModelerSafely(this.modeler);
    this.modeler = null;
    return result;
  }

  /**
   * Get a service from the modeler safely
   */
  getService<T = any>(serviceName: string): T | null {
    try {
      if (!this.modeler) return null;
      return this.modeler.get(serviceName) as T;
    } catch (err) {
      console.warn(`⚠️ Failed to get service ${serviceName}:`, err);
      return null;
    }
  }
}

/**
 * Hook that provides a SafeBpmnModelerWrapper instance
 * This is the RECOMMENDED way to use BPMN.js in this application
 */
export const useSafeBpmnModeler = () => {
  const safeOperations = useBpmnModelerSafe();
  return new SafeBpmnModelerWrapper(safeOperations);
};

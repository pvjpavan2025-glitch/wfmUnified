import { useCallback, useRef } from 'react';
import BpmnModeler from 'bpmn-js/lib/Modeler';

/**
 * Custom hook for safe BPMN modeler operations
 * Prevents the root-0 error by ensuring proper initialization sequences
 */
export const useBpmnModelerSafe = () => {
  const retryCountRef = useRef<Map<string, number>>(new Map());

  // Robust modeler initialization with proper sequencing
  const initializeModelerSafely = useCallback(async (
    containerElement: HTMLDivElement,
    propertiesPanelElement: HTMLDivElement,
    minimapElement: HTMLDivElement | null, // Add minimap container parameter
    modules: any[],
    moddleExtensions: any,
    skipInitialDiagram: boolean = false // New parameter to control initial diagram creation
  ) => {
    try {
      console.log('🚀 Starting BPMN modeler initialization...');

      // Create a new BPMN modeler instance
      const modelerConfig: any = {
        container: containerElement,
        propertiesPanel: {
          parent: propertiesPanelElement
        },
        additionalModules: modules,
        moddleExtensions
      };

      // Add minimap configuration if container is provided
      if (minimapElement) {
        modelerConfig.minimap = {
          parent: minimapElement
        };
      }

      const newModeler = new BpmnModeler(modelerConfig);

      // Critical: Wait for DOM to be fully ready and canvas to initialize
      console.log('⏳ Waiting for modeler DOM initialization...');
      await new Promise(resolve => setTimeout(resolve, 500));

      // Only force canvas initialization with diagram creation if needed
      if (!skipInitialDiagram) {
        console.log('🔧 Forcing canvas layer initialization with empty diagram...');
        try {
          await (newModeler as any).createDiagram();
          console.log('✅ Empty diagram created to initialize canvas');
        } catch (createErr) {
          console.warn('⚠️ Failed to create initial diagram, canvas will be initialized on first operation...', createErr);
        }
      } else {
        console.log('⏭️ Skipping initial diagram creation (will be handled by content import)');
      }

      // Verify canvas service is available
      const canvas = newModeler.get('canvas') as any;
      if (!canvas) {
        throw new Error('Canvas service not available - modeler initialization failed');
      }

      console.log('✅ Canvas initialization completed successfully');
      return newModeler;

    } catch (err) {
      console.error('❌ Error initializing BPMN modeler:', err);
      throw new Error(`Failed to initialize BPMN modeler: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  }, []);

  // Safe XML import with proper error handling and retries
  const importXmlSafely = useCallback(async (
    modeler: BpmnModeler, 
    xmlContent: string, 
    operationId: string = 'default'
  ) => {
    const MAX_RETRIES = 3;
    const currentRetryCount = retryCountRef.current.get(operationId) || 0;
    
    try {
      console.log(`🔄 Attempting XML import (attempt ${currentRetryCount + 1}/${MAX_RETRIES + 1})...`);
      
      // Verify modeler is ready before import
      const canvas = modeler.get('canvas') as any;
      if (!canvas) {
        throw new Error('Canvas service not available - modeler not ready');
      }

      // Check if canvas has basic functionality (don't require root-0 to exist yet)
      if (!canvas.addRootElement || typeof canvas.addRootElement !== 'function') {
        if (currentRetryCount < MAX_RETRIES) {
          console.warn(`⚠️ Canvas not fully ready, retrying in ${(currentRetryCount + 1) * 500}ms...`);
          retryCountRef.current.set(operationId, currentRetryCount + 1);
          await new Promise(resolve => setTimeout(resolve, (currentRetryCount + 1) * 500));
          return importXmlSafely(modeler, xmlContent, operationId);
        } else {
          retryCountRef.current.delete(operationId);
          throw new Error('Canvas not ready for operations after retries');
        }
      }

      // Perform XML import (this will create root-0 layer if needed)
      console.log('📄 Importing XML content...');
      await (modeler as any).importXML(xmlContent);
      console.log('✅ XML imported successfully');

      // Reset retry count on success
      retryCountRef.current.delete(operationId);

      // Zoom to fit with delay for proper rendering
      setTimeout(() => {
        try {
          const canvas = modeler.get('canvas') as any;
          if (canvas && typeof canvas.zoom === 'function') {
            canvas.zoom('fit-viewport');
            console.log('✅ Canvas zoomed to fit');
          }
        } catch (zoomErr) {
          console.warn('⚠️ Zoom failed:', zoomErr);
        }
      }, 300);

      return true;
    } catch (err) {
      console.error(`❌ XML import failed (attempt ${currentRetryCount + 1}):`, err);
      
      if (currentRetryCount < MAX_RETRIES) {
        console.log(`🔄 Retrying XML import in ${(currentRetryCount + 1) * 1000}ms...`);
        retryCountRef.current.set(operationId, currentRetryCount + 1);
        await new Promise(resolve => setTimeout(resolve, (currentRetryCount + 1) * 1000));
        return importXmlSafely(modeler, xmlContent, operationId);
      } else {
        retryCountRef.current.delete(operationId);
        throw new Error(`XML import failed after ${MAX_RETRIES + 1} attempts: ${err instanceof Error ? err.message : 'Unknown error'}`);
      }
    }
  }, []);

  // Safe diagram creation with proper error handling
  const createDiagramSafely = useCallback(async (modeler: BpmnModeler) => {
    try {
      console.log('🆕 Creating new diagram...');
      
      // Verify modeler is ready
      const canvas = modeler.get('canvas') as any;
      if (!canvas) {
        throw new Error('Canvas service not available - modeler not ready');
      }

      // Create new diagram (this will create root-0 layer automatically)
      await (modeler as any).createDiagram();
      console.log('✅ New diagram created successfully');

      // Get the XML for the new diagram
      const { xml: newXml } = await (modeler as any).saveXML({ format: true });
      
      // Zoom to fit with delay
      setTimeout(() => {
        try {
          const canvas = modeler.get('canvas') as any;
          if (canvas && typeof canvas.zoom === 'function') {
            canvas.zoom('fit-viewport');
            console.log('✅ Canvas zoomed to fit for new diagram');
          }
        } catch (zoomErr) {
          console.warn('⚠️ Zoom failed for new diagram:', zoomErr);
        }
      }, 300);

      return newXml || '';
    } catch (err) {
      console.error('❌ Error creating new diagram:', err);
      throw new Error(`Failed to create new diagram: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  }, []);

  // Check if modeler is properly initialized
  const isModelerReady = useCallback((modeler: BpmnModeler | null): boolean => {
    if (!modeler) return false;
    
    try {
      const canvas = modeler.get('canvas') as any;
      // Check for canvas service and basic functionality rather than specific layers
      return !!(canvas && canvas.addRootElement && typeof canvas.addRootElement === 'function');
    } catch (err) {
      return false;
    }
  }, []);

  // Safe zoom operation
  const zoomSafely = useCallback((modeler: BpmnModeler, zoomLevel: number | 'fit-viewport' = 'fit-viewport') => {
    try {
      const canvas = modeler.get('canvas') as any;
      if (canvas && typeof canvas.zoom === 'function') {
        canvas.zoom(zoomLevel);
        return true;
      }
      return false;
    } catch (err) {
      console.warn('⚠️ Zoom operation failed:', err);
      return false;
    }
  }, []);

  // Safe XML save operation
  const saveXmlSafely = useCallback(async (modeler: BpmnModeler, format: boolean = true): Promise<string> => {
    try {
      console.log('💾 Saving XML content...');
      
      // Verify modeler is ready
      if (!isModelerReady(modeler)) {
        throw new Error('Modeler not ready for save operation');
      }

      const result = await (modeler as any).saveXML({ format });
      console.log('✅ XML saved successfully');
      return result.xml || '';
    } catch (err) {
      console.error('❌ Error saving XML:', err);
      throw new Error(`Failed to save XML: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  }, [isModelerReady]);

  // Safe element selection
  const selectElementSafely = useCallback((modeler: BpmnModeler, elementId: string | null) => {
    try {
      if (!isModelerReady(modeler)) {
        console.warn('⚠️ Modeler not ready for element selection');
        return false;
      }

      const selection = modeler.get('selection') as any;
      if (!selection) {
        console.warn('⚠️ Selection service not available');
        return false;
      }

      if (elementId) {
        const elementRegistry = modeler.get('elementRegistry') as any;
        const element = elementRegistry.get(elementId);
        if (element) {
          selection.select(element);
          console.log(`✅ Element ${elementId} selected`);
          return true;
        } else {
          console.warn(`⚠️ Element ${elementId} not found`);
          return false;
        }
      } else {
        selection.select(null);
        console.log('✅ Selection cleared');
        return true;
      }
    } catch (err) {
      console.warn('⚠️ Element selection failed:', err);
      return false;
    }
  }, [isModelerReady]);

  // Safe modeler cleanup
  const cleanupModelerSafely = useCallback((modeler: BpmnModeler | null) => {
    try {
      if (modeler) {
        console.log('🧹 Cleaning up BPMN modeler...');
        (modeler as any).destroy?.();
        console.log('✅ Modeler cleanup completed');
        return true;
      }
      return false;
    } catch (err) {
      console.warn('⚠️ Modeler cleanup failed:', err);
      return false;
    }
  }, []);

  return {
    initializeModelerSafely,
    importXmlSafely,
    createDiagramSafely,
    isModelerReady,
    zoomSafely,
    saveXmlSafely,
    selectElementSafely,
    cleanupModelerSafely
  };
};

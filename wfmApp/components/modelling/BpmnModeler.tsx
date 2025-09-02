import React, { useEffect, useRef, useState, useCallback } from 'react';
import { processApiService } from '@/services/processApi';
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

import 'bpmn-js/dist/assets/diagram-js.css';
import 'bpmn-js/dist/assets/bpmn-font/css/bpmn.css';
import 'bpmn-js-properties-panel/dist/assets/properties-panel.css';
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
            console.log('🧹 Destroying previously active global BPMN modeler');
            try { existing.destroy(); } catch (e) { console.warn('Error destroying existing global modeler', e); }
            delete (window as any).__wfm_bpmn_modeler_active;
          }
        } catch (e) {
          console.warn('⚠️ Global pre-cleanup check failed:', e);
        }

        // Remove any dangling diagram DOM nodes not belonging to our containers
        try {
          const selectors = ['.djs-container', '.bpmn-js', '.diagram-js', '.djs-minimap', '.bpmn-js-minimap'];
          selectors.forEach(sel => {
            document.querySelectorAll(sel).forEach((el) => {
              if (!containerRef.current?.contains(el) && !propertiesPanelRef.current?.contains(el) && !minimapRef.current?.contains(el)) {
                // Only remove if element is outside our intended containers
                (el as HTMLElement).remove();
                console.log('🧹 Removed dangling diagram element', sel);
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
        
        // Listen for element selection changes
        eventBus.on('selection.changed', (event: any) => {
          const { newSelection } = event;
          if (newSelection && newSelection.length > 0) {
            setSelectedElement(newSelection[0]);
          } else {
            setSelectedElement(null);
          }
        });

        // Set up command stack listener for dirty state
        eventBus.on('commandStack.changed', () => {
          onDirtyChange(true);
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
          await importXmlSafely(newModeler, initialXml, 'initial-load');
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
          console.log('🧹 Cleaning up BPMN modeler (local)...');
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

  // Separate effect to handle XML changes without reinitializing modeler
  useEffect(() => {
    if (!modelerRef.current || !xml || xml === initialXml) return;

    const importXmlContent = async () => {
      try {
        setIsLoading(true);
        setError('');
        console.log('📥 Importing XML content...');
        
        await importXmlSafely(modelerRef.current!, xml, 'xml-change');
        onDirtyChange(false);
        console.log('✅ XML content imported successfully');
        
      } catch (err: any) {
        console.error('❌ Error importing XML content:', err);
        setError(`Failed to import diagram: ${err.message}`);
      } finally {
        setIsLoading(false);
      }
    };

    importXmlContent();
  }, [xml, initialXml, onDirtyChange, importXmlSafely]);


  // Toast notification helper
  const showToast = (message: string, type: 'success' | 'error' | 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000); // Auto-hide after 5 seconds
  };

  // Store BPMN in Redis temporarily
  const storeBpmnInRedis = async (xml: string, filename: string) => {
    try {
      const sessionId = sessionStorage.getItem('sessionId') || `session_${Date.now()}`;
      if (!sessionStorage.getItem('sessionId')) {
        sessionStorage.setItem('sessionId', sessionId);
      }

      const response = await processApiService.storeBpmnTemporarily({
        xml,
        filename,
        session_id: sessionId,
        overwrite: true,
      });

      if (response.data?.success) {
        showToast(`BPMN stored temporarily: ${response.data.message}`, 'success');
        return response.data;
      } else {
        throw new Error(response.error || 'Failed to store BPMN temporarily');
      }
    } catch (error: any) {
      console.warn('Temporary storage failed:', error);
      showToast(`Storage unavailable: ${error.message}`, 'error');
      // Fallback to sessionStorage
      const key = `bpmn_temp_${filename}_${Date.now()}`;
      sessionStorage.setItem(key, xml);
      return { key };
    }
  };

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
      const savedXml = await saveXmlSafely(modelerRef.current, true);
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
      console.log('🆕 Creating new diagram via button...');
      
      const newXml = await createDiagramSafely(modelerRef.current);
      setXml(newXml);
      onDirtyChange(false);
      showToast('New diagram created successfully', 'success');
      console.log('✅ New diagram created via button');
      
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
      const normalizedXml = validateAndNormalizeBpmnXml(xmlContent);

      // Set the new XML content, which will trigger the XML import effect
      setXml(normalizedXml);
      showToast('BPMN diagram imported successfully!', 'success');
      setShowImportDialog(false);
      setImportUrl('');
      setImportMethod('url');

    } catch (error) {
      console.error('Error importing BPMN from file:', error);
      setError(error instanceof Error ? error.message : 'Unknown error occurred');
    } finally {
      setIsImporting(false);
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
    setError('');

    try {
      console.log('Attempting to import from URL:', importUrl);
      
      let xmlContent = '';
      
      // Try direct fetch first (for same-origin or CORS-enabled URLs)
      try {
        console.log('Trying direct fetch...');
        const response = await fetch(importUrl, {
          method: 'GET',
          headers: {
            'Accept': 'application/xml, text/xml, text/plain, */*',
          },
          mode: 'cors',
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        xmlContent = await response.text();
        console.log('Direct fetch successful');
        
      } catch (directFetchError) {
        console.log('Direct fetch failed, trying proxy approach:', directFetchError);
        
        // Use our proxy API for CORS-blocked URLs
        try {
          const proxyUrl = `/api/proxy-bpmn?url=${encodeURIComponent(importUrl)}`;
          console.log('Using proxy URL:', proxyUrl);
          
          const proxyResponse = await fetch(proxyUrl, {
            method: 'GET',
            headers: {
              'Accept': 'application/xml, text/xml, text/plain, */*',
            },
          });

          if (!proxyResponse.ok) {
            const errorData = await proxyResponse.json().catch(() => ({ error: 'Unknown proxy error' }));
            throw new Error(`Proxy error: ${errorData.error || proxyResponse.statusText}`);
          }

          xmlContent = await proxyResponse.text();
          console.log('Proxy fetch successful');
          
        } catch (proxyError) {
          console.error('Proxy fetch also failed:', proxyError);
          throw new Error(`Unable to fetch BPMN file. ${proxyError instanceof Error ? proxyError.message : 'Please check the URL and ensure the server allows cross-origin requests.'}`);
        }
      }
      
      if (!xmlContent || xmlContent.trim().length === 0) {
        throw new Error('The URL returned empty content');
      }

      // Validate that the response looks like XML
      if (!xmlContent.trim().startsWith('<?xml') && !xmlContent.trim().startsWith('<')) {
        throw new Error('The URL did not return valid XML content');
      }

      console.log('Successfully fetched XML content, length:', xmlContent.length);

      // Validate and normalize the BPMN XML
      const normalizedXml = validateAndNormalizeBpmnXml(xmlContent);

      // Set the new XML content, which will trigger the XML import effect
      setXml(normalizedXml);
      await storeBpmnInRedis(normalizedXml, `imported_${Date.now()}.bpmn`);
      showToast('BPMN diagram imported successfully!', 'success');
      setShowImportDialog(false);
      setImportUrl('');

    } catch (error) {
      console.error('Error importing BPMN from URL:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      
      // Check if this is a file validity error or a system error
      if (errorMessage.includes('no diagram to display') || 
          errorMessage.includes('unparsable content') || 
          errorMessage.includes('unknown type') ||
          errorMessage.includes('Invalid BPMN') ||
          errorMessage.includes('empty content') ||
          errorMessage.includes('not return valid XML')) {
        // File validity errors - keep dialog open for retry
        showToast(`Invalid file: ${errorMessage}`, 'error');
        setError(`Please check your file and try again. ${errorMessage}`);
      } else {
        // System errors - these are more serious
        showToast(`Import failed: ${errorMessage}`, 'error');
        setError(`Import failed: ${errorMessage}`);
        // For system errors, close the dialog
        setShowImportDialog(false);
        setImportUrl('');
      }
    } finally {
      setIsImporting(false);
    }
  };

  const handleAutoImport = async (url: string, modelerInstance: BpmnModeler) => {
    if (!url.trim() || !modelerInstance) return;

    console.log('🔗 Auto-importing BPMN from URL:', url);
    
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

      console.log('🔗 Auto-import: BPMN XML fetched successfully, importing safely...');
      
      // Use our safe import function
      await importXmlSafely(modelerInstance, xmlData, 'auto-import');
      setXml(xmlData);
      
      console.log('✅ Auto-import: BPMN imported successfully');
      
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
            disabled={isLoading || !isDirty}
          >
            Save
          </button>
          <button
            onClick={handleExecuteWorkflow}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded text-sm font-medium"
            disabled={isLoading || !xml}
          >
            Execute Workflow
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
            className="bpmn-canvas-container w-full h-full border-r border-gray-200"
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

        {/* Properties Panel */}
        <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
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

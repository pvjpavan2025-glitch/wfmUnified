declare module 'bpmn-js/lib/Modeler' {
  export default class BpmnModeler {
    constructor(options: any);
    createDiagram(): Promise<void>;
    saveXML(options?: any): Promise<{ xml?: string }>;
    get(service: string): any;
    destroy(): void;
  }
}

declare module 'bpmn-js-properties-panel' {
  export const BpmnPropertiesPanelModule: any;
  export const BpmnPropertiesProviderModule: any;
  export const CamundaPlatformPropertiesProviderModule: any;
}

declare module 'bpmn-js-color-picker' {
  const ColorPickerModule: any;
  export default ColorPickerModule;
}

declare module 'camunda-bpmn-moddle/resources/camunda.json' {
  const camundaModdleDescriptor: any;
  export default camundaModdleDescriptor;
}

declare module 'diagram-js-minimap' {
  const MinimapModule: any;
  export default MinimapModule;
}

declare module 'bpmn-js/dist/assets/diagram-js.css';
declare module 'bpmn-js/dist/assets/bpmn-font/css/bpmn.css';
declare module '@bpmn-io/properties-panel/dist/assets/properties-panel.css';
declare module 'diagram-js-minimap/assets/diagram-js-minimap.css';

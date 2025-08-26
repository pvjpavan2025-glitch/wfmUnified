/**
 * Color provider for BPMN elements
 */
export default class ColorProvider {
  private _modeling: any;
  private _canvas: any;

  constructor(modeling: any, canvas: any) {
    this._modeling = modeling;
    this._canvas = canvas;
  }

  /**
   * Set fill color for element
   */
  setFillColor(element: any, color: string) {
    this._modeling.setColor(element, {
      fill: color
    });
  }

  /**
   * Set stroke color for element
   */
  setStrokeColor(element: any, color: string) {
    this._modeling.setColor(element, {
      stroke: color
    });
  }

  /**
   * Set both fill and stroke colors
   */
  setColors(element: any, colors: { fill?: string; stroke?: string }) {
    this._modeling.setColor(element, colors);
  }

  /**
   * Get current colors of element
   */
  getColors(element: any) {
    const businessObject = element.businessObject;
    const di = businessObject.di;
    
    return {
      fill: di && di.get('bioc:fill'),
      stroke: di && di.get('bioc:stroke')
    };
  }

  /**
   * Reset colors to default
   */
  resetColors(element: any) {
    this._modeling.setColor(element, {
      fill: undefined,
      stroke: undefined
    });
  }

  /**
   * Predefined color palette
   */
  getColorPalette() {
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
      { name: 'Teal', fill: '#E0F2F1', stroke: '#00796B' }
    ];
  }

  /**
   * Apply color theme to multiple elements
   */
  applyTheme(elements: any[], theme: string) {
    const themes = {
      'success': { fill: '#E8F5E8', stroke: '#388E3C' },
      'warning': { fill: '#FFF3E0', stroke: '#F57C00' },
      'error': { fill: '#FFEBEE', stroke: '#D32F2F' },
      'info': { fill: '#E3F2FD', stroke: '#1976D2' },
      'neutral': { fill: '#F5F5F5', stroke: '#757575' }
    };

    const colors = themes[theme as keyof typeof themes];
    if (colors) {
      elements.forEach(element => {
        this.setColors(element, colors);
      });
    }
  }
}

(ColorProvider as any).$inject = ['modeling', 'canvas'];

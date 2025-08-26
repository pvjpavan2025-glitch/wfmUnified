import {
  is,
  getBusinessObject
} from 'bpmn-js/lib/util/ModelUtil';

/**
 * Transaction boundaries provider for visualizing transaction scopes
 */
export default class TransactionBoundariesProvider {
  private _canvas: any;
  private _elementRegistry: any;
  private _graphicsFactory: any;
  private _eventBus: any;

  constructor(canvas: any, elementRegistry: any, graphicsFactory: any, eventBus: any) {
    this._canvas = canvas;
    this._elementRegistry = elementRegistry;
    this._graphicsFactory = graphicsFactory;
    this._eventBus = eventBus;

    this._eventBus.on('import.done', () => {
      this.showTransactionBoundaries();
    });
  }

  /**
   * Show transaction boundaries for all elements
   */
  showTransactionBoundaries() {
    const rootElement = this._canvas.getRootElement();
    this._processElement(rootElement);
  }

  /**
   * Hide all transaction boundaries
   */
  hideTransactionBoundaries() {
    const overlays = this._canvas.getContainer().querySelectorAll('.transaction-boundary');
    overlays.forEach((overlay: Element) => overlay.remove());
  }

  /**
   * Process element and its children for transaction boundaries
   */
  private _processElement(element: any) {
    if (this._isTransactionBoundary(element)) {
      this._addTransactionBoundary(element);
    }

    // Process children
    if (element.children) {
      element.children.forEach((child: any) => {
        this._processElement(child);
      });
    }
  }

  /**
   * Check if element represents a transaction boundary
   */
  private _isTransactionBoundary(element: any): boolean {
    const businessObject = getBusinessObject(element);
    
    // Transaction boundaries are typically:
    // - Subprocess with transaction behavior
    // - Activities with async before/after
    // - Service tasks with external implementation
    // - Call activities
    
    if (is(element, 'bpmn:Transaction')) {
      return true;
    }

    if (is(element, 'bpmn:SubProcess')) {
      return businessObject.triggeredByEvent || 
             businessObject.asyncBefore || 
             businessObject.asyncAfter;
    }

    if (is(element, 'bpmn:ServiceTask')) {
      return businessObject.asyncBefore || 
             businessObject.asyncAfter ||
             businessObject.implementation === 'external';
    }

    if (is(element, 'bpmn:CallActivity')) {
      return true;
    }

    if (is(element, 'bpmn:UserTask')) {
      return businessObject.asyncBefore || businessObject.asyncAfter;
    }

    return false;
  }

  /**
   * Add visual transaction boundary indicator
   */
  private _addTransactionBoundary(element: any) {
    const gfx = this._elementRegistry.getGraphics(element);
    if (!gfx) return;

    const boundaryType = this._getTransactionBoundaryType(element);
    const color = this._getBoundaryColor(boundaryType);

    // Create boundary overlay
    const boundary = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    boundary.setAttribute('class', 'transaction-boundary');
    boundary.setAttribute('x', '0');
    boundary.setAttribute('y', '0');
    boundary.setAttribute('width', element.width.toString());
    boundary.setAttribute('height', element.height.toString());
    boundary.setAttribute('fill', 'none');
    boundary.setAttribute('stroke', color);
    boundary.setAttribute('stroke-width', '2');
    boundary.setAttribute('stroke-dasharray', '5,5');
    boundary.setAttribute('pointer-events', 'none');

    // Add to graphics
    gfx.appendChild(boundary);

    // Add transaction type indicator
    this._addTransactionTypeIndicator(element, boundaryType, color);
  }

  /**
   * Get transaction boundary type
   */
  private _getTransactionBoundaryType(element: any): string {
    const businessObject = getBusinessObject(element);

    if (is(element, 'bpmn:Transaction')) {
      return 'transaction';
    }

    if (businessObject.asyncBefore && businessObject.asyncAfter) {
      return 'async-both';
    }

    if (businessObject.asyncBefore) {
      return 'async-before';
    }

    if (businessObject.asyncAfter) {
      return 'async-after';
    }

    if (is(element, 'bpmn:CallActivity')) {
      return 'call-activity';
    }

    if (is(element, 'bpmn:ServiceTask') && businessObject.implementation === 'external') {
      return 'external-task';
    }

    if (is(element, 'bpmn:SubProcess') && businessObject.triggeredByEvent) {
      return 'event-subprocess';
    }

    return 'default';
  }

  /**
   * Get color for boundary type
   */
  private _getBoundaryColor(type: string): string {
    const colors = {
      'transaction': '#FF6B6B',
      'async-both': '#4ECDC4',
      'async-before': '#45B7D1',
      'async-after': '#96CEB4',
      'call-activity': '#FFEAA7',
      'external-task': '#DDA0DD',
      'event-subprocess': '#98D8C8',
      'default': '#74B9FF'
    };

    return colors[type as keyof typeof colors] || colors.default;
  }

  /**
   * Add transaction type indicator
   */
  private _addTransactionTypeIndicator(element: any, type: string, color: string) {
    const gfx = this._elementRegistry.getGraphics(element);
    if (!gfx) return;

    // Create indicator circle
    const indicator = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    indicator.setAttribute('class', 'transaction-indicator');
    indicator.setAttribute('cx', (element.width - 10).toString());
    indicator.setAttribute('cy', '10');
    indicator.setAttribute('r', '6');
    indicator.setAttribute('fill', color);
    indicator.setAttribute('stroke', '#fff');
    indicator.setAttribute('stroke-width', '1');

    // Add tooltip
    const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
    title.textContent = this._getTransactionTypeLabel(type);
    indicator.appendChild(title);

    gfx.appendChild(indicator);

    // Add type abbreviation text
    const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    text.setAttribute('x', (element.width - 10).toString());
    text.setAttribute('y', '14');
    text.setAttribute('text-anchor', 'middle');
    text.setAttribute('font-size', '8');
    text.setAttribute('font-weight', 'bold');
    text.setAttribute('fill', '#fff');
    text.setAttribute('pointer-events', 'none');
    text.textContent = this._getTransactionTypeAbbreviation(type);

    gfx.appendChild(text);
  }

  /**
   * Get human-readable label for transaction type
   */
  private _getTransactionTypeLabel(type: string): string {
    const labels = {
      'transaction': 'Transaction Scope',
      'async-both': 'Async Before & After',
      'async-before': 'Async Before',
      'async-after': 'Async After',
      'call-activity': 'Call Activity',
      'external-task': 'External Task',
      'event-subprocess': 'Event Subprocess',
      'default': 'Transaction Boundary'
    };

    return labels[type as keyof typeof labels] || labels.default;
  }

  /**
   * Get abbreviation for transaction type
   */
  private _getTransactionTypeAbbreviation(type: string): string {
    const abbreviations = {
      'transaction': 'TX',
      'async-both': 'AB',
      'async-before': 'A<',
      'async-after': 'A>',
      'call-activity': 'CA',
      'external-task': 'EX',
      'event-subprocess': 'ES',
      'default': 'TB'
    };

    return abbreviations[type as keyof typeof abbreviations] || abbreviations.default;
  }

  /**
   * Toggle transaction boundaries visibility
   */
  toggleTransactionBoundaries() {
    const existing = this._canvas.getContainer().querySelectorAll('.transaction-boundary');
    if (existing.length > 0) {
      this.hideTransactionBoundaries();
    } else {
      this.showTransactionBoundaries();
    }
  }

  /**
   * Get transaction boundary statistics
   */
  getTransactionStatistics() {
    const stats = {
      total: 0,
      byType: {} as Record<string, number>
    };

    const rootElement = this._canvas.getRootElement();
    this._collectStats(rootElement, stats);

    return stats;
  }

  /**
   * Collect statistics recursively
   */
  private _collectStats(element: any, stats: any) {
    if (this._isTransactionBoundary(element)) {
      const type = this._getTransactionBoundaryType(element);
      stats.total++;
      stats.byType[type] = (stats.byType[type] || 0) + 1;
    }

    if (element.children) {
      element.children.forEach((child: any) => {
        this._collectStats(child, stats);
      });
    }
  }
}

(TransactionBoundariesProvider as any).$inject = ['canvas', 'elementRegistry', 'graphicsFactory', 'eventBus'];

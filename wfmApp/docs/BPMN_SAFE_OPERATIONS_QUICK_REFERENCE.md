# BPMN Modeler Safe Operations - Quick Reference

## Import the Hook

```typescript
import { useBpmnModelerSafe } from '@/hooks/useBpmnModelerSafe';

const {
  initializeModelerSafely,
  importXmlSafely,
  createDiagramSafely,
  isModelerReady,
  zoomSafely
} = useBpmnModelerSafe();
```

## Initialize Modeler

```typescript
const modeler = await initializeModelerSafely(
  containerRef.current!,
  propertiesPanelRef.current!,
  [BpmnPropertiesPanelModule, ColorPickerModule, ...],
  { camunda: camundaModdleDescriptor }
);
```

## Import XML Safely

```typescript
// With operation ID for tracking
await importXmlSafely(modeler, xmlContent, 'user-import');

// Will retry up to 3 times with progressive delays
// Verifies canvas layers before import
// Handles zoom-to-fit automatically
```

## Create New Diagram

```typescript
const newXml = await createDiagramSafely(modeler);
setXml(newXml);
```

## Check if Modeler is Ready

```typescript
if (isModelerReady(modeler)) {
  // Safe to perform operations
} else {
  // Wait or show loading state
}
```

## Safe Zoom Operations

```typescript
// Zoom to fit viewport
zoomSafely(modeler, 'fit-viewport');

// Zoom to specific level
zoomSafely(modeler, 1.5);
```

## Error Handling Pattern

```typescript
try {
  await importXmlSafely(modeler, xml, 'operation-id');
  console.log('✅ Success');
} catch (error) {
  console.error('❌ Failed after retries:', error.message);
  setError(`Import failed: ${error.message}`);
}
```

## Common Operation IDs

- `'initial-load'` - Loading initial XML on component mount
- `'user-import'` - User-triggered import from file/URL
- `'auto-import'` - Automatic import from URL parameter
- `'xml-change'` - Programmatic XML change via state
- `'template-load'` - Loading from template selection

## Console Log Patterns

Look for these log messages to track operations:

```
🚀 Starting BPMN modeler initialization...
✅ Canvas layers initialized successfully
🔄 Attempting XML import (attempt 1/4)...
✅ XML imported successfully
⚠️ Canvas not ready, retrying in 500ms...
❌ XML import failed after retries
```

## Quick Troubleshooting

| Error Pattern | Likely Cause | Solution |
|---------------|--------------|----------|
| `Canvas layers failed to initialize` | DOM not ready | Increase initialization delay |
| `XML import failed after retries` | Invalid XML | Validate XML content |
| `Canvas not ready for diagram creation` | Timing issue | Check modeler readiness first |
| `root-0 undefined` | Legacy code | Use safe operations |

Remember: Always use the safe operations instead of direct BPMN.js methods!

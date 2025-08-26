import {
  is,
  getBusinessObject
} from 'bpmn-js/lib/util/ModelUtil';

import {
  isTextFieldEntryEdited,
  isToggleSwitchEntryEdited,
  isSelectEntryEdited,
  TextFieldEntry,
  ToggleSwitchEntry,
  SelectEntry
} from '@bpmn-io/properties-panel';

const LOW_PRIORITY = 500;

/**
 * Custom properties provider for enhanced BPMN element properties
 */
export default function CustomPropertiesProvider(propertiesPanel: any, injector: any) {
  this.getGroups = function(element: any) {
    return function(groups: any[]) {
      // Add custom groups for different element types
      if (is(element, 'bpmn:Task')) {
        groups.push(createTaskGroup(element, injector));
      }

      if (is(element, 'bpmn:ServiceTask')) {
        groups.push(createServiceTaskGroup(element, injector));
      }

      if (is(element, 'bpmn:UserTask')) {
        groups.push(createUserTaskGroup(element, injector));
      }

      if (is(element, 'bpmn:ScriptTask')) {
        groups.push(createScriptTaskGroup(element, injector));
      }

      if (is(element, 'bpmn:BusinessRuleTask')) {
        groups.push(createBusinessRuleTaskGroup(element, injector));
      }

      if (is(element, 'bpmn:SendTask')) {
        groups.push(createSendTaskGroup(element, injector));
      }

      if (is(element, 'bpmn:ReceiveTask')) {
        groups.push(createReceiveTaskGroup(element, injector));
      }

      if (is(element, 'bpmn:ManualTask')) {
        groups.push(createManualTaskGroup(element, injector));
      }

      // Add execution group for all executable elements
      if (isExecutable(element)) {
        groups.push(createExecutionGroup(element, injector));
      }

      // Add appearance group for visual customization
      groups.push(createAppearanceGroup(element, injector));

      return groups;
    };
  };

  propertiesPanel.registerProvider(LOW_PRIORITY, this);
}

// Task-specific property groups
function createTaskGroup(element: any, injector: any) {
  return {
    id: 'task',
    label: 'Task Properties',
    entries: [
      {
        id: 'task-name',
        component: TextFieldEntry,
        isEdited: isTextFieldEntryEdited,
        props: {
          element,
          id: 'task-name',
          label: 'Name',
          getValue: () => element.businessObject.name || '',
          setValue: (value: string) => {
            const modeling = injector.get('modeling');
            modeling.updateProperties(element, { name: value });
          }
        }
      },
      {
        id: 'task-documentation',
        component: TextFieldEntry,
        isEdited: isTextFieldEntryEdited,
        props: {
          element,
          id: 'task-documentation',
          label: 'Documentation',
          getValue: () => {
            const documentation = element.businessObject.documentation;
            return documentation && documentation[0] ? documentation[0].text : '';
          },
          setValue: (value: string) => {
            const modeling = injector.get('modeling');
            const bpmnFactory = injector.get('bpmnFactory');
            
            const documentation = bpmnFactory.create('bpmn:Documentation', {
              text: value
            });
            
            modeling.updateProperties(element, {
              documentation: [documentation]
            });
          }
        }
      }
    ]
  };
}

function createServiceTaskGroup(element: any, injector: any) {
  return {
    id: 'service-task',
    label: 'Service Task',
    entries: [
      {
        id: 'service-implementation',
        component: SelectEntry,
        isEdited: isSelectEntryEdited,
        props: {
          element,
          id: 'service-implementation',
          label: 'Implementation',
          getValue: () => element.businessObject.implementation || 'webService',
          setValue: (value: string) => {
            const modeling = injector.get('modeling');
            modeling.updateProperties(element, { implementation: value });
          },
          getOptions: () => [
            { label: 'Web Service', value: 'webService' },
            { label: 'Java Class', value: 'javaClass' },
            { label: 'Expression', value: 'expression' },
            { label: 'Delegate Expression', value: 'delegateExpression' },
            { label: 'External', value: 'external' },
            { label: 'Connector', value: 'connector' }
          ]
        }
      },
      {
        id: 'service-topic',
        component: TextFieldEntry,
        isEdited: isTextFieldEntryEdited,
        props: {
          element,
          id: 'service-topic',
          label: 'Topic',
          getValue: () => element.businessObject.topic || '',
          setValue: (value: string) => {
            const modeling = injector.get('modeling');
            modeling.updateProperties(element, { topic: value });
          }
        }
      }
    ]
  };
}

function createUserTaskGroup(element: any, injector: any) {
  return {
    id: 'user-task',
    label: 'User Task',
    entries: [
      {
        id: 'user-assignee',
        component: TextFieldEntry,
        isEdited: isTextFieldEntryEdited,
        props: {
          element,
          id: 'user-assignee',
          label: 'Assignee',
          getValue: () => element.businessObject.assignee || '',
          setValue: (value: string) => {
            const modeling = injector.get('modeling');
            modeling.updateProperties(element, { assignee: value });
          }
        }
      },
      {
        id: 'user-candidate-users',
        component: TextFieldEntry,
        isEdited: isTextFieldEntryEdited,
        props: {
          element,
          id: 'user-candidate-users',
          label: 'Candidate Users',
          getValue: () => element.businessObject.candidateUsers || '',
          setValue: (value: string) => {
            const modeling = injector.get('modeling');
            modeling.updateProperties(element, { candidateUsers: value });
          }
        }
      },
      {
        id: 'user-candidate-groups',
        component: TextFieldEntry,
        isEdited: isTextFieldEntryEdited,
        props: {
          element,
          id: 'user-candidate-groups',
          label: 'Candidate Groups',
          getValue: () => element.businessObject.candidateGroups || '',
          setValue: (value: string) => {
            const modeling = injector.get('modeling');
            modeling.updateProperties(element, { candidateGroups: value });
          }
        }
      },
      {
        id: 'user-due-date',
        component: TextFieldEntry,
        isEdited: isTextFieldEntryEdited,
        props: {
          element,
          id: 'user-due-date',
          label: 'Due Date',
          getValue: () => element.businessObject.dueDate || '',
          setValue: (value: string) => {
            const modeling = injector.get('modeling');
            modeling.updateProperties(element, { dueDate: value });
          }
        }
      },
      {
        id: 'user-priority',
        component: TextFieldEntry,
        isEdited: isTextFieldEntryEdited,
        props: {
          element,
          id: 'user-priority',
          label: 'Priority',
          getValue: () => element.businessObject.priority || '',
          setValue: (value: string) => {
            const modeling = injector.get('modeling');
            modeling.updateProperties(element, { priority: value });
          }
        }
      }
    ]
  };
}

function createScriptTaskGroup(element: any, injector: any) {
  return {
    id: 'script-task',
    label: 'Script Task',
    entries: [
      {
        id: 'script-format',
        component: SelectEntry,
        isEdited: isSelectEntryEdited,
        props: {
          element,
          id: 'script-format',
          label: 'Script Format',
          getValue: () => element.businessObject.scriptFormat || 'javascript',
          setValue: (value: string) => {
            const modeling = injector.get('modeling');
            modeling.updateProperties(element, { scriptFormat: value });
          },
          getOptions: () => [
            { label: 'JavaScript', value: 'javascript' },
            { label: 'Python', value: 'python' },
            { label: 'Groovy', value: 'groovy' },
            { label: 'JRuby', value: 'jruby' },
            { label: 'Jython', value: 'jython' }
          ]
        }
      },
      {
        id: 'script-value',
        component: TextFieldEntry,
        isEdited: isTextFieldEntryEdited,
        props: {
          element,
          id: 'script-value',
          label: 'Script',
          getValue: () => element.businessObject.script || '',
          setValue: (value: string) => {
            const modeling = injector.get('modeling');
            modeling.updateProperties(element, { script: value });
          }
        }
      },
      {
        id: 'script-result-variable',
        component: TextFieldEntry,
        isEdited: isTextFieldEntryEdited,
        props: {
          element,
          id: 'script-result-variable',
          label: 'Result Variable',
          getValue: () => element.businessObject.resultVariable || '',
          setValue: (value: string) => {
            const modeling = injector.get('modeling');
            modeling.updateProperties(element, { resultVariable: value });
          }
        }
      }
    ]
  };
}

function createBusinessRuleTaskGroup(element: any, injector: any) {
  return {
    id: 'business-rule-task',
    label: 'Business Rule Task',
    entries: [
      {
        id: 'decision-ref',
        component: TextFieldEntry,
        isEdited: isTextFieldEntryEdited,
        props: {
          element,
          id: 'decision-ref',
          label: 'Decision Reference',
          getValue: () => element.businessObject.decisionRef || '',
          setValue: (value: string) => {
            const modeling = injector.get('modeling');
            modeling.updateProperties(element, { decisionRef: value });
          }
        }
      },
      {
        id: 'decision-ref-binding',
        component: SelectEntry,
        isEdited: isSelectEntryEdited,
        props: {
          element,
          id: 'decision-ref-binding',
          label: 'Binding',
          getValue: () => element.businessObject.decisionRefBinding || 'latest',
          setValue: (value: string) => {
            const modeling = injector.get('modeling');
            modeling.updateProperties(element, { decisionRefBinding: value });
          },
          getOptions: () => [
            { label: 'Latest', value: 'latest' },
            { label: 'Deployment', value: 'deployment' },
            { label: 'Version', value: 'version' }
          ]
        }
      }
    ]
  };
}

function createSendTaskGroup(element: any, injector: any) {
  return {
    id: 'send-task',
    label: 'Send Task',
    entries: [
      {
        id: 'message-ref',
        component: TextFieldEntry,
        isEdited: isTextFieldEntryEdited,
        props: {
          element,
          id: 'message-ref',
          label: 'Message',
          getValue: () => element.businessObject.messageRef || '',
          setValue: (value: string) => {
            const modeling = injector.get('modeling');
            modeling.updateProperties(element, { messageRef: value });
          }
        }
      }
    ]
  };
}

function createReceiveTaskGroup(element: any, injector: any) {
  return {
    id: 'receive-task',
    label: 'Receive Task',
    entries: [
      {
        id: 'message-ref',
        component: TextFieldEntry,
        isEdited: isTextFieldEntryEdited,
        props: {
          element,
          id: 'message-ref',
          label: 'Message',
          getValue: () => element.businessObject.messageRef || '',
          setValue: (value: string) => {
            const modeling = injector.get('modeling');
            modeling.updateProperties(element, { messageRef: value });
          }
        }
      },
      {
        id: 'instantiate',
        component: ToggleSwitchEntry,
        isEdited: isToggleSwitchEntryEdited,
        props: {
          element,
          id: 'instantiate',
          label: 'Instantiate',
          getValue: () => element.businessObject.instantiate || false,
          setValue: (value: boolean) => {
            const modeling = injector.get('modeling');
            modeling.updateProperties(element, { instantiate: value });
          }
        }
      }
    ]
  };
}

function createManualTaskGroup(element: any, injector: any) {
  return {
    id: 'manual-task',
    label: 'Manual Task',
    entries: [
      {
        id: 'manual-instructions',
        component: TextFieldEntry,
        isEdited: isTextFieldEntryEdited,
        props: {
          element,
          id: 'manual-instructions',
          label: 'Instructions',
          getValue: () => element.businessObject.instructions || '',
          setValue: (value: string) => {
            const modeling = injector.get('modeling');
            modeling.updateProperties(element, { instructions: value });
          }
        }
      }
    ]
  };
}

function createExecutionGroup(element: any, injector: any) {
  return {
    id: 'execution',
    label: 'Execution',
    entries: [
      {
        id: 'async-before',
        component: ToggleSwitchEntry,
        isEdited: isToggleSwitchEntryEdited,
        props: {
          element,
          id: 'async-before',
          label: 'Asynchronous Before',
          getValue: () => element.businessObject.asyncBefore || false,
          setValue: (value: boolean) => {
            const modeling = injector.get('modeling');
            modeling.updateProperties(element, { asyncBefore: value });
          }
        }
      },
      {
        id: 'async-after',
        component: ToggleSwitchEntry,
        isEdited: isToggleSwitchEntryEdited,
        props: {
          element,
          id: 'async-after',
          label: 'Asynchronous After',
          getValue: () => element.businessObject.asyncAfter || false,
          setValue: (value: boolean) => {
            const modeling = injector.get('modeling');
            modeling.updateProperties(element, { asyncAfter: value });
          }
        }
      },
      {
        id: 'exclusive',
        component: ToggleSwitchEntry,
        isEdited: isToggleSwitchEntryEdited,
        props: {
          element,
          id: 'exclusive',
          label: 'Exclusive',
          getValue: () => element.businessObject.exclusive !== false,
          setValue: (value: boolean) => {
            const modeling = injector.get('modeling');
            modeling.updateProperties(element, { exclusive: value });
          }
        }
      }
    ]
  };
}

function createAppearanceGroup(element: any, injector: any) {
  return {
    id: 'appearance',
    label: 'Appearance',
    entries: [
      {
        id: 'color-fill',
        component: TextFieldEntry,
        isEdited: isTextFieldEntryEdited,
        props: {
          element,
          id: 'color-fill',
          label: 'Fill Color',
          getValue: () => {
            const di = element.businessObject.di;
            return di && di.get('bioc:fill') || '';
          },
          setValue: (value: string) => {
            const modeling = injector.get('modeling');
            const di = element.businessObject.di;
            if (di) {
              modeling.updateProperties(element, {});
              di.set('bioc:fill', value);
            }
          }
        }
      },
      {
        id: 'color-stroke',
        component: TextFieldEntry,
        isEdited: isTextFieldEntryEdited,
        props: {
          element,
          id: 'color-stroke',
          label: 'Stroke Color',
          getValue: () => {
            const di = element.businessObject.di;
            return di && di.get('bioc:stroke') || '';
          },
          setValue: (value: string) => {
            const modeling = injector.get('modeling');
            const di = element.businessObject.di;
            if (di) {
              modeling.updateProperties(element, {});
              di.set('bioc:stroke', value);
            }
          }
        }
      }
    ]
  };
}

function isExecutable(element: any) {
  return is(element, 'bpmn:Task') ||
         is(element, 'bpmn:ServiceTask') ||
         is(element, 'bpmn:UserTask') ||
         is(element, 'bpmn:ScriptTask') ||
         is(element, 'bpmn:BusinessRuleTask') ||
         is(element, 'bpmn:SendTask') ||
         is(element, 'bpmn:ReceiveTask') ||
         is(element, 'bpmn:ManualTask') ||
         is(element, 'bpmn:CallActivity') ||
         is(element, 'bpmn:SubProcess');
}

(CustomPropertiesProvider as any).$inject = ['propertiesPanel', 'injector'];

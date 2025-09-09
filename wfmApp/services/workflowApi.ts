/**
 * Workflow API service for managing workflow instances and execution.
 */

const WORKFLOW_INSTANCE_SERVICE_URL = process.env.NEXT_PUBLIC_BPMN_BACKEND_URL || 'http://localhost:8100';
const WORKFLOW_EXECUTION_SERVICE_URL = process.env.NEXT_PUBLIC_BPMN_BACKEND_URL || 'http://localhost:8100';

export interface WorkflowInstanceCreate {
  name: string;
  description?: string;
  workflow_definition_id: string;
  bpmn_xml: string;
  input_data: Record<string, any>;
  created_by: string;
}

export interface WorkflowExecutionRequest {
  bpmn_xml: string;
  workflow_name: string;
  workflow_description?: string;
  input_data: Record<string, any>;
  created_by: string;
}

export interface WorkflowInstance {
  id: string;
  name: string;
  description?: string;
  workflow_definition_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'suspended' | 'paused';
  current_step?: string;
  input_data: Record<string, any>;
  execution_data: Record<string, any>;
  error_message?: string;
  created_at: string;
  updated_at: string;
  created_by: string;
  updated_by?: string;
  started_at?: string;
  completed_at?: string;
  steps: WorkflowStep[];
  execution_logs: WorkflowExecutionLog[];
}

export interface WorkflowStep {
  step_id: string;
  name: string;
  step_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  started_at?: string;
  completed_at?: string;
  input_data: Record<string, any>;
  output_data: Record<string, any>;
  error_message?: string;
  assigned_to?: string;
}

export interface WorkflowExecutionLog {
  timestamp: string;
  level: string;
  message: string;
  step_id?: string;
  data: Record<string, any>;
}

class WorkflowApiService {
  /**
   * Create a new workflow instance
   */
  async createWorkflowInstance(data: WorkflowInstanceCreate): Promise<WorkflowInstance> {
    try {
      const response = await fetch(`${WORKFLOW_INSTANCE_SERVICE_URL}/api/v1/instances`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating workflow instance:', error);
      throw new Error(`Failed to create workflow instance: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Create and execute a workflow in one step
   */
  async createAndExecuteWorkflow(data: WorkflowExecutionRequest): Promise<{ instance: WorkflowInstance; execution: any }> {
    try {
      // First create the workflow instance
      const instance = await this.createWorkflowInstance({
        name: data.workflow_name,
        description: data.workflow_description,
        workflow_definition_id: `def_${Date.now()}`, // Generate a temporary ID
        bpmn_xml: data.bpmn_xml,
        input_data: data.input_data,
        created_by: data.created_by,
      });

      // Then execute it
      const execution = await this.executeWorkflow(instance.id, data.input_data);

      return { instance, execution };
    } catch (error) {
      console.error('Error creating and executing workflow:', error);
      throw new Error(`Failed to create and execute workflow: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Execute a workflow instance
   */
  async executeWorkflow(instanceId: string, inputData: Record<string, any> = {}): Promise<any> {
    try {
      const response = await fetch(`${WORKFLOW_INSTANCE_SERVICE_URL}/api/v1/instances/${instanceId}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          workflow_instance_id: instanceId,
          input_data: inputData,
          auto_start: true,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error executing workflow:', error);
      throw new Error(`Failed to execute workflow: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Continue workflow execution (for user tasks)
   */
  async continueWorkflow(instanceId: string, taskData: Record<string, any> = {}): Promise<any> {
    try {
      const response = await fetch(`${WORKFLOW_EXECUTION_SERVICE_URL}/api/v1/workflow-execution/instances/${instanceId}/continue`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ task_data: taskData }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error continuing workflow:', error);
      throw new Error(`Failed to continue workflow: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Cancel a workflow execution
   */
  async cancelWorkflow(instanceId: string, cancelledBy: string): Promise<void> {
    try {
      const response = await fetch(`${WORKFLOW_EXECUTION_SERVICE_URL}/api/v1/workflow-execution/instances/${instanceId}/cancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ cancelled_by: cancelledBy }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error cancelling workflow:', error);
      throw new Error(`Failed to cancel workflow: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get workflow instance details
   */
  async getWorkflowInstance(instanceId: string): Promise<WorkflowInstance> {
    try {
      const response = await fetch(`${WORKFLOW_INSTANCE_SERVICE_URL}/api/v1/instances/${instanceId}`);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching workflow instance:', error);
      throw new Error(`Failed to fetch workflow instance: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get list of workflow instances
   */
  async getWorkflowInstances(params: {
    skip?: number;
    limit?: number;
    status?: string;
    created_by?: string;
  } = {}): Promise<WorkflowInstance[]> {
    try {
      const searchParams = new URLSearchParams();
      
      if (params.skip !== undefined) searchParams.append('skip', params.skip.toString());
      if (params.limit !== undefined) searchParams.append('limit', params.limit.toString());
      if (params.status) searchParams.append('status', params.status);
      if (params.created_by) searchParams.append('created_by', params.created_by);

      const response = await fetch(`${WORKFLOW_INSTANCE_SERVICE_URL}/api/v1/instances?${searchParams}`);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching workflow instances:', error);
      throw new Error(`Failed to fetch workflow instances: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get workflow execution status
   */
  async getWorkflowStatus(instanceId: string): Promise<any> {
    try {
      const response = await fetch(`${WORKFLOW_EXECUTION_SERVICE_URL}/api/v1/workflow-execution/instances/${instanceId}/status`);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching workflow status:', error);
      throw new Error(`Failed to fetch workflow status: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Update workflow step status
   */
  async updateStepStatus(
    instanceId: string,
    stepId: string,
    status: string,
    outputData?: Record<string, any>,
    errorMessage?: string
  ): Promise<void> {
    try {
      const response = await fetch(`${WORKFLOW_INSTANCE_SERVICE_URL}/api/v1/instances/${instanceId}/steps/${stepId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          status,
          output_data: outputData,
          error_message: errorMessage,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error updating step status:', error);
      throw new Error(`Failed to update step status: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }
}

export const workflowApiService = new WorkflowApiService();

/**
 * Frontend API service for process management
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_BPMN_BACKEND_URL || 'http://localhost:8100';

// Types
export interface Process {
  id: string;
  name: string;
  description: string;
  bpmn_xml: string;
  process_id: string;
  process_name: string;
  version: string;
  category: string;
  tags: string[];
  metadata: Record<string, any>;
  status: string;
  created_by: string;
  tenant_id: string;
  created_at: string;
  updated_at: string;
  task_count: number;
  gateway_count: number;
  event_count: number;
  flow_count: number;
  complexity_score: number;
  estimated_duration: number;
  task_types: string[];
  gateway_types: string[];
  event_types: string[];
}

export interface ProcessCreate {
  name: string;
  description?: string;
  bpmn_xml: string;
  version: string;
  category?: string;
  tags?: string[];
  metadata?: Record<string, any>;
  created_by: string;
  tenant_id: string;
}

export interface ProcessUpdate {
  name?: string;
  description?: string;
  bpmn_xml?: string;
  version?: string;
  category?: string;
  tags?: string[];
  metadata?: Record<string, any>;
  status?: string;
}

export interface ProcessInstance {
  id: string;
  process_id: string;
  process_name: string;
  process_version: string;
  input_data: Record<string, any>;
  output_data?: Record<string, any>;
  status: string;
  started_by: string;
  tenant_id: string;
  started_at: string;
  completed_at?: string;
}

export interface ProcessInstanceCreate {
  process_id: string;
  input_data?: Record<string, any>;
  started_by?: string;
  tenant_id?: string;
}

export interface Template {
  id: string;
  name: string;
  description: string;
  bpmn_xml: string;
  category: string;
  tags: string[];
  metadata: Record<string, any>;
  created_by: string;
  tenant_id: string;
  created_at: string;
  updated_at: string;
  usage_count: number;
}

export interface TemplateCreate {
  name: string;
  description?: string;
  bpmn_xml: string;
  category?: string;
  tags?: string[];
  metadata?: Record<string, any>;
  created_by: string;
  tenant_id: string;
}

export interface ApiResponse<T> {
  data?: T;
  message?: string;
  error?: string;
}

// API Service Class
class ProcessApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      return { error: error instanceof Error ? error.message : 'Unknown error occurred' };
    }
  }

  // Process Management
  async createProcess(processData: ProcessCreate): Promise<ApiResponse<Process>> {
    return this.request<Process>('/api/v1/enhanced-workflows/processes', {
      method: 'POST',
      body: JSON.stringify(processData),
    });
  }

  async listProcesses(params?: {
    skip?: number;
    limit?: number;
    category?: string;
    status?: string;
    tenant_id?: string;
  }): Promise<ApiResponse<{ processes: Process[]; total: number; skip: number; limit: number }>> {
    const searchParams = new URLSearchParams();
    if (params?.skip) searchParams.append('skip', params.skip.toString());
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.category) searchParams.append('category', params.category);
    if (params?.status) searchParams.append('status', params.status);
    if (params?.tenant_id) searchParams.append('tenant_id', params.tenant_id);

    const queryString = searchParams.toString();
    const endpoint = `/api/v1/enhanced-workflows/processes${queryString ? `?${queryString}` : ''}`;
    
    return this.request<{ processes: Process[]; total: number; skip: number; limit: number }>(endpoint);
  }

  async getProcess(processId: string): Promise<ApiResponse<Process>> {
    return this.request<Process>(`/api/v1/enhanced-workflows/processes/${processId}`);
  }

  async updateProcess(processId: string, processData: ProcessUpdate): Promise<ApiResponse<Process>> {
    return this.request<Process>(`/api/v1/enhanced-workflows/processes/${processId}`, {
      method: 'PUT',
      body: JSON.stringify(processData),
    });
  }

  async deleteProcess(processId: string): Promise<ApiResponse<{ message: string }>> {
    return this.request<{ message: string }>(`/api/v1/enhanced-workflows/processes/${processId}`, {
      method: 'DELETE',
    });
  }

  // Process Instances
  async createProcessInstance(
    processId: string,
    instanceData: ProcessInstanceCreate
  ): Promise<ApiResponse<ProcessInstance>> {
    return this.request<ProcessInstance>(`/api/v1/enhanced-workflows/processes/${processId}/instances`, {
      method: 'POST',
      body: JSON.stringify(instanceData),
    });
  }

  async listProcessInstances(
    processId: string,
    params?: {
      skip?: number;
      limit?: number;
      status?: string;
      tenant_id?: string;
    }
  ): Promise<ApiResponse<{ instances: ProcessInstance[]; total: number; skip: number; limit: number; process_id: string }>> {
    const searchParams = new URLSearchParams();
    if (params?.skip) searchParams.append('skip', params.skip.toString());
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.status) searchParams.append('status', params.status);
    if (params?.tenant_id) searchParams.append('tenant_id', params.tenant_id);

    const queryString = searchParams.toString();
    const endpoint = `/api/v1/enhanced-workflows/processes/${processId}/instances${queryString ? `?${queryString}` : ''}`;
    
    return this.request<{ instances: ProcessInstance[]; total: number; skip: number; limit: number; process_id: string }>(endpoint);
  }

  async getProcessInstance(instanceId: string): Promise<ApiResponse<ProcessInstance>> {
    return this.request<ProcessInstance>(`/api/v1/enhanced-workflows/instances/${instanceId}`);
  }

  async executeProcessInstance(instanceId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/v1/enhanced-workflows/instances/${instanceId}/execute`, {
      method: 'POST',
    });
  }

  async deleteProcessInstance(instanceId: string): Promise<ApiResponse<{ message: string }>> {
    return this.request<{ message: string }>(`/api/v1/enhanced-workflows/instances/${instanceId}`, {
      method: 'DELETE',
    });
  }

  // Templates
  async createTemplateFromProcess(
    processId: string,
    templateData: Record<string, any>
  ): Promise<ApiResponse<Template>> {
    return this.request<Template>(`/api/v1/enhanced-workflows/processes/${processId}/templates`, {
      method: 'POST',
      body: JSON.stringify(templateData),
    });
  }

  async listTemplates(params?: {
    skip?: number;
    limit?: number;
    category?: string;
    tenant_id?: string;
  }): Promise<ApiResponse<{ templates: Template[]; total: number; skip: number; limit: number }>> {
    const searchParams = new URLSearchParams();
    if (params?.skip) searchParams.append('skip', params.skip.toString());
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.category) searchParams.append('category', params.category);
    if (params?.tenant_id) searchParams.append('tenant_id', params.tenant_id);

    const queryString = searchParams.toString();
    const endpoint = `/api/v1/enhanced-workflows/templates${queryString ? `?${queryString}` : ''}`;
    
    return this.request<{ templates: Template[]; total: number; skip: number; limit: number }>(endpoint);
  }

  // BPMN Validation
  async validateBpmn(bpmnXml: string): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v1/enhanced-workflows/validate', {
      method: 'POST',
      body: JSON.stringify({ bpmn_xml: bpmnXml }),
    });
  }

  // File Upload
  async uploadBpmnFile(file: File): Promise<ApiResponse<any>> {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const url = `${this.baseUrl}/api/v1/enhanced-workflows/upload`;
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      console.error('File upload failed:', error);
      return { error: error instanceof Error ? error.message : 'Unknown error occurred' };
    }
  }
}

// Export singleton instance
export const processApiService = new ProcessApiService();

// Export types
export type {
  Process,
  ProcessCreate,
  ProcessUpdate,
  ProcessInstance,
  ProcessInstanceCreate,
  Template,
  TemplateCreate,
  ApiResponse,
};

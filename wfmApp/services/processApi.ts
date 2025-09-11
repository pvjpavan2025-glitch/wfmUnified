/**
 * Frontend API service for process management
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_BPMN_BACKEND_URL || 'http://localhost:8100';
// Offline / backend optional mode: when true, network failures return graceful empty data
const OFFLINE_MODE = process.env.NEXT_PUBLIC_BPMN_OFFLINE_MODE === 'true';
// Proxy toggle: enable only if explicitly requested via env var NEXT_PUBLIC_USE_API_PROXY = 'true'
// This lets us bypass the proxy (option 2) without touching other working functionality.
const USE_PROXY = typeof window !== 'undefined' && process.env.NEXT_PUBLIC_USE_API_PROXY === 'true';
const BROWSER_PROXY_PREFIX = USE_PROXY ? '/api/backend?path=' : undefined;

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

export interface BpmnTempStorageRequest {
  xml: string;
  filename: string;
  session_id: string;
  overwrite?: boolean;
}

export interface BpmnTempStorageResponse {
  success: boolean;
  key?: string;
  message: string;
  timestamp: string;
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
      let url = `${this.baseUrl}${endpoint}`;
      // If in browser and proxy prefix is available, route through proxy
      if (typeof window !== 'undefined' && BROWSER_PROXY_PREFIX) {
        url = `${BROWSER_PROXY_PREFIX}${encodeURIComponent(endpoint)}`;
      }

  const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

  let responseData: any = null;
  try { responseData = await response.json(); } catch { /* non-json */ }
      
      if (!response.ok) {
        // Handle validation errors (422) specially
        if (response.status === 422) {
          const validationError = typeof responseData === 'object' 
            ? JSON.stringify(responseData, null, 2)  // Pretty print object
            : responseData;
          console.error('Validation Error:', validationError);
          throw new Error(`Validation Error: ${validationError}`);
        }
        
        // Handle other errors
        const errorMessage = responseData?.detail || 
                           responseData?.message || 
                           (typeof responseData === 'object' ? JSON.stringify(responseData) : responseData) ||
                           `HTTP error! status: ${response.status}`;
        throw new Error(errorMessage);
      }

      return { data: responseData };
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      if (OFFLINE_MODE) {
        // Return sensible empty structures based on heuristic of endpoint
        if (/processes\/instances/.test(endpoint)) return { data: [] as any };
        if (/processes\/?$/.test(endpoint) || /processes\?/.test(endpoint)) return { data: [] as any };
        if (/templates/.test(endpoint)) return { data: [] as any };
        return { error: `(offline) ${errorMessage}` };
      }
      return { error: errorMessage };
    }
  }

  // Process Management
  async createProcess(processData: ProcessCreate, userId: string): Promise<ApiResponse<Process>> {
    console.log('🔍 API: createProcess called');
    console.log('📄 API: Create data BPMN XML length:', processData.bpmn_xml?.length || 0);
    console.log('📄 API: Create data BPMN XML preview:', processData.bpmn_xml?.substring(0, 150) || 'NO XML');
    
    const response = await this.request<Process>(`/api/v1/processes/?user_id=${userId}`, {
      method: 'POST',
      body: JSON.stringify(processData),
    });
    
    console.log('🔍 API: createProcess response:', response);
    if (response.data) {
      console.log('📄 API: Created process BPMN XML length:', response.data.bpmn_xml?.length || 0);
      console.log('📄 API: Created process BPMN XML preview:', response.data.bpmn_xml?.substring(0, 150) || 'NO XML');
    }
    return response;
  }

  async listProcesses(params?: {
    skip?: number;
    limit?: number;
    category?: string;
    status?: string;
    tenant_id?: string;
  }): Promise<ApiResponse<Process[]>> {
    const searchParams = new URLSearchParams();
    if (params?.skip) searchParams.append('skip', params.skip.toString());
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.category) searchParams.append('category', params.category);
    if (params?.status) searchParams.append('status', params.status);
    if (params?.tenant_id) searchParams.append('tenant_id', params.tenant_id);

    const queryString = searchParams.toString();
    const endpoint = `/api/v1/processes/${queryString ? `?${queryString}` : ''}`;
    
    const res = await this.request<Process[]>(endpoint);
    // Normalize potential backend field mismatches (e.g., process_id)
    if (res.data) {
      res.data = res.data.map((p: any) => ({
        // Preserve original fields first, then normalize id to a stable value
        ...p,
        id: p?.id ?? p?.process_id ?? p?.processId,
      }));
    }
    return res;
  }

  async getProcess(processId: string): Promise<ApiResponse<Process>> {
    console.log('🔍 API: getProcess called with ID:', processId);
    const response = await this.request<Process>(`/api/v1/processes/${processId}`);
    console.log('🔍 API: getProcess response:', response);
    if (response.data) {
      console.log('📄 API: Retrieved BPMN XML length:', response.data.bpmn_xml?.length || 0);
      console.log('📄 API: Retrieved BPMN XML preview:', response.data.bpmn_xml?.substring(0, 150) || 'NO XML');
    }
    return response;
  }

  async updateProcess(processId: string, processData: ProcessUpdate): Promise<ApiResponse<Process>> {
    console.log('🔍 API: updateProcess called with ID:', processId);
    console.log('📄 API: Update data BPMN XML length:', processData.bpmn_xml?.length || 0);
    console.log('📄 API: Update data BPMN XML preview:', processData.bpmn_xml?.substring(0, 150) || 'NO XML');
    
    const response = await this.request<Process>(`/api/v1/processes/${processId}?user_id=current_user`, {
      method: 'PUT',
      body: JSON.stringify(processData),
    });
    
    console.log('🔍 API: updateProcess response:', response);
    if (response.data) {
      console.log('📄 API: Updated process BPMN XML length:', response.data.bpmn_xml?.length || 0);
      console.log('📄 API: Updated process BPMN XML preview:', response.data.bpmn_xml?.substring(0, 150) || 'NO XML');
    }
    return response;
  }

  async deleteProcess(processId: string): Promise<ApiResponse<Process>> {
    return this.request<Process>(`/api/v1/processes/${processId}`, {
      method: 'DELETE',
    });
  }

  // Process Instances
  async createProcessInstance(
    processId: string,
    instanceData: ProcessInstanceCreate
  ): Promise<ApiResponse<ProcessInstance>> {
    return this.request<ProcessInstance>(`/api/v1/processes/${processId}/instances`, {
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
  ): Promise<ApiResponse<ProcessInstance[]>> {
    // Use the list-all endpoint with process_id filter to avoid 405 on nested route
    const searchParams = new URLSearchParams();
    if (params?.skip) searchParams.append('skip', params.skip.toString());
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.status) searchParams.append('status', params.status);
    if (params?.tenant_id) searchParams.append('tenant_id', params.tenant_id);
    if (processId) searchParams.append('process_id', processId);

    const queryString = searchParams.toString();
    const endpoint = `/api/v1/processes/instances${queryString ? `?${queryString}` : ''}`;
    
    return this.request<ProcessInstance[]>(endpoint);
  }

  async getProcessInstance(instanceId: string): Promise<ApiResponse<ProcessInstance>> {
    return this.request<ProcessInstance>(`/api/v1/processes/instances/${instanceId}`);
  }

  async executeProcessInstance(instanceId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/v1/processes/instances/${instanceId}/execute`, {
      method: 'POST',
    });
  }

  async deleteProcessInstance(instanceId: string): Promise<ApiResponse<{ message: string }>> {
    return this.request<{ message: string }>(`/api/v1/processes/instances/${instanceId}`, {
      method: 'DELETE',
    });
  }

  async listAllProcessInstances(params?: {
    skip?: number;
    limit?: number;
    process_id?: string;
    status?: string;
  }): Promise<ApiResponse<ProcessInstance[]>> {
    const searchParams = new URLSearchParams();
    if (params?.skip) searchParams.append('skip', params.skip.toString());
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.process_id) searchParams.append('process_id', params.process_id);
    if (params?.status) searchParams.append('status', params.status);

    const queryString = searchParams.toString();
    const endpoint = `/api/v1/processes/instances${queryString ? `?${queryString}` : ''}`;
    
    return this.request<ProcessInstance[]>(endpoint);
  }

  // Templates
  async createTemplateFromProcess(
    processId: string,
    templateData: Record<string, any>
  ): Promise<ApiResponse<Template>> {
    return this.request<Template>(`/api/v1/processes/${processId}/templates`, {
      method: 'POST',
      body: JSON.stringify(templateData),
    });
  }

  async listTemplates(params?: {
    skip?: number;
    limit?: number;
    category?: string;
    tenant_id?: string;
  }): Promise<ApiResponse<Template[]>> {
    const searchParams = new URLSearchParams();
    if (params?.skip) searchParams.append('skip', params.skip.toString());
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.category) searchParams.append('category', params.category);
    if (params?.tenant_id) searchParams.append('tenant_id', params.tenant_id);

    const queryString = searchParams.toString();
    const endpoint = `/api/v1/processes/templates${queryString ? `?${queryString}` : ''}`;
    
    return this.request<Template[]>(endpoint);
  }

  async createTemplate(templateData: Record<string, any>): Promise<ApiResponse<Template>> {
    return this.request<Template>(`/api/v1/processes/templates`, {
      method: 'POST',
      body: JSON.stringify(templateData),
    });
  }

  async getTemplate(templateId: string): Promise<ApiResponse<Template>> {
    return this.request<Template>(`/api/v1/processes/templates/${templateId}`);
  }

  async updateTemplate(templateId: string, templateData: Record<string, any>): Promise<ApiResponse<Template>> {
    return this.request<Template>(`/api/v1/processes/templates/${templateId}`, {
      method: 'PUT',
      body: JSON.stringify(templateData),
    });
  }

  async deleteTemplate(templateId: string): Promise<ApiResponse<{ message: string }>> {
    return this.request<{ message: string }>(`/api/v1/processes/templates/${templateId}`);
  }

  // BPMN Temporary Storage
  async storeBpmnTemporarily(
    storageData: BpmnTempStorageRequest
  ): Promise<ApiResponse<BpmnTempStorageResponse>> {
    return this.request<BpmnTempStorageResponse>(`/api/v1/bpmn-temp/store`, {
      method: 'POST',
      body: JSON.stringify(storageData),
    });
  }

  // BPMN Validation
  async validateBpmn(bpmnXml: string): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v1/workflows/validate', {
      method: 'POST',
      body: JSON.stringify({ bpmn_xml: bpmnXml }),
    });
  }

  // Backend reachability ping (bypasses OFFLINE_MODE handling to know real status)
  async pingBackend(timeoutMs: number = 4000): Promise<boolean> {
    const controller = new AbortController();
    const to = setTimeout(() => controller.abort(), timeoutMs);
    try {
      // Prefer /health if exists, fallback to a lightweight processes query
      const healthUrl = `${this.baseUrl}/health`;
      let resp: Response | null = null;
      try {
        resp = await fetch(healthUrl, { method: 'GET', signal: controller.signal });
        if (resp.ok) return true;
      } catch { /* ignore and fallback */ }
      const probeUrl = `${this.baseUrl}/api/v1/processes/?limit=1`;
      resp = await fetch(probeUrl, { method: 'GET', signal: controller.signal });
      return resp.ok;
    } catch {
      return false;
    } finally {
      clearTimeout(to);
    }
  }

  // File Upload
  async uploadBpmnFile(file: File): Promise<ApiResponse<any>> {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const url = `${this.baseUrl}/api/v1/workflows/upload`;
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

// Types are already exported with export interface above

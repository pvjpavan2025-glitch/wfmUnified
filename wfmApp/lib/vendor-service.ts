import { API_CONFIG } from './api';
import { authService } from './auth-service';

export interface Vendor {
  _id?: string;
  id: string;  // Make id required instead of optional
  tenant_id: string;
  name: string;
  description?: string;
  contact_email: string;
  contact_phone: string;
  address: string;
  status: 'active' | 'inactive' | 'suspended';
  capabilities: string[];
  specializations: string[];  // Make specializations required for UI compatibility
  service_areas: string[];
  technician_count: number;
  lead_count: number;
  created_at: string;
  updated_at: string;
  created_by?: string;
  updated_by?: string;
}

export interface CreateVendorRequest {
  name: string;
  description?: string;
  contact_email: string;
  contact_phone: string;
  address: string;
  capabilities: string[];
  service_areas?: string[];
  tenant_id: string;
}

export interface VendorsResponse {
  vendors: Vendor[];
  total: number;
  page: number;
  limit: number;
}

class VendorService {
  private baseUrl = API_CONFIG.API_GATEWAY;

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      ...authService.getAuthHeaders(),
      ...options.headers,
    };

    console.log('VendorService: Making request to:', url);
    console.log('VendorService: Headers:', headers);

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('VendorService: Request failed:', response.status, errorText);
      throw new Error(`Request failed: ${response.status} ${errorText}`);
    }

    const data = await response.json();
    console.log('VendorService: Response data:', data);
    return data;
  }

  async getVendors(params?: {
    page?: number;
    limit?: number;
    search?: string;
    status?: string;
  }): Promise<Vendor[]> {
    try {
      const queryParams = new URLSearchParams();
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.limit) queryParams.append('limit', params.limit.toString());
      if (params?.search) queryParams.append('search', params.search);
      if (params?.status && params.status !== 'all') queryParams.append('status', params.status);

      const endpoint = `/vendors${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
      const vendors = await this.makeRequest<Vendor[]>(endpoint);
      
      console.log('Raw vendors from API:', vendors);
      console.log('First vendor raw:', vendors[0]);
      if (vendors[0]) {
        console.log('All keys in first vendor:', Object.keys(vendors[0]));
        console.log('All values in first vendor:', Object.entries(vendors[0]));
      }
      
      // Normalize the response - ensure id field exists
      return vendors.map((vendor, index) => {
        console.log(`Normalizing vendor ${index}:`, vendor);
        console.log('vendor._id:', vendor._id);
        console.log('vendor.id:', vendor.id);
        console.log('All vendor keys:', Object.keys(vendor));
        
        // Try to find any field that could be an ID
        const vendorAny = vendor as any;
        let possibleId = vendor._id || vendor.id || vendorAny.vendor_id || vendorAny.objectId || vendorAny.pk || '';
        
        // If no valid ID found, generate a temporary one based on vendor data
        if (!possibleId || possibleId === 'null' || possibleId === 'undefined') {
          // Use vendor name + tenant_id + created_at as a fallback unique identifier
          const fallbackId = `temp_${vendor.name}_${vendor.tenant_id}_${vendor.created_at}`.replace(/[^a-zA-Z0-9_]/g, '_');
          console.warn(`Vendor ${index} has no valid ID, using fallback: ${fallbackId}`);
          possibleId = fallbackId;
        }
        
        console.log('Final ID used:', possibleId);
        
        const normalizedVendor = {
          ...vendor,
          id: possibleId,
          // Map capabilities to specializations for UI compatibility
          specializations: vendor.capabilities || [],
        };
        
        console.log('Normalized vendor:', normalizedVendor);
        return normalizedVendor;
      });
    } catch (error) {
      console.error('VendorService: Error fetching vendors:', error);
      throw error;
    }
  }

  async getVendor(id: string): Promise<Vendor> {
    try {
      const vendor = await this.makeRequest<Vendor>(`/vendors/${id}`);
      return {
        ...vendor,
        id: vendor._id || vendor.id || '',
        specializations: vendor.capabilities || [],
      };
    } catch (error) {
      console.error('VendorService: Error fetching vendor:', error);
      throw error;
    }
  }

  async createVendor(vendorData: CreateVendorRequest): Promise<Vendor> {
    try {
      const vendor = await this.makeRequest<Vendor>('/vendors', {
        method: 'POST',
        body: JSON.stringify(vendorData),
      });
      return {
        ...vendor,
        id: vendor._id || vendor.id || '',
        specializations: vendor.capabilities || [],
      };
    } catch (error) {
      console.error('VendorService: Error creating vendor:', error);
      throw error;
    }
  }

  async updateVendor(id: string, vendorData: Partial<Vendor>): Promise<Vendor> {
    console.log('VendorService.updateVendor called with:', { id, vendorData });
    console.log('ID type:', typeof id);
    console.log('ID length:', id ? id.length : 'undefined');
    console.log('ID value (JSON):', JSON.stringify(id));
    console.log('Full URL will be:', `/vendors/${id}`);
    
    if (!id || id === 'undefined' || id === 'null' || id.trim() === '') {
      throw new Error(`Invalid vendor ID: "${id}" (type: ${typeof id})`);
    }
    
    // Check if this is a temporary/fallback ID (starts with 'temp_')
    if (id.startsWith('temp_')) {
      throw new Error(`Cannot update vendor with temporary ID: "${id}". This vendor has no valid database ID and cannot be updated.`);
    }
    
    const url = `/vendors/${id}`;
    console.log('Final constructed URL:', url);
    
    return this.makeRequest<Vendor>(url, {
      method: 'PUT',
      body: JSON.stringify(vendorData),
    });
  }

  async deleteVendor(id: string): Promise<void> {
    try {
      await this.makeRequest(`/vendors/${id}`, {
        method: 'DELETE',
      });
    } catch (error) {
      console.error('VendorService: Error deleting vendor:', error);
      throw error;
    }
  }
}

export const vendorService = new VendorService();

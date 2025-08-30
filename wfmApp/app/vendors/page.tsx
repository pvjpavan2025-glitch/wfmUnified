"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table as TableComponent, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { RefreshCw, Eye, Plus, Search, Filter, Building2, Users, UserPlus, Edit, List, Table } from 'lucide-react';
import { ProtectedRoute } from '../../components/protected-route';
import AppShell from '@/components/app-shell';
import HierarchicalVendorsTable from '@/components/vendors/hierarchical-vendors-table';
import NestedVendorsTableView from '@/components/vendors/nested-vendors-table-view';
import { vendorService, type Vendor } from '@/lib/vendor-service';

// Add Vendor Dialog Component
const AddVendorDialog = ({ 
  onSubmit, 
  loading, 
  onCancel 
}: { 
  onSubmit: (data: any) => void; 
  loading: boolean; 
  onCancel: () => void; 
}) => {
  const [formData, setFormData] = useState({
    name: '',
    contact_email: '',
    contact_phone: '',
    address: '',
    description: '',
    capabilities: [] as string[]
  });
  const [capabilityInput, setCapabilityInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const addCapability = () => {
    if (capabilityInput.trim() && !formData.capabilities.includes(capabilityInput.trim())) {
      setFormData({
        ...formData,
        capabilities: [...formData.capabilities, capabilityInput.trim()]
      });
      setCapabilityInput('');
    }
  };

  const removeCapability = (capability: string) => {
    setFormData({
      ...formData,
      capabilities: formData.capabilities.filter(c => c !== capability)
    });
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addCapability();
    }
  };

  return (
    <DialogContent className="max-w-2xl">
      <DialogHeader>
        <DialogTitle>Add New Vendor</DialogTitle>
        <DialogDescription>
          Create a new vendor to manage their technicians and assignments
        </DialogDescription>
      </DialogHeader>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="name">Company Name *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              placeholder="Enter company name"
              required
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="contact_email">Contact Email *</Label>
            <Input
              id="contact_email"
              type="email"
              value={formData.contact_email}
              onChange={(e) => setFormData({...formData, contact_email: e.target.value})}
              placeholder="contact@company.com"
              required
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="contact_phone">Contact Phone *</Label>
            <Input
              id="contact_phone"
              value={formData.contact_phone}
              onChange={(e) => setFormData({...formData, contact_phone: e.target.value})}
              placeholder="+1-555-0123"
              required
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="address">Address *</Label>
            <Input
              id="address"
              value={formData.address}
              onChange={(e) => setFormData({...formData, address: e.target.value})}
              placeholder="123 Main St, City, State"
              required
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            value={formData.description}
            onChange={(e) => setFormData({...formData, description: e.target.value})}
            placeholder="Brief description of the vendor's services..."
            rows={3}
          />
        </div>

        <div className="space-y-2">
          <Label>Capabilities</Label>
          <div className="flex gap-2">
            <Input
              value={capabilityInput}
              onChange={(e) => setCapabilityInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Enter capability (e.g., fiber_installation)"
            />
            <Button type="button" onClick={addCapability} variant="outline">
              Add
            </Button>
          </div>
          <div className="flex flex-wrap gap-2 mt-2">
            {formData.capabilities.map((capability) => (
              <Badge key={capability} variant="secondary" className="cursor-pointer">
                {capability}
                <button
                  type="button"
                  onClick={() => removeCapability(capability)}
                  className="ml-2 hover:text-red-500"
                >
                  ×
                </button>
              </Badge>
            ))}
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-4">
          <Button type="button" variant="outline" onClick={onCancel} disabled={loading}>
            Cancel
          </Button>
          <Button type="submit" disabled={loading}>
            {loading ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                Creating...
              </>
            ) : (
              'Create Vendor'
            )}
          </Button>
        </div>
      </form>
    </DialogContent>
  );
};

interface Technician {
  id: string;
  name: string;
  email: string;
  phone: string;
  vendor_id: string;
  vendor_name: string;
  skills: string[];
  experience_years: number;
  status: string;
  availability_status: string;
  location: string;
  created_at: string;
}

interface Lead {
  id: string;
  name: string;
  email: string;
  phone: string;
  vendor_id: string;
  vendor_name: string;
  specializations: string[];
  team_size: number;
  status: string;
  created_at: string;
}

const VendorsPage = () => {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [technicians, setTechnicians] = useState<Technician[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedVendor, setSelectedVendor] = useState<Vendor | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('vendors');
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [viewMode, setViewMode] = useState('hierarchical');
  const [isAddVendorOpen, setIsAddVendorOpen] = useState(false);
  const [addVendorLoading, setAddVendorLoading] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  // Refetch data when filters change
  useEffect(() => {
    if (!loading) {
      const timeoutId = setTimeout(() => {
        fetchData();
      }, 500); // Debounce search
      return () => clearTimeout(timeoutId);
    }
  }, [searchTerm, statusFilter]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch vendors from the API
      const vendorsData = await vendorService.getVendors({
        page: 1,
        limit: 100, // Get all vendors for now
        status: statusFilter === 'all' ? undefined : statusFilter,
        search: searchTerm || undefined
      });
      
      console.log('Fetched vendors:', vendorsData);
      setVendors(vendorsData);
      
      // TODO: Implement technicians and leads APIs
      // For now, keep mock data for technicians and leads
      const mockTechnicians: Technician[] = [
        {
          id: 'tech-001',
          name: 'Jacob Williams',
          email: 'jacob@techcorp.com',
          phone: '+1-555-1001',
          vendor_id: 'vendor-001',
          vendor_name: 'TechCorp Solutions',
          skills: ['fiber_optics', 'network_troubleshooting', 'data_validation'],
          experience_years: 5,
          status: 'active',
          availability_status: 'available',
          location: 'San Francisco, CA',
          created_at: '2024-01-01T00:00:00Z'
        },
        {
          id: 'tech-002',
          name: 'Mike Chen',
          email: 'mike@techcorp.com',
          phone: '+1-555-1002',
          vendor_id: 'vendor-001',
          vendor_name: 'TechCorp Solutions',
          skills: ['technical_review', 'fiber_optics', 'project_management'],
          experience_years: 8,
          status: 'active',
          availability_status: 'busy',
          location: 'San Francisco, CA',
          created_at: '2024-01-01T00:00:00Z'
        },
        {
          id: 'tech-003',
          name: 'Joseph Joestar',
          email: 'joseph@fieldservices.com',
          phone: '+1-555-2001',
          vendor_id: 'vendor-002',
          vendor_name: 'Field Services Inc',
          skills: ['cable_installation', 'field_work', 'equipment_maintenance'],
          experience_years: 3,
          status: 'active',
          availability_status: 'available',
          location: 'Austin, TX',
          created_at: '2024-01-02T00:00:00Z'
        }
      ];

      const mockLeads: Lead[] = [
        {
          id: 'lead-001',
          name: 'Sarah Johnson',
          email: 'sarah@techcorp.com',
          phone: '+1-555-3001',
          vendor_id: 'vendor-001',
          vendor_name: 'TechCorp Solutions',
          specializations: ['team_management', 'quality_assurance'],
          team_size: 8,
          status: 'active',
          created_at: '2024-01-01T00:00:00Z'
        },
        {
          id: 'lead-002',
          name: 'Lisa Rodriguez',
          email: 'lisa@techcorp.com',
          phone: '+1-555-3002',
          vendor_id: 'vendor-001',
          vendor_name: 'TechCorp Solutions',
          specializations: ['technical_oversight', 'training'],
          team_size: 7,
          status: 'active',
          created_at: '2024-01-01T00:00:00Z'
        },
        {
          id: 'lead-003',
          name: 'Diana Prince',
          email: 'diana@fieldservices.com',
          phone: '+1-555-4001',
          vendor_id: 'vendor-002',
          vendor_name: 'Field Services Inc',
          specializations: ['field_operations', 'safety_compliance'],
          team_size: 5,
          status: 'active',
          created_at: '2024-01-02T00:00:00Z'
        }
      ];

      setTechnicians(mockTechnicians);
      setLeads(mockLeads);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      setError(`Failed to fetch vendor data: ${error instanceof Error ? error.message : 'Unknown error'}`);
      // On error, fall back to empty data
      setVendors([]);
      setTechnicians([]);
      setLeads([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAddVendor = async (vendorData: {
    name: string;
    contact_email: string;
    contact_phone: string;
    address: string;
    description?: string;
    capabilities: string[];
  }) => {
    try {
      setAddVendorLoading(true);
      await vendorService.createVendor({
        ...vendorData,
        tenant_id: 'default', // Use default tenant for now
      });
      
      // Close dialog and refresh data
      setIsAddVendorOpen(false);
      await fetchData();
    } catch (error) {
      console.error('Failed to create vendor:', error);
      setError(`Failed to create vendor: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setAddVendorLoading(false);
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'active': return 'default';
      case 'inactive': return 'secondary';
      case 'suspended': return 'destructive';
      default: return 'outline';
    }
  };

  const getAvailabilityBadgeVariant = (status: string) => {
    switch (status) {
      case 'available': return 'default';
      case 'busy': return 'secondary';
      case 'unavailable': return 'destructive';
      default: return 'outline';
    }
  };

  const filteredVendors = vendors.filter((vendor: Vendor) => {
    const matchesSearch = vendor.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         vendor.contact_email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || vendor.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const filteredTechnicians = technicians.filter((tech: Technician) => {
    const matchesSearch = tech.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         tech.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         tech.vendor_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || tech.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const filteredLeads = leads.filter((lead: Lead) => {
    const matchesSearch = lead.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         lead.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         lead.vendor_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || lead.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // Calculate summary statistics
  const totalVendors = filteredVendors.length;
  const totalLeads = filteredLeads.length;
  const totalTechnicians = filteredTechnicians.length;
  const activeTechnicians = filteredTechnicians.filter((t: Technician) => t.availability_status === 'available').length;

  return (
    <ProtectedRoute>
      <AppShell title="Vendor Management" subtitle="Manage vendors, technicians, and team leads">
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold">Vendor Management</h1>
              <p className="text-muted-foreground">Manage vendors, technicians, and team leads</p>
            </div>
            <div className="flex gap-2">
              <Button onClick={() => fetchData()}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Refresh
              </Button>
              <Dialog open={isAddVendorOpen} onOpenChange={setIsAddVendorOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="mr-2 h-4 w-4" />
                    Add Vendor
                  </Button>
                </DialogTrigger>
                <AddVendorDialog 
                  onSubmit={handleAddVendor} 
                  loading={addVendorLoading}
                  onCancel={() => setIsAddVendorOpen(false)}
                />
              </Dialog>
            </div>
          </div>

          {/* Summary Stats - Single Line */}
          <Card>
            <CardContent className="py-4">
              <div className="flex items-center justify-between w-full">
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-muted-foreground">Total Vendors:</span>
                  <span className="text-lg font-bold">{totalVendors}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-muted-foreground">Team Leads:</span>
                  <span className="text-lg font-bold">{totalLeads}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-muted-foreground">Total Technicians:</span>
                  <span className="text-lg font-bold">{totalTechnicians}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-muted-foreground">Available Technicians:</span>
                  <span className="text-lg font-bold text-green-600">{activeTechnicians}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Error Display */}
          {error && (
            <Card>
              <CardContent className="py-4">
                <div className="flex items-center gap-2 text-red-600">
                  <RefreshCw className="h-4 w-4" />
                  <span className="font-medium">Error:</span>
                  <span>{error}</span>
                  <Button variant="outline" size="sm" onClick={fetchData}>
                    Retry
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Filters & View Options */}
          <Card>
            <CardContent className="py-4">
              <div className="flex gap-4 items-center">
                <Filter className="h-5 w-5 text-muted-foreground" />
                
                {/* Search Bar */}
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <Input
                    type="text"
                    placeholder="Search vendors, leads, or technicians..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
                
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-40">
                    <SelectValue placeholder="All Statuses" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Statuses</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
                    <SelectItem value="suspended">Suspended</SelectItem>
                  </SelectContent>
                </Select>
                
                {/* View Toggle Buttons */}
                <div className="flex">
                  <Button
                    variant={viewMode === 'hierarchical' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setViewMode('hierarchical')}
                    className="rounded-r-none"
                  >
                    <List className="mr-2 h-4 w-4" />
                    Hierarchical
                  </Button>
                  <Button
                    variant={viewMode === 'table' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setViewMode('table')}
                    className="rounded-l-none"
                  >
                    <Table className="mr-2 h-4 w-4" />
                    Table
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Vendors Display */}
          {viewMode === 'hierarchical' ? (
            <HierarchicalVendorsTable
              vendors={filteredVendors}
              leads={filteredLeads}
              technicians={filteredTechnicians}
              searchTerm={searchTerm}
              statusFilter={statusFilter}
            />
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Vendors ({filteredVendors.length}) - Table View</CardTitle>
                <CardDescription>Nested table view of vendors, team leads, and technicians</CardDescription>
              </CardHeader>
              <CardContent>
                <NestedVendorsTableView
                  vendors={filteredVendors}
                  leads={filteredLeads}
                  technicians={filteredTechnicians}
                  searchTerm={searchTerm}
                  statusFilter={statusFilter}
                />
              </CardContent>
            </Card>
          )}

          {/* Legacy Tabs - Hidden but kept for reference */}
          <div className="hidden">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="vendors" className="flex items-center gap-2">
                  <Building2 className="h-4 w-4" />
                  Vendors ({filteredVendors.length})
                </TabsTrigger>
                <TabsTrigger value="technicians" className="flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  Technicians ({filteredTechnicians.length})
                </TabsTrigger>
                <TabsTrigger value="leads" className="flex items-center gap-2">
                  <UserPlus className="h-4 w-4" />
                  Team Leads ({filteredLeads.length})
                </TabsTrigger>
              </TabsList>

              <TabsContent value="vendors" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Vendors</CardTitle>
              <CardDescription>Manage vendor companies and their information</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex justify-center p-8">
                  <RefreshCw className="h-8 w-8 animate-spin" />
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Company Name</TableHead>
                      <TableHead>Contact</TableHead>
                      <TableHead>Specializations</TableHead>
                      <TableHead>Technicians</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredVendors.map((vendor) => (
                      <TableRow key={vendor.id}>
                        <TableCell>
                          <div>
                            <div className="font-medium">{vendor.name}</div>
                            <div className="text-sm text-muted-foreground">{vendor.address}</div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div>
                            <div className="text-sm">{vendor.contact_email}</div>
                            <div className="text-sm text-muted-foreground">{vendor.contact_phone}</div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {(vendor.specializations || vendor.capabilities || []).map((spec: string) => (
                              <Badge key={spec} variant="outline" className="text-xs">
                                {spec.replace('_', ' ')}
                              </Badge>
                            ))}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary">{vendor.technician_count}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={getStatusBadgeVariant(vendor.status)}>
                            {vendor.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            <Dialog>
                              <DialogTrigger asChild>
                                <Button 
                                  variant="outline" 
                                  size="sm"
                                  onClick={() => setSelectedVendor(vendor)}
                                >
                                  <Eye className="h-4 w-4" />
                                </Button>
                              </DialogTrigger>
                              <DialogContent className="max-w-2xl">
                                <DialogHeader>
                                  <DialogTitle>Vendor Details - {selectedVendor?.name}</DialogTitle>
                                  <DialogDescription>
                                    View and manage vendor information
                                  </DialogDescription>
                                </DialogHeader>
                                {selectedVendor && (
                                  <div className="space-y-4">
                                    <div className="grid grid-cols-2 gap-4">
                                      <div>
                                        <h4 className="font-semibold">Company Information</h4>
                                        <p><strong>Name:</strong> {selectedVendor.name}</p>
                                        <p><strong>Email:</strong> {selectedVendor.contact_email}</p>
                                        <p><strong>Phone:</strong> {selectedVendor.contact_phone}</p>
                                        <p><strong>Address:</strong> {selectedVendor.address}</p>
                                      </div>
                                      <div>
                                        <h4 className="font-semibold">Business Details</h4>
                                        <p><strong>Status:</strong> {selectedVendor.status}</p>
                                        <p><strong>Technicians:</strong> {selectedVendor.technician_count}</p>
                                        <p><strong>Created:</strong> {new Date(selectedVendor.created_at).toLocaleDateString()}</p>
                                      </div>
                                    </div>
                                    <div>
                                      <h4 className="font-semibold">Specializations</h4>
                                      <div className="flex gap-2 mt-2">
                                        {(selectedVendor.specializations || selectedVendor.capabilities || []).map((spec: string) => (
                                          <Badge key={spec} variant="outline">
                                            {spec.replace('_', ' ')}
                                          </Badge>
                                        ))}
                                      </div>
                                    </div>
                                  </div>
                                )}
                              </DialogContent>
                            </Dialog>
                            <Button variant="outline" size="sm">
                              <Edit className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
              </TabsContent>

              <TabsContent value="technicians" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Technicians</CardTitle>
              <CardDescription>Manage field technicians and their assignments</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Vendor</TableHead>
                    <TableHead>Skills</TableHead>
                    <TableHead>Experience</TableHead>
                    <TableHead>Availability</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredTechnicians.map((tech) => (
                    <TableRow key={tech.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{tech.name}</div>
                          <div className="text-sm text-muted-foreground">{tech.email}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="text-sm">{tech.vendor_name}</div>
                          <div className="text-sm text-muted-foreground">{tech.location}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {tech.skills.slice(0, 2).map((skill) => (
                            <Badge key={skill} variant="outline" className="text-xs">
                              {skill.replace('_', ' ')}
                            </Badge>
                          ))}
                          {tech.skills.length > 2 && (
                            <Badge variant="outline" className="text-xs">
                              +{tech.skills.length - 2} more
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{tech.experience_years} years</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getAvailabilityBadgeVariant(tech.availability_status)}>
                          {tech.availability_status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusBadgeVariant(tech.status)}>
                          {tech.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="outline" size="sm">
                            <Edit className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
              </TabsContent>

              <TabsContent value="leads" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Team Leads</CardTitle>
              <CardDescription>Manage team leads and supervisors</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Vendor</TableHead>
                    <TableHead>Specializations</TableHead>
                    <TableHead>Team Size</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredLeads.map((lead) => (
                    <TableRow key={lead.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{lead.name}</div>
                          <div className="text-sm text-muted-foreground">{lead.email}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">{lead.vendor_name}</div>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {lead.specializations.map((spec) => (
                            <Badge key={spec} variant="outline" className="text-xs">
                              {spec.replace('_', ' ')}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{lead.team_size} members</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusBadgeVariant(lead.status)}>
                          {lead.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="outline" size="sm">
                            <Edit className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
              </TabsContent>
            </Tabs>
          </div>

          {filteredVendors.length === 0 && !loading && (
            <div className="text-center py-12">
              <p className="text-muted-foreground">No vendors found matching your criteria.</p>
            </div>
          )}
        </div>
      </AppShell>
    </ProtectedRoute>
  );
};

export default VendorsPage;

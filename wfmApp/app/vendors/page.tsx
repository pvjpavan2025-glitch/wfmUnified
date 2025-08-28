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

interface Vendor {
  id: string;
  name: string;
  contact_email: string;
  contact_phone: string;
  address: string;
  status: string;
  specializations: string[];
  technician_count: number;
  created_at: string;
}

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
  const [activeTab, setActiveTab] = useState('vendors');
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [viewMode, setViewMode] = useState('hierarchical');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      // Mock data for now - replace with actual API calls
      const mockVendors: Vendor[] = [
        {
          id: 'vendor-001',
          name: 'TechCorp Solutions',
          contact_email: 'contact@techcorp.com',
          contact_phone: '+1-555-0101',
          address: '123 Tech Street, San Francisco, CA',
          status: 'active',
          specializations: ['fiber_installation', 'network_maintenance'],
          technician_count: 15,
          created_at: '2024-01-01T00:00:00Z'
        },
        {
          id: 'vendor-002',
          name: 'Field Services Inc',
          contact_email: 'info@fieldservices.com',
          contact_phone: '+1-555-0102',
          address: '456 Service Ave, Austin, TX',
          status: 'active',
          specializations: ['cable_installation', 'equipment_repair'],
          technician_count: 8,
          created_at: '2024-01-02T00:00:00Z'
        }
      ];

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

      setVendors(mockVendors);
      setTechnicians(mockTechnicians);
      setLeads(mockLeads);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
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

  const filteredVendors = vendors.filter(vendor => {
    const matchesSearch = vendor.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         vendor.contact_email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || vendor.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const filteredTechnicians = technicians.filter(tech => {
    const matchesSearch = tech.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         tech.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         tech.vendor_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || tech.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const filteredLeads = leads.filter(lead => {
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
  const activeTechnicians = filteredTechnicians.filter(t => t.availability_status === 'available').length;

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
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Add Vendor
              </Button>
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
                            {vendor.specializations.map((spec) => (
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
                                        {selectedVendor.specializations.map((spec) => (
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

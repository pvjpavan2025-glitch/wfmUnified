"use client";

import React, { useState } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ChevronDown, ChevronRight, Building2, Users, UserPlus, Eye, Edit, Phone, Mail, MapPin } from 'lucide-react';
import { Vendor } from '@/lib/vendor-service';

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

interface NestedVendorsTableViewProps {
  vendors: Vendor[];
  leads: Lead[];
  technicians: Technician[];
  searchTerm: string;
  statusFilter: string;
  onEditVendor?: (vendor: Vendor) => void;
}

const NestedVendorsTableView: React.FC<NestedVendorsTableViewProps> = ({
  vendors,
  leads,
  technicians,
  searchTerm,
  statusFilter,
  onEditVendor
}) => {
  const [expandedVendors, setExpandedVendors] = useState<Set<string>>(new Set());
  const [expandedLeads, setExpandedLeads] = useState<Set<string>>(new Set());

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

  const toggleVendorExpansion = (vendorId: string) => {
    const newExpanded = new Set(expandedVendors);
    if (newExpanded.has(vendorId)) {
      newExpanded.delete(vendorId);
    } else {
      newExpanded.add(vendorId);
    }
    setExpandedVendors(newExpanded);
  };

  const toggleLeadExpansion = (leadId: string) => {
    const newExpanded = new Set(expandedLeads);
    if (newExpanded.has(leadId)) {
      newExpanded.delete(leadId);
    } else {
      newExpanded.add(leadId);
    }
    setExpandedLeads(newExpanded);
  };

  // Filter and organize data
  const filteredVendors = vendors.filter(vendor => {
    const matchesSearch = vendor.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         vendor.contact_email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || vendor.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getVendorLeads = (vendorId: string) => {
    return leads.filter(lead => lead.vendor_id === vendorId);
  };

  const getLeadTechnicians = (vendorId: string) => {
    return technicians.filter(tech => tech.vendor_id === vendorId);
  };

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-12"></TableHead>
          <TableHead>Name / Contact</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>Details</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {filteredVendors.map((vendor) => {
          const isVendorExpanded = expandedVendors.has(vendor.id);
          const vendorLeads = getVendorLeads(vendor.id);
          const vendorTechnicians = getLeadTechnicians(vendor.id);

          return (
            <React.Fragment key={vendor.id}>
              {/* Vendor Row */}
              <TableRow className="bg-gray-50 border-b-2">
                <TableCell>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleVendorExpansion(vendor.id)}
                    className="p-1"
                  >
                    {isVendorExpanded ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                  </Button>
                </TableCell>
                <TableCell>
                  <div className="flex items-center space-x-2">
                    <Building2 className="h-4 w-4 text-blue-600" />
                    <div>
                      <div className="font-semibold">{vendor.name}</div>
                      <div className="text-sm text-muted-foreground flex items-center space-x-2">
                        <Mail className="h-3 w-3" />
                        <span>{vendor.contact_email}</span>
                      </div>
                      <div className="text-sm text-muted-foreground flex items-center space-x-2">
                        <Phone className="h-3 w-3" />
                        <span>{vendor.contact_phone}</span>
                      </div>
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className="bg-gray-100">VENDOR</Badge>
                </TableCell>
                <TableCell>
                  <div>
                    <div className="text-sm font-medium">{vendorLeads.length} leads, {vendorTechnicians.length} technicians</div>
                    <div className="text-xs text-muted-foreground flex items-center space-x-1">
                      <MapPin className="h-3 w-3" />
                      <span>{vendor.address}</span>
                    </div>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {vendor.specializations.slice(0, 2).map((spec) => (
                        <Badge key={spec} variant="secondary" className="text-xs">
                          {spec.replace('_', ' ')}
                        </Badge>
                      ))}
                      {vendor.specializations.length > 2 && (
                        <Badge variant="secondary" className="text-xs">
                          +{vendor.specializations.length - 2} more
                        </Badge>
                      )}
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant={getStatusBadgeVariant(vendor.status)}>
                    {vendor.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="flex space-x-1">
                    <Button variant="outline" size="sm">
                      <Eye className="h-3 w-3" />
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => onEditVendor?.(vendor)}
                    >
                      <Edit className="h-3 w-3" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>

              {/* Expanded Vendor Content - Team Leads */}
              {isVendorExpanded && vendorLeads.map((lead) => {
                const isLeadExpanded = expandedLeads.has(lead.id);
                const leadTechnicians = getLeadTechnicians(vendor.id);

                return (
                  <React.Fragment key={lead.id}>
                    {/* Lead Row */}
                    <TableRow className="bg-blue-50 pl-8">
                      <TableCell className="pl-8">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => toggleLeadExpansion(lead.id)}
                          className="p-1"
                        >
                          {isLeadExpanded ? (
                            <ChevronDown className="h-4 w-4" />
                          ) : (
                            <ChevronRight className="h-4 w-4" />
                          )}
                        </Button>
                      </TableCell>
                      <TableCell className="pl-4">
                        <div className="flex items-center space-x-2">
                          <UserPlus className="h-4 w-4 text-green-600" />
                          <div>
                            <div className="font-medium">{lead.name}</div>
                            <div className="text-sm text-muted-foreground flex items-center space-x-2">
                              <Mail className="h-3 w-3" />
                              <span>{lead.email}</span>
                            </div>
                            <div className="text-sm text-muted-foreground flex items-center space-x-2">
                              <Phone className="h-3 w-3" />
                              <span>{lead.phone}</span>
                            </div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="bg-blue-100">LEAD</Badge>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="text-sm font-medium">{lead.team_size} team members</div>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {lead.specializations.map((spec) => (
                              <Badge key={spec} variant="outline" className="text-xs">
                                {spec.replace('_', ' ')}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusBadgeVariant(lead.status)}>
                          {lead.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex space-x-1">
                          <Button variant="outline" size="sm">
                            <Eye className="h-3 w-3" />
                          </Button>
                          <Button variant="outline" size="sm">
                            <Edit className="h-3 w-3" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>

                    {/* Expanded Lead Content - Technicians */}
                    {isLeadExpanded && leadTechnicians.map((technician) => (
                      <TableRow key={technician.id} className="bg-green-50">
                        <TableCell className="pl-12"></TableCell>
                        <TableCell className="pl-8">
                          <div className="flex items-center space-x-2">
                            <Users className="h-4 w-4 text-purple-600" />
                            <div>
                              <div className="font-medium">{technician.name}</div>
                              <div className="text-sm text-muted-foreground flex items-center space-x-2">
                                <Mail className="h-3 w-3" />
                                <span>{technician.email}</span>
                              </div>
                              <div className="text-sm text-muted-foreground flex items-center space-x-2">
                                <Phone className="h-3 w-3" />
                                <span>{technician.phone}</span>
                              </div>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="bg-green-100">TECHNICIAN</Badge>
                        </TableCell>
                        <TableCell>
                          <div>
                            <div className="text-sm font-medium">{technician.experience_years} years experience</div>
                            <div className="text-xs text-muted-foreground flex items-center space-x-1">
                              <MapPin className="h-3 w-3" />
                              <span>{technician.location}</span>
                            </div>
                            <div className="flex items-center space-x-2 mt-1">
                              <Badge variant={getAvailabilityBadgeVariant(technician.availability_status)} className="text-xs">
                                {technician.availability_status}
                              </Badge>
                            </div>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {technician.skills.slice(0, 2).map((skill) => (
                                <Badge key={skill} variant="secondary" className="text-xs">
                                  {skill.replace('_', ' ')}
                                </Badge>
                              ))}
                              {technician.skills.length > 2 && (
                                <Badge variant="secondary" className="text-xs">
                                  +{technician.skills.length - 2} more
                                </Badge>
                              )}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant={getStatusBadgeVariant(technician.status)}>
                            {technician.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex space-x-1">
                            <Button variant="outline" size="sm">
                              <Eye className="h-3 w-3" />
                            </Button>
                            <Button variant="outline" size="sm">
                              <Edit className="h-3 w-3" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </React.Fragment>
                );
              })}
            </React.Fragment>
          );
        })}
      </TableBody>
    </Table>
  );
};

export default NestedVendorsTableView;

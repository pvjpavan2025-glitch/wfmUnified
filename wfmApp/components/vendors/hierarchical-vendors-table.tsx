"use client";

import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
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

interface HierarchicalVendorsTableProps {
  vendors: Vendor[];
  leads: Lead[];
  technicians: Technician[];
  searchTerm: string;
  statusFilter: string;
  onEditVendor?: (vendor: Vendor) => void;
}

const HierarchicalVendorsTable: React.FC<HierarchicalVendorsTableProps> = ({
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

  const getLeadTechnicians = (vendorId: string, leadId?: string) => {
    return technicians.filter(tech => tech.vendor_id === vendorId);
  };

  const getVendorStats = (vendorId: string) => {
    const vendorLeads = getVendorLeads(vendorId);
    const vendorTechnicians = getLeadTechnicians(vendorId);
    const activeTechnicians = vendorTechnicians.filter(t => t.status === 'active').length;
    const availableTechnicians = vendorTechnicians.filter(t => t.availability_status === 'available').length;
    
    return {
      totalLeads: vendorLeads.length,
      totalTechnicians: vendorTechnicians.length,
      activeTechnicians,
      availableTechnicians,
      utilizationRate: vendorTechnicians.length > 0 ? Math.round((activeTechnicians / vendorTechnicians.length) * 100) : 0
    };
  };

  return (
    <div className="space-y-4">
      {filteredVendors.map((vendor) => {
        const isExpanded = expandedVendors.has(vendor.id);
        const vendorLeads = getVendorLeads(vendor.id);
        const stats = getVendorStats(vendor.id);

        return (
          <Card key={vendor.id} className="overflow-hidden">
            <CardContent className="p-0">
              {/* Vendor Row */}
              <div className="bg-gray-50 border-b p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleVendorExpansion(vendor.id)}
                      className="p-1"
                    >
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                    </Button>
                    <Building2 className="h-5 w-5 text-blue-600" />
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-semibold">{vendor.name}</span>
                        <Badge variant="outline" className="text-xs">VENDOR</Badge>
                      </div>
                      <div className="text-sm text-muted-foreground flex items-center space-x-4">
                        <span className="flex items-center space-x-1">
                          <Mail className="h-3 w-3" />
                          <span>{vendor.contact_email}</span>
                        </span>
                        <span className="flex items-center space-x-1">
                          <Phone className="h-3 w-3" />
                          <span>{vendor.contact_phone}</span>
                        </span>
                        <span className="flex items-center space-x-1">
                          <MapPin className="h-3 w-3" />
                          <span>{vendor.address}</span>
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <div className="text-sm font-medium">{stats.totalLeads} leads, {stats.totalTechnicians} technicians</div>
                      <div className="text-xs text-muted-foreground">
                        {stats.availableTechnicians} available • {stats.utilizationRate}% utilization
                      </div>
                      <Progress value={stats.utilizationRate} className="w-20 h-2 mt-1" />
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant={getStatusBadgeVariant(vendor.status)}>
                        {vendor.status}
                      </Badge>
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
                    </div>
                  </div>
                </div>
                <div className="mt-2 flex flex-wrap gap-1">
                  {vendor.specializations.map((spec) => (
                    <Badge key={spec} variant="secondary" className="text-xs">
                      {spec.replace('_', ' ')}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Expanded Vendor Content */}
              {isExpanded && (
                <div className="bg-white">
                  {/* Team Leads */}
                  {vendorLeads.map((lead) => {
                    const isLeadExpanded = expandedLeads.has(lead.id);
                    const leadTechnicians = getLeadTechnicians(vendor.id);

                    return (
                      <div key={lead.id}>
                        <div className="bg-blue-50 border-b p-4 pl-12">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
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
                              <UserPlus className="h-4 w-4 text-green-600" />
                              <div>
                                <div className="flex items-center space-x-2">
                                  <span className="font-medium">{lead.name}</span>
                                  <Badge variant="outline" className="text-xs bg-blue-100">LEAD</Badge>
                                </div>
                                <div className="text-sm text-muted-foreground flex items-center space-x-4">
                                  <span className="flex items-center space-x-1">
                                    <Mail className="h-3 w-3" />
                                    <span>{lead.email}</span>
                                  </span>
                                  <span className="flex items-center space-x-1">
                                    <Phone className="h-3 w-3" />
                                    <span>{lead.phone}</span>
                                  </span>
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center space-x-4">
                              <div className="text-right">
                                <div className="text-sm font-medium">{lead.team_size} team members</div>
                                <div className="text-xs text-muted-foreground">Team Lead</div>
                              </div>
                              <div className="flex items-center space-x-2">
                                <Badge variant={getStatusBadgeVariant(lead.status)}>
                                  {lead.status}
                                </Badge>
                                <div className="flex space-x-1">
                                  <Button variant="outline" size="sm">
                                    <Eye className="h-3 w-3" />
                                  </Button>
                                  <Button variant="outline" size="sm">
                                    <Edit className="h-3 w-3" />
                                  </Button>
                                </div>
                              </div>
                            </div>
                          </div>
                          <div className="mt-2 flex flex-wrap gap-1">
                            {lead.specializations.map((spec) => (
                              <Badge key={spec} variant="outline" className="text-xs">
                                {spec.replace('_', ' ')}
                              </Badge>
                            ))}
                          </div>
                        </div>

                        {/* Expanded Lead Content - Technicians */}
                        {isLeadExpanded && (
                          <div className="bg-white">
                            {leadTechnicians.map((technician) => (
                              <div key={technician.id} className="border-b p-4 pl-20 bg-green-50">
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center space-x-3">
                                    <Users className="h-4 w-4 text-purple-600" />
                                    <div>
                                      <div className="flex items-center space-x-2">
                                        <span className="font-medium">{technician.name}</span>
                                        <Badge variant="outline" className="text-xs bg-green-100">TECHNICIAN</Badge>
                                      </div>
                                      <div className="text-sm text-muted-foreground flex items-center space-x-4">
                                        <span className="flex items-center space-x-1">
                                          <Mail className="h-3 w-3" />
                                          <span>{technician.email}</span>
                                        </span>
                                        <span className="flex items-center space-x-1">
                                          <Phone className="h-3 w-3" />
                                          <span>{technician.phone}</span>
                                        </span>
                                        <span className="flex items-center space-x-1">
                                          <MapPin className="h-3 w-3" />
                                          <span>{technician.location}</span>
                                        </span>
                                      </div>
                                    </div>
                                  </div>
                                  <div className="flex items-center space-x-4">
                                    <div className="text-right">
                                      <div className="text-sm font-medium">{technician.experience_years} years experience</div>
                                      <div className="text-xs text-muted-foreground">
                                        <Badge variant={getAvailabilityBadgeVariant(technician.availability_status)} className="text-xs">
                                          {technician.availability_status}
                                        </Badge>
                                      </div>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                      <Badge variant={getStatusBadgeVariant(technician.status)}>
                                        {technician.status}
                                      </Badge>
                                      <div className="flex space-x-1">
                                        <Button variant="outline" size="sm">
                                          <Eye className="h-3 w-3" />
                                        </Button>
                                        <Button variant="outline" size="sm">
                                          <Edit className="h-3 w-3" />
                                        </Button>
                                      </div>
                                    </div>
                                  </div>
                                </div>
                                <div className="mt-2 flex flex-wrap gap-1">
                                  {technician.skills.slice(0, 3).map((skill) => (
                                    <Badge key={skill} variant="secondary" className="text-xs">
                                      {skill.replace('_', ' ')}
                                    </Badge>
                                  ))}
                                  {technician.skills.length > 3 && (
                                    <Badge variant="secondary" className="text-xs">
                                      +{technician.skills.length - 3} more
                                    </Badge>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};

export default HierarchicalVendorsTable;

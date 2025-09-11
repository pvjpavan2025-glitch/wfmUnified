"use client";

import React, { useState, useEffect } from 'react';
import { AppShell } from '@/components/app-shell';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Search, Filter, Eye, Play, Square, Pause, RotateCcw } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { workflowApiService, WorkflowInstance } from '@/services/workflowApi';

const statusColors = {
  pending: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  running: 'bg-blue-100 text-blue-800 border-blue-200',
  completed: 'bg-green-100 text-green-800 border-green-200',
  failed: 'bg-red-100 text-red-800 border-red-200',
  cancelled: 'bg-gray-100 text-gray-800 border-gray-200',
  suspended: 'bg-orange-100 text-orange-800 border-orange-200',
  paused: 'bg-purple-100 text-purple-800 border-purple-200'
};

const statusIcons = {
  pending: <Play className="w-4 h-4" />,
  running: <Play className="w-4 h-4" />,
  completed: <Square className="w-4 h-4" />,
  failed: <Square className="w-4 h-4" />,
  cancelled: <Square className="w-4 h-4" />,
  suspended: <Pause className="w-4 h-4" />,
  paused: <Pause className="w-4 h-4" />
};

export default function InstancesPage() {
  const router = useRouter();
  const [instances, setInstances] = useState<WorkflowInstance[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const itemsPerPage = 10;

  useEffect(() => {
    fetchInstances();
  }, [currentPage, statusFilter]);

  const fetchInstances = async () => {
    try {
      setLoading(true);
      const params = {
        skip: (currentPage - 1) * itemsPerPage,
        limit: itemsPerPage,
        ...(statusFilter !== 'all' && { status: statusFilter })
      };

      const data = await workflowApiService.getWorkflowInstances(params);
      setInstances(data);
      
      // Calculate total pages (this would typically come from the API)
      setTotalPages(Math.ceil(data.length / itemsPerPage));
    } catch (error) {
      console.error('Error fetching instances:', error);
      toast.error('Failed to load workflow instances');
    } finally {
      setLoading(false);
    }
  };

  const filteredInstances = instances.filter(instance =>
    instance.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    instance.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    instance.created_by.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleViewDetails = (instanceId: string) => {
    router.push(`/instances/${instanceId}`);
  };

  const handleExecuteWorkflow = async (instanceId: string) => {
    try {
      await workflowApiService.executeWorkflow(instanceId, {});
      toast.success('Workflow execution started');
      fetchInstances(); // Refresh the list
    } catch (error) {
      console.error('Error executing workflow:', error);
      toast.error('Failed to execute workflow');
    }
  };

  const handleCancelWorkflow = async (instanceId: string) => {
    try {
      await workflowApiService.cancelWorkflow(instanceId, 'user');
      toast.success('Workflow cancelled');
      fetchInstances(); // Refresh the list
    } catch (error) {
      console.error('Error cancelling workflow:', error);
      toast.error('Failed to cancel workflow');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getDuration = (startDate?: string, endDate?: string) => {
    if (!startDate) return '-';
    
    const start = new Date(startDate);
    const end = endDate ? new Date(endDate) : new Date();
    const diffMs = end.getTime() - start.getTime();
    
    const hours = Math.floor(diffMs / (1000 * 60 * 60));
    const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  return (
    <AppShell title="Workflow Instances" subtitle="Monitor and manage your workflow executions">
      <div className="space-y-6">

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 items-center">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Search instances..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="running">Running</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
                <SelectItem value="cancelled">Cancelled</SelectItem>
                <SelectItem value="suspended">Suspended</SelectItem>
                <SelectItem value="paused">Paused</SelectItem>
              </SelectContent>
            </Select>
            <Button onClick={fetchInstances} variant="outline">
              <RotateCcw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Instances Table */}
      <Card>
        <CardHeader>
          <CardTitle>Workflow Instances</CardTitle>
          <CardDescription>
            {filteredInstances.length} instances found
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center items-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created By</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredInstances.map((instance) => (
                  <TableRow key={instance.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{instance.name}</div>
                        {instance.description && (
                          <div className="text-sm text-muted-foreground">
                            {instance.description}
                          </div>
                        )}
                        {instance.error_message && (
                          <div className="text-sm text-red-600 mt-1">
                            Error: {instance.error_message}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge 
                        variant="outline" 
                        className={statusColors[instance.status]}
                      >
                        <span className="flex items-center gap-1">
                          {statusIcons[instance.status]}
                          {instance.status.charAt(0).toUpperCase() + instance.status.slice(1)}
                        </span>
                      </Badge>
                    </TableCell>
                    <TableCell>{instance.created_by}</TableCell>
                    <TableCell>{formatDate(instance.created_at)}</TableCell>
                    <TableCell>
                      {getDuration(instance.started_at, instance.completed_at)}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleViewDetails(instance.id)}
                        >
                          <Eye className="w-4 h-4 mr-1" />
                          View
                        </Button>
                        {instance.status === 'pending' && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleExecuteWorkflow(instance.id)}
                          >
                            <Play className="w-4 h-4 mr-1" />
                            Execute
                          </Button>
                        )}
                        {(instance.status === 'running' || instance.status === 'paused') && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleCancelWorkflow(instance.id)}
                          >
                            <Square className="w-4 h-4 mr-1" />
                            Cancel
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}

          {!loading && filteredInstances.length === 0 && (
            <div className="text-center py-8">
              <p className="text-muted-foreground">No workflow instances found</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <Button
            variant="outline"
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1}
          >
            Previous
          </Button>
          <span className="flex items-center px-4">
            Page {currentPage} of {totalPages}
          </span>
          <Button
            variant="outline"
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages}
          >
            Next
          </Button>
        </div>
      )}
      </div>
    </AppShell>
  );
}

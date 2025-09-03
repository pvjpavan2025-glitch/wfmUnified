"use client";

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ArrowLeft, Play, Square, Pause, RotateCcw, Eye, FileText, Activity } from 'lucide-react';
import { toast } from 'sonner';
import BpmnViewer from '../../../components/modelling/BpmnViewer';

interface WorkflowStep {
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

interface WorkflowExecutionLog {
  timestamp: string;
  level: string;
  message: string;
  step_id?: string;
  data: Record<string, any>;
}

interface WorkflowInstanceDetails {
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
  bpmn_xml?: string;
}

const statusColors = {
  pending: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  running: 'bg-blue-100 text-blue-800 border-blue-200',
  completed: 'bg-green-100 text-green-800 border-green-200',
  failed: 'bg-red-100 text-red-800 border-red-200',
  cancelled: 'bg-gray-100 text-gray-800 border-gray-200',
  suspended: 'bg-orange-100 text-orange-800 border-orange-200',
  paused: 'bg-purple-100 text-purple-800 border-purple-200',
  skipped: 'bg-gray-100 text-gray-600 border-gray-200'
};

const logLevelColors = {
  INFO: 'text-blue-600',
  WARNING: 'text-yellow-600',
  ERROR: 'text-red-600',
  DEBUG: 'text-gray-600'
};

export default function InstanceDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const instanceId = params.id as string;
  
  const [instance, setInstance] = useState<WorkflowInstanceDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (instanceId) {
      fetchInstanceDetails();
    }
  }, [instanceId]);

  const fetchInstanceDetails = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8100/api/v1/instances/${instanceId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch workflow instance details');
      }
      const data = await response.json();
      setInstance(data);
    } catch (error) {
      console.error('Error fetching instance details:', error);
      toast.error('Failed to load workflow instance details');
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteWorkflow = async () => {
    if (!instance) return;
    
    try {
      const response = await fetch(`http://localhost:8100/api/v1/workflow-execution/instances/${instanceId}/continue`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ task_data: {} })
      });

      if (!response.ok) {
        throw new Error('Failed to execute workflow');
      }

      toast.success('Workflow execution started');
      fetchInstanceDetails();
    } catch (error) {
      console.error('Error executing workflow:', error);
      toast.error('Failed to execute workflow');
    }
  };

  const handleCancelWorkflow = async () => {
    if (!instance) return;
    
    try {
      const response = await fetch(`http://localhost:8100/api/v1/workflow-execution/instances/${instanceId}/cancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ cancelled_by: 'user' })
      });

      if (!response.ok) {
        throw new Error('Failed to cancel workflow');
      }

      toast.success('Workflow cancelled');
      fetchInstanceDetails();
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
    const seconds = Math.floor((diffMs % (1000 * 60)) / 1000);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${seconds}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    }
    return `${seconds}s`;
  };

  const getStepProgress = () => {
    if (!instance || !instance.steps || !Array.isArray(instance.steps) || instance.steps.length === 0) {
      return { completed: 0, total: 0, percentage: 0 };
    }
    
    const completed = instance.steps.filter(step => 
      step.status === 'completed' || step.status === 'skipped'
    ).length;
    const total = instance.steps.length;
    const percentage = Math.round((completed / total) * 100);
    
    return { completed, total, percentage };
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex justify-center items-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  if (!instance) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center py-8">
          <p className="text-muted-foreground">Workflow instance not found</p>
          <Button onClick={() => router.push('/instances')} className="mt-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Instances
          </Button>
        </div>
      </div>
    );
  }

  const progress = getStepProgress();

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push('/instances')}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <h1 className="text-3xl font-bold tracking-tight">{instance.name}</h1>
          </div>
          {instance.description && (
            <p className="text-muted-foreground">{instance.description}</p>
          )}
        </div>
        <div className="flex gap-2">
          <Button onClick={fetchInstanceDetails} variant="outline">
            <RotateCcw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          {instance.status === 'pending' && (
            <Button onClick={handleExecuteWorkflow}>
              <Play className="w-4 h-4 mr-2" />
              Execute
            </Button>
          )}
          {(instance.status === 'running' || instance.status === 'paused') && (
            <Button onClick={handleCancelWorkflow} variant="destructive">
              <Square className="w-4 h-4 mr-2" />
              Cancel
            </Button>
          )}
        </div>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Status</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge 
              variant="outline" 
              className={statusColors[instance.status]}
            >
              {instance.status.charAt(0).toUpperCase() + instance.status.slice(1)}
            </Badge>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{progress.percentage}%</div>
            <p className="text-xs text-muted-foreground">
              {progress.completed} of {progress.total} steps
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Duration</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {getDuration(instance.started_at, instance.completed_at)}
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Created By</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm font-medium">{instance.created_by}</div>
            <p className="text-xs text-muted-foreground">
              {formatDate(instance.created_at)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Error Message */}
      {instance.error_message && (
        <Card className="border-red-200 bg-red-50">
          <CardHeader>
            <CardTitle className="text-red-800">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-red-700">{instance.error_message}</p>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="steps">Steps</TabsTrigger>
          <TabsTrigger value="diagram">Diagram</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Instance Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm font-medium">ID:</span>
                  <span className="text-sm text-muted-foreground">{instance.id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium">Workflow Definition:</span>
                  <span className="text-sm text-muted-foreground">{instance.workflow_definition_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium">Current Step:</span>
                  <span className="text-sm text-muted-foreground">{instance.current_step || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium">Started:</span>
                  <span className="text-sm text-muted-foreground">
                    {instance.started_at ? formatDate(instance.started_at) : 'Not started'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium">Completed:</span>
                  <span className="text-sm text-muted-foreground">
                    {instance.completed_at ? formatDate(instance.completed_at) : 'Not completed'}
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Input Data</CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-48">
                  <pre className="text-xs bg-gray-50 p-2 rounded">
                    {JSON.stringify(instance.input_data, null, 2)}
                  </pre>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="steps">
          <Card>
            <CardHeader>
              <CardTitle>Workflow Steps</CardTitle>
              <CardDescription>
                Detailed view of all workflow steps and their execution status
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Step</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Duration</TableHead>
                    <TableHead>Assigned To</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {instance.steps && Array.isArray(instance.steps) ? instance.steps.map((step) => (
                    <TableRow key={step.step_id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{step.name}</div>
                          <div className="text-sm text-muted-foreground">{step.step_id}</div>
                          {step.error_message && (
                            <div className="text-sm text-red-600 mt-1">
                              Error: {step.error_message}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className="capitalize">{step.step_type}</span>
                      </TableCell>
                      <TableCell>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          statusColors[step.status] || 'bg-gray-100 text-gray-800 border-gray-200'
                        }`}>
                          {step.status}
                        </span>
                      </TableCell>
                      <TableCell>
                        {getDuration(step.started_at, step.completed_at)}
                      </TableCell>
                      <TableCell>{step.assigned_to || '-'}</TableCell>
                    </TableRow>
                  )) : (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center text-muted-foreground">
                        No steps available
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="diagram">
          <Card>
            <CardHeader>
              <CardTitle>BPMN Diagram</CardTitle>
              <CardDescription>
                Visual representation of the workflow with execution status
              </CardDescription>
            </CardHeader>
            <CardContent>
              {instance.bpmn_xml ? (
                <div className="h-96 border rounded">
                  <BpmnViewer 
                    xml={instance.bpmn_xml} 
                    executionData={instance.steps}
                  />
                </div>
              ) : (
                <div className="h-96 border rounded flex items-center justify-center">
                  <p className="text-muted-foreground">No BPMN diagram available</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="logs">
          <Card>
            <CardHeader>
              <CardTitle>Execution Logs</CardTitle>
              <CardDescription>
                Detailed execution logs and events
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96">
                <div className="space-y-2">
                  {instance.execution_logs && Array.isArray(instance.execution_logs) ? instance.execution_logs.map((log, index) => (
                    <div key={index} className="border-l-2 border-gray-200 pl-4 py-2">
                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-muted-foreground">
                          {formatDate(log.timestamp)}
                        </span>
                        <Badge 
                          variant="outline" 
                          className={`text-xs ${logLevelColors[log.level as keyof typeof logLevelColors]}`}
                        >
                          {log.level}
                        </Badge>
                        {log.step_id && (
                          <Badge variant="outline" className="text-xs">
                            {log.step_id}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm mt-1">{log.message}</p>
                      {Object.keys(log.data).length > 0 && (
                        <pre className="text-xs bg-gray-50 p-2 rounded mt-2">
                          {JSON.stringify(log.data, null, 2)}
                        </pre>
                      )}
                    </div>
                  )) : (
                    <p className="text-muted-foreground text-center py-4">
                      No execution logs available
                    </p>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

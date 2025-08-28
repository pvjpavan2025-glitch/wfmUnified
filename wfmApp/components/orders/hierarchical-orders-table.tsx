import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ChevronDown, ChevronRight, User, Calendar, RefreshCw, AlertCircle, Eye } from 'lucide-react';
import { cn } from '@/lib/utils';
import TaskDetailsModal from '@/components/task-details-modal';

interface TaskInstance {
  id: string;
  name: string;
  type: string;
  status: string;
  assigned_technician_id?: string;
  assigned_lead_id?: string;
  scheduled_start?: string;
  scheduled_end?: string;
  created_at: string;
}

interface ProcessInstance {
  id: string;
  process_definition_key: string;
  status: string;
  tasks: TaskInstance[];
  created_at: string;
  completed_tasks: number;
  total_tasks: number;
}

interface Order {
  id: string;
  external_id: string;
  source: string;
  status: string;
  priority: string;
  description: string;
  customer_id?: string;
  processes: ProcessInstance[];
  total_tasks: number;
  completed_tasks: number;
  created_at: string;
  requested_completion_date?: string;
}

interface HierarchicalOrdersTableProps {
  orders: Order[];
  loading: boolean;
  onRefreshOrder: (orderId: string) => void;
}

const HierarchicalOrdersTable: React.FC<HierarchicalOrdersTableProps> = ({
  orders,
  loading,
  onRefreshOrder
}) => {
  const [expandedOrders, setExpandedOrders] = useState<Set<string>>(new Set());
  const [expandedProcesses, setExpandedProcesses] = useState<Set<string>>(new Set());
  const [loadingProcesses, setLoadingProcesses] = useState<Set<string>>(new Set());
  const [selectedTask, setSelectedTask] = useState<TaskInstance | null>(null);
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);

  const toggleOrderExpansion = async (orderId: string) => {
    const newExpanded = new Set(expandedOrders);
    if (newExpanded.has(orderId)) {
      newExpanded.delete(orderId);
      // Also collapse all processes under this order
      const orderProcesses = orders.find(o => o.id === orderId)?.processes || [];
      orderProcesses.forEach(p => {
        const newExpandedProcesses = new Set(expandedProcesses);
        newExpandedProcesses.delete(p.id);
        setExpandedProcesses(newExpandedProcesses);
      });
    } else {
      newExpanded.add(orderId);
      // Lazy load processes if needed
      if (!loadingProcesses.has(orderId)) {
        setLoadingProcesses(prev => new Set(prev).add(orderId));
        // Simulate API call - replace with actual implementation
        setTimeout(() => {
          setLoadingProcesses(prev => {
            const newSet = new Set(prev);
            newSet.delete(orderId);
            return newSet;
          });
        }, 500);
      }
    }
    setExpandedOrders(newExpanded);
  };

  const toggleProcessExpansion = (processId: string) => {
    const newExpanded = new Set(expandedProcesses);
    if (newExpanded.has(processId)) {
      newExpanded.delete(processId);
    } else {
      newExpanded.add(processId);
    }
    setExpandedProcesses(newExpanded);
  };

  const handleTaskDetailsClick = (task: TaskInstance) => {
    setSelectedTask(task);
    setIsTaskModalOpen(true);
  };

  const handleCloseTaskModal = () => {
    setIsTaskModalOpen(false);
    setSelectedTask(null);
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'completed': return 'default';
      case 'in_progress': return 'secondary';
      case 'pending': return 'outline';
      case 'failed': return 'destructive';
      default: return 'outline';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'text-red-600';
      case 'high': return 'text-orange-600';
      case 'medium': return 'text-yellow-600';
      case 'low': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  const getProgressColor = (percentage: number) => {
    if (percentage === 100) return 'bg-green-500';
    if (percentage >= 75) return 'bg-blue-500';
    if (percentage >= 50) return 'bg-yellow-500';
    if (percentage >= 25) return 'bg-orange-500';
    return 'bg-gray-300';
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex justify-center p-8">
          <RefreshCw className="h-8 w-8 animate-spin" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Orders ({orders.length}) - Hierarchical View</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {orders.map((order) => {
            const isOrderExpanded = expandedOrders.has(order.id);
            const isLoadingProcesses = loadingProcesses.has(order.id);
            const orderProgress = order.total_tasks > 0 ? (order.completed_tasks / order.total_tasks) * 100 : 0;

            return (
              <div key={order.id} className="border rounded-lg overflow-hidden">
                {/* Order Row */}
                <div 
                  className="flex items-center p-4 hover:bg-gray-50 cursor-pointer border-b"
                  onClick={() => toggleOrderExpansion(order.id)}
                >
                  <div className="flex items-center space-x-3 flex-1">
                    <Button variant="ghost" size="sm" className="p-0 h-6 w-6">
                      {isOrderExpanded ? 
                        <ChevronDown className="h-4 w-4" /> : 
                        <ChevronRight className="h-4 w-4" />
                      }
                    </Button>
                    
                    <div className="flex items-center space-x-4 flex-1">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-semibold text-lg">{order.external_id}</span>
                          <Badge variant={getStatusBadgeVariant(order.status)}>
                            {order.status.replace('_', ' ')}
                          </Badge>
                          <span className={cn("text-sm font-medium", getPriorityColor(order.priority))}>
                            {order.priority.toUpperCase()}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 truncate">{order.description}</p>
                        <div className="flex items-center space-x-4 text-xs text-gray-500 mt-1">
                          <span>Source: {order.source}</span>
                          <span>Customer: {order.customer_id}</span>
                          <span>Created: {new Date(order.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-4">
                        <div className="text-right">
                          <div className="text-sm font-medium">
                            {order.completed_tasks}/{order.total_tasks} tasks
                          </div>
                          <div className="text-xs text-gray-500">
                            {order.processes.length} processes
                          </div>
                        </div>
                        
                        <div className="w-32">
                          <Progress 
                            value={orderProgress} 
                            className="h-2"
                          />
                          <div className="text-xs text-center mt-1 text-gray-600">
                            {Math.round(orderProgress)}%
                          </div>
                        </div>
                        
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            onRefreshOrder(order.id);
                          }}
                        >
                          <RefreshCw className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Processes Section */}
                {isOrderExpanded && (
                  <div className="bg-gray-50">
                    {isLoadingProcesses ? (
                      <div className="flex justify-center p-4">
                        <RefreshCw className="h-4 w-4 animate-spin" />
                        <span className="ml-2 text-sm text-gray-600">Loading processes...</span>
                      </div>
                    ) : (
                      order.processes.map((process) => {
                        const isProcessExpanded = expandedProcesses.has(process.id);
                        const processProgress = process.total_tasks > 0 ? (process.completed_tasks / process.total_tasks) * 100 : 0;

                        return (
                          <div key={process.id} className="border-t">
                            {/* Process Row */}
                            <div 
                              className="flex items-center p-4 pl-12 hover:bg-gray-100 cursor-pointer"
                              onClick={() => toggleProcessExpansion(process.id)}
                            >
                              <div className="flex items-center space-x-3 flex-1">
                                <Button variant="ghost" size="sm" className="p-0 h-5 w-5">
                                  {isProcessExpanded ? 
                                    <ChevronDown className="h-3 w-3" /> : 
                                    <ChevronRight className="h-3 w-3" />
                                  }
                                </Button>
                                
                                <div className="flex items-center space-x-4 flex-1">
                                  <div className="min-w-0 flex-1">
                                    <div className="flex items-center space-x-2">
                                      <span className="font-medium">{process.process_definition_key}</span>
                                      <Badge variant={getStatusBadgeVariant(process.status)} className="text-xs">
                                        {process.status}
                                      </Badge>
                                    </div>
                                    <div className="text-xs text-gray-500 mt-1">
                                      Process ID: {process.id} • Created: {new Date(process.created_at).toLocaleString()}
                                    </div>
                                  </div>
                                  
                                  <div className="flex items-center space-x-4">
                                    <div className="text-right text-sm">
                                      <div>{process.completed_tasks}/{process.total_tasks} tasks</div>
                                    </div>
                                    
                                    <div className="w-24">
                                      <Progress 
                                        value={processProgress} 
                                        className="h-1.5"
                                      />
                                      <div className="text-xs text-center mt-1 text-gray-600">
                                        {Math.round(processProgress)}%
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>

                            {/* Tasks Section */}
                            {isProcessExpanded && (
                              <div className="bg-white">
                                {process.tasks.map((task) => (
                                  <div key={task.id} className="flex items-center p-3 pl-20 border-t border-gray-100 hover:bg-gray-50">
                                    <div className="flex items-center space-x-4 flex-1">
                                      <div className="min-w-0 flex-1">
                                        <div className="flex items-center space-x-2">
                                          <span className="text-sm font-medium">{task.name}</span>
                                          <Badge variant={getStatusBadgeVariant(task.status)} className="text-xs">
                                            {task.status}
                                          </Badge>
                                        </div>
                                        <div className="text-xs text-gray-500 mt-1">
                                          {task.type} • Task ID: {task.id}
                                        </div>
                                      </div>
                                      
                                      <div className="flex items-center space-x-4 text-sm">
                                        <div className="flex items-center space-x-1">
                                          <User className="h-3 w-3" />
                                          <span>{task.assigned_technician_id || 'Unassigned'}</span>
                                        </div>
                                        
                                        {task.scheduled_start && (
                                          <div className="flex items-center space-x-1">
                                            <Calendar className="h-3 w-3" />
                                            <span>{new Date(task.scheduled_start).toLocaleDateString()}</span>
                                          </div>
                                        )}
                                        
                                        {task.status === 'pending' && !task.assigned_technician_id && (
                                          <AlertCircle className="h-4 w-4 text-orange-500" />
                                        )}
                                        
                                        <Button
                                          variant="ghost"
                                          size="sm"
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            handleTaskDetailsClick(task);
                                          }}
                                          className="h-8 w-8 p-0"
                                        >
                                          <Eye className="h-4 w-4" />
                                        </Button>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        );
                      })
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
      
      {/* Task Details Modal */}
      {selectedTask && (
        <TaskDetailsModal
          task={selectedTask}
          isOpen={isTaskModalOpen}
          onClose={handleCloseTaskModal}
        />
      )}
    </Card>
  );
};

export default HierarchicalOrdersTable;

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
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

interface NestedTableViewProps {
  orders: Order[];
  loading: boolean;
  onRefreshOrder: (orderId: string) => void;
}

const NestedTableView: React.FC<NestedTableViewProps> = ({
  orders,
  loading,
  onRefreshOrder
}) => {
  const [expandedOrders, setExpandedOrders] = useState<Set<string>>(new Set());
  const [expandedProcesses, setExpandedProcesses] = useState<Set<string>>(new Set());
  const [selectedTask, setSelectedTask] = useState<TaskInstance | null>(null);
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);

  const toggleOrderExpansion = (orderId: string) => {
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
        <CardTitle>Orders ({orders.length}) - Nested Table View</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-12"></TableHead>
              <TableHead>ID / Name</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Priority / Assignment</TableHead>
              <TableHead>Progress</TableHead>
              <TableHead>Created / Scheduled</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {orders.map((order) => {
              const isOrderExpanded = expandedOrders.has(order.id);
              const orderProgress = order.total_tasks > 0 ? (order.completed_tasks / order.total_tasks) * 100 : 0;

              return (
                <React.Fragment key={order.id}>
                  {/* Order Row */}
                  <TableRow className="bg-gray-50 font-medium">
                    <TableCell>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="p-0 h-6 w-6"
                        onClick={() => toggleOrderExpansion(order.id)}
                      >
                        {isOrderExpanded ? 
                          <ChevronDown className="h-4 w-4" /> : 
                          <ChevronRight className="h-4 w-4" />
                        }
                      </Button>
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="font-semibold">{order.external_id}</div>
                        <div className="text-sm text-gray-600 truncate max-w-xs">{order.description}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">ORDER</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getStatusBadgeVariant(order.status)}>
                        {order.status.replace('_', ' ')}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div>
                        <span className={cn("text-sm font-medium", getPriorityColor(order.priority))}>
                          {order.priority.toUpperCase()}
                        </span>
                        <div className="text-xs text-gray-500">
                          {order.source} • {order.customer_id}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Progress value={orderProgress} className="w-16 h-2" />
                        <span className="text-xs text-gray-600">
                          {order.completed_tasks}/{order.total_tasks}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {new Date(order.created_at).toLocaleDateString()}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => onRefreshOrder(order.id)}
                      >
                        <RefreshCw className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>

                  {/* Process Rows */}
                  {isOrderExpanded && order.processes.map((process) => {
                    const isProcessExpanded = expandedProcesses.has(process.id);
                    const processProgress = process.total_tasks > 0 ? (process.completed_tasks / process.total_tasks) * 100 : 0;

                    return (
                      <React.Fragment key={process.id}>
                        <TableRow className="bg-blue-50">
                          <TableCell className="pl-8">
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              className="p-0 h-5 w-5"
                              onClick={() => toggleProcessExpansion(process.id)}
                            >
                              {isProcessExpanded ? 
                                <ChevronDown className="h-3 w-3" /> : 
                                <ChevronRight className="h-3 w-3" />
                              }
                            </Button>
                          </TableCell>
                          <TableCell>
                            <div>
                              <div className="font-medium">{process.process_definition_key}</div>
                              <div className="text-xs text-gray-500">Process ID: {process.id}</div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className="text-xs bg-blue-100">PROCESS</Badge>
                          </TableCell>
                          <TableCell>
                            <Badge variant={getStatusBadgeVariant(process.status)} className="text-xs">
                              {process.status}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="text-sm text-gray-600">
                              {process.tasks.length} tasks
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Progress value={processProgress} className="w-12 h-1.5" />
                              <span className="text-xs text-gray-600">
                                {process.completed_tasks}/{process.total_tasks}
                              </span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="text-xs text-gray-500">
                              {new Date(process.created_at).toLocaleString()}
                            </div>
                          </TableCell>
                          <TableCell></TableCell>
                        </TableRow>

                        {/* Task Rows */}
                        {isProcessExpanded && process.tasks.map((task) => (
                          <TableRow key={task.id} className="bg-green-50">
                            <TableCell className="pl-12"></TableCell>
                            <TableCell>
                              <div>
                                <div className="font-medium text-sm">{task.name}</div>
                                <div className="text-xs text-gray-500">Task ID: {task.id}</div>
                              </div>
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline" className="text-xs bg-green-100">TASK</Badge>
                            </TableCell>
                            <TableCell>
                              <Badge variant={getStatusBadgeVariant(task.status)} className="text-xs">
                                {task.status}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center space-x-2 text-sm">
                                <div className="flex items-center space-x-1">
                                  <User className="h-3 w-3" />
                                  <span>{task.assigned_technician_id || 'Unassigned'}</span>
                                </div>
                                {task.status === 'pending' && !task.assigned_technician_id && (
                                  <AlertCircle className="h-3 w-3 text-orange-500" />
                                )}
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="text-xs text-gray-500">
                                {task.type}
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="text-xs">
                                {task.scheduled_start ? (
                                  <div className="flex items-center space-x-1">
                                    <Calendar className="h-3 w-3" />
                                    <span>{new Date(task.scheduled_start).toLocaleDateString()}</span>
                                  </div>
                                ) : (
                                  <span className="text-gray-400">Not scheduled</span>
                                )}
                              </div>
                            </TableCell>
                            <TableCell>
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

export default NestedTableView;

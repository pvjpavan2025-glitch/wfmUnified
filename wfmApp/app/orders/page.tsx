"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { RefreshCw, Eye, Plus, Search, Filter } from 'lucide-react';

interface Order {
  id: string;
  external_id: string;
  source: string;
  status: string;
  priority: string;
  description: string;
  customer_id?: string;
  processes: string[];
  total_tasks: number;
  completed_tasks: number;
  created_at: string;
  requested_completion_date?: string;
}

interface ProcessInstance {
  id: string;
  process_definition_key: string;
  status: string;
  tasks: TaskInstance[];
  created_at: string;
}

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

const OrdersPage = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [orderDetails, setOrderDetails] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [priorityFilter, setPriorityFilter] = useState('all');

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      // Mock data for now - replace with actual API call
      const mockOrders: Order[] = [
        {
          id: '1',
          external_id: 'ORD-001',
          source: 'OSM',
          status: 'in_progress',
          priority: 'high',
          description: 'Service installation order',
          customer_id: 'CUST-001',
          processes: ['order_validation', 'technical_assessment'],
          total_tasks: 5,
          completed_tasks: 2,
          created_at: '2024-01-15T10:00:00Z',
          requested_completion_date: '2024-01-20T18:00:00Z'
        },
        {
          id: '2',
          external_id: 'ORD-002',
          source: 'PORTAL',
          status: 'pending',
          priority: 'medium',
          description: 'Equipment maintenance request',
          customer_id: 'CUST-002',
          processes: ['order_validation'],
          total_tasks: 3,
          completed_tasks: 0,
          created_at: '2024-01-15T14:30:00Z'
        }
      ];
      setOrders(mockOrders);
    } catch (error) {
      console.error('Failed to fetch orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchOrderDetails = async (orderId: string) => {
    try {
      // Mock data for now - replace with actual API call
      const mockDetails = {
        order: orders.find(o => o.id === orderId),
        process_instances: [
          {
            id: 'proc-1',
            process_definition_key: 'order_validation',
            status: 'completed',
            tasks: [
              {
                id: 'task-1',
                name: 'Validate Order Data',
                type: 'userTask',
                status: 'completed',
                assigned_technician_id: 'tech-1',
                assigned_lead_id: 'lead-1',
                created_at: '2024-01-15T10:05:00Z'
              },
              {
                id: 'task-2',
                name: 'Check Inventory',
                type: 'userTask',
                status: 'completed',
                assigned_technician_id: 'tech-2',
                assigned_lead_id: 'lead-1',
                created_at: '2024-01-15T10:15:00Z'
              }
            ],
            created_at: '2024-01-15T10:00:00Z'
          },
          {
            id: 'proc-2',
            process_definition_key: 'technical_assessment',
            status: 'in_progress',
            tasks: [
              {
                id: 'task-3',
                name: 'Technical Review',
                type: 'userTask',
                status: 'in_progress',
                assigned_technician_id: 'tech-3',
                assigned_lead_id: 'lead-2',
                scheduled_start: '2024-01-15T16:00:00Z',
                created_at: '2024-01-15T12:00:00Z'
              },
              {
                id: 'task-4',
                name: 'Resource Allocation',
                type: 'userTask',
                status: 'pending',
                created_at: '2024-01-15T12:00:00Z'
              },
              {
                id: 'task-5',
                name: 'Schedule Work',
                type: 'userTask',
                status: 'pending',
                created_at: '2024-01-15T12:00:00Z'
              }
            ],
            created_at: '2024-01-15T12:00:00Z'
          }
        ]
      };
      setOrderDetails(mockDetails);
    } catch (error) {
      console.error('Failed to fetch order details:', error);
    }
  };

  const refreshOrderProgress = async (orderId: string) => {
    try {
      // Call API to refresh order progress
      console.log('Refreshing progress for order:', orderId);
      await fetchOrders(); // Refresh the orders list
    } catch (error) {
      console.error('Failed to refresh order progress:', error);
    }
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

  const getPriorityBadgeVariant = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'destructive';
      case 'high': return 'secondary';
      case 'medium': return 'outline';
      case 'low': return 'outline';
      default: return 'outline';
    }
  };

  const filteredOrders = orders.filter(order => {
    const matchesSearch = order.external_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         order.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || order.status === statusFilter;
    const matchesPriority = priorityFilter === 'all' || order.priority === priorityFilter;
    return matchesSearch && matchesStatus && matchesPriority;
  });

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Orders</h1>
          <p className="text-muted-foreground">Manage and track order processing</p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          New Order
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search orders..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="max-w-sm"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>
            <Select value={priorityFilter} onValueChange={setPriorityFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Priority" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Priorities</SelectItem>
                <SelectItem value="urgent">Urgent</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Orders Table */}
      <Card>
        <CardHeader>
          <CardTitle>Orders ({filteredOrders.length})</CardTitle>
          <CardDescription>
            Track order progress and manage process execution
          </CardDescription>
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
                  <TableHead>Order ID</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Progress</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredOrders.map((order) => (
                  <TableRow key={order.id}>
                    <TableCell className="font-medium">{order.external_id}</TableCell>
                    <TableCell>{order.description}</TableCell>
                    <TableCell>{order.source}</TableCell>
                    <TableCell>
                      <Badge variant={getStatusBadgeVariant(order.status)}>
                        {order.status.replace('_', ' ')}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getPriorityBadgeVariant(order.priority)}>
                        {order.priority}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Progress 
                          value={order.total_tasks > 0 ? (order.completed_tasks / order.total_tasks) * 100 : 0} 
                          className="w-20"
                        />
                        <span className="text-sm text-muted-foreground">
                          {order.completed_tasks}/{order.total_tasks}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>{new Date(order.created_at).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => {
                                setSelectedOrder(order);
                                fetchOrderDetails(order.id);
                              }}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                            <DialogHeader>
                              <DialogTitle>Order Details - {selectedOrder?.external_id}</DialogTitle>
                              <DialogDescription>
                                View order progress, processes, and task assignments
                              </DialogDescription>
                            </DialogHeader>
                            {orderDetails && (
                              <Tabs defaultValue="overview" className="w-full">
                                <TabsList>
                                  <TabsTrigger value="overview">Overview</TabsTrigger>
                                  <TabsTrigger value="processes">Processes</TabsTrigger>
                                  <TabsTrigger value="tasks">Tasks</TabsTrigger>
                                </TabsList>
                                <TabsContent value="overview" className="space-y-4">
                                  <div className="grid grid-cols-2 gap-4">
                                    <div>
                                      <h4 className="font-semibold">Order Information</h4>
                                      <p><strong>ID:</strong> {selectedOrder?.external_id}</p>
                                      <p><strong>Source:</strong> {selectedOrder?.source}</p>
                                      <p><strong>Status:</strong> {selectedOrder?.status}</p>
                                      <p><strong>Priority:</strong> {selectedOrder?.priority}</p>
                                      <p><strong>Customer:</strong> {selectedOrder?.customer_id}</p>
                                    </div>
                                    <div>
                                      <h4 className="font-semibold">Progress</h4>
                                      <p><strong>Total Tasks:</strong> {selectedOrder?.total_tasks}</p>
                                      <p><strong>Completed:</strong> {selectedOrder?.completed_tasks}</p>
                                      <p><strong>Processes:</strong> {selectedOrder?.processes.length}</p>
                                      <Progress 
                                        value={selectedOrder?.total_tasks ? (selectedOrder.completed_tasks / selectedOrder.total_tasks) * 100 : 0} 
                                        className="mt-2"
                                      />
                                    </div>
                                  </div>
                                </TabsContent>
                                <TabsContent value="processes">
                                  <div className="space-y-4">
                                    {orderDetails.process_instances.map((process: ProcessInstance) => (
                                      <Card key={process.id}>
                                        <CardHeader>
                                          <div className="flex justify-between items-center">
                                            <CardTitle className="text-lg">{process.process_definition_key}</CardTitle>
                                            <Badge variant={getStatusBadgeVariant(process.status)}>
                                              {process.status}
                                            </Badge>
                                          </div>
                                        </CardHeader>
                                        <CardContent>
                                          <p><strong>Process ID:</strong> {process.id}</p>
                                          <p><strong>Tasks:</strong> {process.tasks.length}</p>
                                          <p><strong>Created:</strong> {new Date(process.created_at).toLocaleString()}</p>
                                        </CardContent>
                                      </Card>
                                    ))}
                                  </div>
                                </TabsContent>
                                <TabsContent value="tasks">
                                  <Table>
                                    <TableHeader>
                                      <TableRow>
                                        <TableHead>Task Name</TableHead>
                                        <TableHead>Type</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead>Assigned To</TableHead>
                                        <TableHead>Scheduled</TableHead>
                                      </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                      {orderDetails.process_instances.flatMap((process: ProcessInstance) => 
                                        process.tasks.map((task: TaskInstance) => (
                                          <TableRow key={task.id}>
                                            <TableCell>{task.name}</TableCell>
                                            <TableCell>{task.type}</TableCell>
                                            <TableCell>
                                              <Badge variant={getStatusBadgeVariant(task.status)}>
                                                {task.status}
                                              </Badge>
                                            </TableCell>
                                            <TableCell>
                                              {task.assigned_technician_id ? `Tech: ${task.assigned_technician_id}` : 'Unassigned'}
                                            </TableCell>
                                            <TableCell>
                                              {task.scheduled_start ? new Date(task.scheduled_start).toLocaleString() : 'Not scheduled'}
                                            </TableCell>
                                          </TableRow>
                                        ))
                                      )}
                                    </TableBody>
                                  </Table>
                                </TabsContent>
                              </Tabs>
                            )}
                          </DialogContent>
                        </Dialog>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => refreshOrderProgress(order.id)}
                        >
                          <RefreshCw className="h-4 w-4" />
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
    </div>
  );
};

export default OrdersPage;

"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Plus, Search, Filter, LayoutList, Table, List } from 'lucide-react';
import { ProtectedRoute } from '../../components/protected-route';
import AppShell from '@/components/app-shell';
import HierarchicalOrdersTable from '@/components/orders/hierarchical-orders-table';
import NestedTableView from '@/components/orders/nested-table-view';

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

const OrdersPage = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [priorityFilter, setPriorityFilter] = useState('all');
  const [viewMode, setViewMode] = useState<'hierarchical' | 'table'>('hierarchical');

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      // Mock data with complete hierarchy - replace with actual API call
      const mockOrders: Order[] = [
        {
          id: '1',
          external_id: 'ORD-001',
          source: 'OSM',
          status: 'in_progress',
          priority: 'high',
          description: 'Service installation order',
          customer_id: 'CUST-001',
          processes: [
            {
              id: 'proc-1',
              process_definition_key: 'order_validation',
              status: 'completed',
              completed_tasks: 2,
              total_tasks: 2,
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
              completed_tasks: 1,
              total_tasks: 3,
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
          ],
          total_tasks: 5,
          completed_tasks: 3,
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
          processes: [
            {
              id: 'proc-3',
              process_definition_key: 'equipment_assessment',
              status: 'pending',
              completed_tasks: 0,
              total_tasks: 3,
              tasks: [
                {
                  id: 'task-6',
                  name: 'Equipment Inspection',
                  type: 'userTask',
                  status: 'pending',
                  created_at: '2024-01-15T14:30:00Z'
                },
                {
                  id: 'task-7',
                  name: 'Maintenance Planning',
                  type: 'userTask',
                  status: 'pending',
                  created_at: '2024-01-15T14:30:00Z'
                },
                {
                  id: 'task-8',
                  name: 'Schedule Maintenance',
                  type: 'userTask',
                  status: 'pending',
                  created_at: '2024-01-15T14:30:00Z'
                }
              ],
              created_at: '2024-01-15T14:30:00Z'
            }
          ],
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

  const refreshOrderProgress = async (orderId: string) => {
    try {
      console.log('Refreshing progress for order:', orderId);
      await fetchOrders(); // Refresh the orders list
    } catch (error) {
      console.error('Failed to refresh order progress:', error);
    }
  };

  const filteredOrders = orders.filter(order => {
    const matchesSearch = order.external_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         order.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         order.processes.some(p => 
                           p.process_definition_key.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           p.tasks.some(t => t.name.toLowerCase().includes(searchTerm.toLowerCase()))
                         );
    const matchesStatus = statusFilter === 'all' || order.status === statusFilter;
    const matchesPriority = priorityFilter === 'all' || order.priority === priorityFilter;
    return matchesSearch && matchesStatus && matchesPriority;
  });

  // Calculate summary statistics
  const totalOrders = filteredOrders.length;
  const totalProcesses = filteredOrders.reduce((sum, order) => sum + order.processes.length, 0);
  const totalTasks = filteredOrders.reduce((sum, order) => sum + order.total_tasks, 0);
  const completedTasks = filteredOrders.reduce((sum, order) => sum + order.completed_tasks, 0);
  const pendingTasks = totalTasks - completedTasks;

  return (
    <ProtectedRoute>
      <AppShell title="Orders" subtitle="Manage and track order processing">
        <div className="space-y-6">
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

          {/* Summary Stats - Single Line */}
          <Card>
            <CardContent className="py-4">
              <div className="flex items-center justify-between w-full">
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-muted-foreground">Total Orders:</span>
                  <span className="text-lg font-bold">{totalOrders}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-muted-foreground">Active Processes:</span>
                  <span className="text-lg font-bold">{totalProcesses}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-muted-foreground">Completed Tasks:</span>
                  <span className="text-lg font-bold text-green-600">{completedTasks}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-muted-foreground">Pending Tasks:</span>
                  <span className="text-lg font-bold text-orange-600">{pendingTasks}</span>
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
                    placeholder="Search orders, processes, or tasks..."
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
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="in_progress">In Progress</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                    <SelectItem value="cancelled">Cancelled</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={priorityFilter} onValueChange={setPriorityFilter}>
                  <SelectTrigger className="w-40">
                    <SelectValue placeholder="All Priorities" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Priorities</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="low">Low</SelectItem>
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

          {/* Orders Display */}
          {viewMode === 'hierarchical' ? (
            <HierarchicalOrdersTable
              orders={filteredOrders}
              loading={loading}
              onRefreshOrder={refreshOrderProgress}
            />
          ) : (
            <NestedTableView
              orders={filteredOrders}
              loading={loading}
              onRefreshOrder={refreshOrderProgress}
            />
          )}
        </div>
      </AppShell>
    </ProtectedRoute>
  );
};

export default OrdersPage;

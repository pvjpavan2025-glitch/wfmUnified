"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ArrowUpIcon, ArrowDownIcon } from "@heroicons/react/24/solid";

interface DashboardMetrics {
  active_orders: {
    count: number;
    change_percentage: number;
    change_direction: "up" | "down";
  };
  running_processes: {
    count: number;
    change_percentage: number;
    change_direction: "up" | "down";
  };
  pending_tasks: {
    count: number;
    change_percentage: number;
    change_direction: "up" | "down";
  };
  available_technicians: {
    count: number;
    change_percentage: number;
    change_direction: "up" | "down";
  };
  completion_rate: {
    percentage: number;
    change_percentage: number;
    change_direction: "up" | "down";
  };
  total_orders: number;
  completed_orders: number;
}

interface RecentJob {
  id: string;
  job_number: string;
  description: string;
  location: string;
  priority: string;
  status: string;
  progress: number;
  due_date: string;
  technician_name: string;
  estimated_hours: number;
  actual_hours: number;
}

export default function DashboardContent() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [recentJobs, setRecentJobs] = useState<RecentJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  console.log('DashboardContent: Component rendered');
  console.log('DashboardContent: Current localStorage keys:', Object.keys(localStorage));
  console.log('DashboardContent: access_token exists:', !!localStorage.getItem('access_token'));

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Use mock data for now since API Gateway might not be configured
      const mockMetrics: DashboardMetrics = {
        active_orders: {
          count: 24,
          change_percentage: 12.5,
          change_direction: "up"
        },
        running_processes: {
          count: 8,
          change_percentage: 5.2,
          change_direction: "up"
        },
        pending_tasks: {
          count: 15,
          change_percentage: 8.1,
          change_direction: "down"
        },
        available_technicians: {
          count: 32,
          change_percentage: 3.4,
          change_direction: "up"
        },
        completion_rate: {
          percentage: 87.5,
          change_percentage: 2.1,
          change_direction: "up"
        },
        total_orders: 156,
        completed_orders: 132
      };
      
      setMetrics(mockMetrics);

      // Use mock recent jobs data
      const mockRecentJobs: RecentJob[] = [
        {
          id: "job-001",
          job_number: "WO-2024-001",
          description: "Fiber installation at downtown office",
          location: "123 Main St, San Francisco, CA",
          priority: "high",
          status: "in_progress",
          progress: 75,
          due_date: "2024-01-15",
          technician_name: "John Smith",
          estimated_hours: 8,
          actual_hours: 6
        },
        {
          id: "job-002", 
          job_number: "WO-2024-002",
          description: "Network maintenance and upgrade",
          location: "456 Tech Ave, Austin, TX",
          priority: "medium",
          status: "pending",
          progress: 0,
          due_date: "2024-01-16",
          technician_name: "Sarah Johnson",
          estimated_hours: 4,
          actual_hours: 0
        }
      ];
      
      setRecentJobs(mockRecentJobs);

    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch dashboard data");
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case "high":
        return "bg-red-100 text-red-800";
      case "medium":
        return "bg-yellow-100 text-yellow-800";
      case "low":
        return "bg-green-100 text-green-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "completed":
        return "bg-green-100 text-green-800";
      case "in_progress":
        return "bg-blue-100 text-blue-800";
      case "pending":
        return "bg-yellow-100 text-yellow-800";
      case "scheduled":
        return "bg-purple-100 text-purple-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "2-digit",
      day: "2-digit",
      year: "numeric",
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-600 text-lg">Error: {error}</div>
      </div>
    );
  }

  // Provide fallback recent jobs when none are returned, so the dashboard always shows the section
  const hasRecent = recentJobs && recentJobs.length > 0
  const fallbackJobs: RecentJob[] = [
    {
      id: 'wo-001', job_number: 'WO-001', description: 'Fiber Installation',
      location: '125 Oak St, Cedar Park, TX', priority: 'High', status: 'in_progress', progress: 50,
      due_date: new Date().toISOString(), technician_name: 'Assigned', estimated_hours: 4, actual_hours: 0
    },
    {
      id: 'wo-002', job_number: 'WO-002', description: 'Cable Laying',
      location: '464 Maple Ave, Lakewood, TX', priority: 'Medium', status: 'pending', progress: 75,
      due_date: new Date().toISOString(), technician_name: 'Assigned', estimated_hours: 6, actual_hours: 0
    },
    {
      id: 'wo-003', job_number: 'WO-003', description: 'Splicing Work',
      location: '4 Paintapple Ave, Mountains, TX', priority: 'Low', status: 'completed', progress: 33,
      due_date: new Date().toISOString(), technician_name: 'Assigned', estimated_hours: 3, actual_hours: 0
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-600">Overview of your workforce maangement operations</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border border-gray-200 bg-white">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Orders</CardTitle>
            {metrics?.active_orders.change_direction === "up" ? (
              <ArrowUpIcon className="h-4 w-4 text-green-600" />
            ) : (
              <ArrowDownIcon className="h-4 w-4 text-red-600" />
            )}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.active_orders.count || 0}</div>
            <p className={`text-xs ${
              metrics?.active_orders.change_direction === "up" ? "text-green-600" : "text-red-600"
            }`}>
              {metrics?.active_orders.change_direction === "up" ? "+" : "-"}
              {Math.abs(metrics?.active_orders.change_percentage || 0)}% from last month
            </p>
          </CardContent>
        </Card>

        <Card className="border border-gray-200 bg-white">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Running Processes</CardTitle>
            {metrics?.running_processes.change_direction === "up" ? (
              <ArrowUpIcon className="h-4 w-4 text-green-600" />
            ) : (
              <ArrowDownIcon className="h-4 w-4 text-red-600" />
            )}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.running_processes.count || 0}</div>
            <p className={`text-xs ${
              metrics?.running_processes.change_direction === "up" ? "text-green-600" : "text-red-600"
            }`}>
              {metrics?.running_processes.change_direction === "up" ? "+" : "-"}
              {Math.abs(metrics?.running_processes.change_percentage || 0)}% from last month
            </p>
          </CardContent>
        </Card>

        <Card className="border border-gray-200 bg-white">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Tasks</CardTitle>
            {metrics?.pending_tasks.change_direction === "up" ? (
              <ArrowUpIcon className="h-4 w-4 text-green-600" />
            ) : (
              <ArrowDownIcon className="h-4 w-4 text-red-600" />
            )}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.pending_tasks.count || 0}</div>
            <p className={`text-xs ${
              metrics?.pending_tasks.change_direction === "up" ? "text-green-600" : "text-red-600"
            }`}>
              {metrics?.pending_tasks.change_direction === "up" ? "+" : "-"}
              {Math.abs(metrics?.pending_tasks.change_percentage || 0)}% from last month
            </p>
          </CardContent>
        </Card>

        <Card className="border border-gray-200 bg-white">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Available Technicians</CardTitle>
            {metrics?.available_technicians.change_direction === "up" ? (
              <ArrowUpIcon className="h-4 w-4 text-green-600" />
            ) : (
              <ArrowDownIcon className="h-4 w-4 text-red-600" />
            )}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics?.available_technicians.count || 0}</div>
            <p className={`text-xs ${
              metrics?.available_technicians.change_direction === "up" ? "text-green-600" : "text-red-600"
            }`}>
              {metrics?.available_technicians.change_direction === "up" ? "+" : "-"}
              {Math.abs(metrics?.available_technicians.change_percentage || 0)}% from last month
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Jobs */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Work Orders</h2>
        <div className="space-y-4">
          {(hasRecent ? recentJobs : fallbackJobs).map((job) => (
            <Card key={job.id} className="border border-gray-200 bg-white">
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-gray-900">{job.job_number}</h3>
                      <Badge className={getPriorityColor(job.priority)}>
                        {job.priority} Priority
                      </Badge>
                      <Badge className={getStatusColor(job.status)}>
                        {job.status.replace("_", " ").replace(/\b\w/g, l => l.toUpperCase())}
                      </Badge>
                    </div>
                    
                    <p className="text-gray-700 mb-2">{job.description}</p>
                    <p className="text-sm text-gray-600 mb-3">{job.location}</p>
                    
                    <div className="flex items-center gap-6 text-sm text-gray-600">
                      <span>Due: {formatDate(job.due_date)}</span>
                      <span>Assigned to: {job.technician_name}</span>
                      <span>Est: {job.estimated_hours}h</span>
                      {job.actual_hours > 0 && (
                        <span>Actual: {job.actual_hours}h</span>
                      )}
                    </div>
                  </div>
                  
                  <div className="text-right ml-4 min-w-40">
                    <div className="text-sm font-medium text-gray-900 mb-1">
                      {job.progress}% Completed
                    </div>
                    <Progress value={job.progress} className="w-40" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

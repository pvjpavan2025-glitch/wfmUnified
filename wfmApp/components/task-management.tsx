"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  LayoutDashboard,
  CheckSquare,
  Calendar,
  Users,
  Building2,
  BarChart3,
  Settings,
  Bell,
  User,
  MapPin,
  Search,
  Filter,
  LogOut,
  Eye,
  UserCheck,
  Clock,
  AlertCircle,
  CheckCircle2,
  RefreshCw
} from "lucide-react"
import { useAuth } from "../contexts/auth-context"

interface TaskInstance {
  id: string
  name: string
  type: string
  status: "pending" | "in_progress" | "completed" | "failed"
  priority: "urgent" | "high" | "medium" | "low"
  order_id: string
  process_id: string
  process_definition_key: string
  assigned_technician_id?: string
  assigned_lead_id?: string
  technician_name?: string
  lead_name?: string
  required_skills: string[]
  estimated_duration?: number
  scheduled_start?: string
  scheduled_end?: string
  actual_start?: string
  actual_end?: string
  location?: string
  description?: string
  created_at: string
  updated_at: string
}

export default function TaskManagement() {
  const { user, logout } = useAuth()
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [priorityFilter, setPriorityFilter] = useState("all")
  const [assignmentFilter, setAssignmentFilter] = useState("all")
  const [tasks, setTasks] = useState<TaskInstance[]>([])
  const [selectedTask, setSelectedTask] = useState<TaskInstance | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchTasks()
  }, [])

  const fetchTasks = async () => {
    try {
      setLoading(true)
      // Mock data for now - replace with actual API call
      const mockTasks: TaskInstance[] = [
        {
          id: "task-001",
          name: "Validate Order Data",
          type: "userTask",
          status: "completed",
          priority: "high",
          order_id: "order-001",
          process_id: "proc-001",
          process_definition_key: "order_validation",
          assigned_technician_id: "tech-001",
          assigned_lead_id: "lead-001",
          technician_name: "Jacob Williams",
          lead_name: "Sarah Johnson",
          required_skills: ["data_validation", "order_processing"],
          estimated_duration: 60,
          scheduled_start: "2024-01-15T10:00:00Z",
          scheduled_end: "2024-01-15T11:00:00Z",
          actual_start: "2024-01-15T10:05:00Z",
          actual_end: "2024-01-15T10:45:00Z",
          location: "Cleveland, Ohio",
          description: "Validate incoming order data for completeness and accuracy",
          created_at: "2024-01-15T09:30:00Z",
          updated_at: "2024-01-15T10:45:00Z"
        },
        {
          id: "task-002",
          name: "Technical Assessment",
          type: "userTask",
          status: "in_progress",
          priority: "urgent",
          order_id: "order-002",
          process_id: "proc-002",
          process_definition_key: "technical_assessment",
          assigned_technician_id: "tech-002",
          assigned_lead_id: "lead-002",
          technician_name: "Mike Chen",
          lead_name: "Lisa Rodriguez",
          required_skills: ["technical_review", "fiber_optics"],
          estimated_duration: 120,
          scheduled_start: "2024-01-15T14:00:00Z",
          scheduled_end: "2024-01-15T16:00:00Z",
          actual_start: "2024-01-15T14:10:00Z",
          location: "Mount street, NYC",
          description: "Perform technical assessment for fiber installation",
          created_at: "2024-01-15T13:30:00Z",
          updated_at: "2024-01-15T14:10:00Z"
        },
        {
          id: "task-003",
          name: "Resource Allocation",
          type: "userTask",
          status: "pending",
          priority: "medium",
          order_id: "order-003",
          process_id: "proc-003",
          process_definition_key: "resource_planning",
          required_skills: ["resource_planning", "inventory_management"],
          estimated_duration: 90,
          location: "Kutch, Gujarat",
          description: "Allocate resources for upcoming installation work",
          created_at: "2024-01-15T12:00:00Z",
          updated_at: "2024-01-15T12:00:00Z"
        },
        {
          id: "task-004",
          name: "Cable Installation",
          type: "userTask",
          status: "completed",
          priority: "low",
          order_id: "order-004",
          process_id: "proc-004",
          process_definition_key: "installation_work",
          assigned_technician_id: "tech-003",
          assigned_lead_id: "lead-003",
          technician_name: "Joseph Joestar",
          lead_name: "Diana Prince",
          required_skills: ["cable_installation", "field_work"],
          estimated_duration: 240,
          scheduled_start: "2024-01-14T08:00:00Z",
          scheduled_end: "2024-01-14T12:00:00Z",
          actual_start: "2024-01-14T08:15:00Z",
          actual_end: "2024-01-14T11:45:00Z",
          location: "Panaji, Goa",
          description: "Install cable infrastructure for new customer",
          created_at: "2024-01-14T07:30:00Z",
          updated_at: "2024-01-14T11:45:00Z"
        }
      ]
      setTasks(mockTasks)
    } catch (error) {
      console.error('Failed to fetch tasks:', error)
    } finally {
      setLoading(false)
    }
  }

  const assignTask = async (taskId: string, technicianId: string, leadId: string) => {
    try {
      // Call API to assign task
      console.log('Assigning task:', taskId, 'to technician:', technicianId, 'lead:', leadId)
      await fetchTasks() // Refresh tasks
    } catch (error) {
      console.error('Failed to assign task:', error)
    }
  }

  const completeTask = async (taskId: string) => {
    try {
      // Call API to complete task
      console.log('Completing task:', taskId)
      await fetchTasks() // Refresh tasks
    } catch (error) {
      console.error('Failed to complete task:', error)
    }
  }

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case "completed": return "default"
      case "in_progress": return "secondary"
      case "pending": return "outline"
      case "failed": return "destructive"
      default: return "outline"
    }
  }

  const getPriorityBadgeVariant = (priority: string) => {
    switch (priority) {
      case "urgent": return "destructive"
      case "high": return "secondary"
      case "medium": return "outline"
      case "low": return "outline"
      default: return "outline"
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed": return <CheckCircle2 className="h-4 w-4 text-green-600" />
      case "in_progress": return <Clock className="h-4 w-4 text-blue-600" />
      case "pending": return <AlertCircle className="h-4 w-4 text-yellow-600" />
      case "failed": return <AlertCircle className="h-4 w-4 text-red-600" />
      default: return <AlertCircle className="h-4 w-4 text-gray-600" />
    }
  }

  const filteredTasks = tasks.filter((task) => {
    const matchesSearch =
      task.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (task.location && task.location.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (task.technician_name && task.technician_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      task.process_definition_key.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesStatus = statusFilter === "all" || task.status === statusFilter
    const matchesPriority = priorityFilter === "all" || task.priority === priorityFilter
    const matchesAssignment = assignmentFilter === "all" || 
      (assignmentFilter === "assigned" && task.assigned_technician_id) ||
      (assignmentFilter === "unassigned" && !task.assigned_technician_id)

    return matchesSearch && matchesStatus && matchesPriority && matchesAssignment
  })

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Task Management</h1>
          <p className="text-muted-foreground">Manage and track task assignments and progress</p>
        </div>
        <Button onClick={() => fetchTasks()}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
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
                placeholder="Search tasks..."
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
            <Select value={assignmentFilter} onValueChange={setAssignmentFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Assignment" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Tasks</SelectItem>
                <SelectItem value="assigned">Assigned</SelectItem>
                <SelectItem value="unassigned">Unassigned</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Tasks Table */}
      <Card>
        <CardHeader>
          <CardTitle>Tasks ({filteredTasks.length})</CardTitle>
          <CardDescription>
            Track task progress and manage assignments
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
                  <TableHead>Task</TableHead>
                  <TableHead>Process</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Assigned To</TableHead>
                  <TableHead>Schedule</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTasks.map((task) => (
                  <TableRow key={task.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{task.name}</div>
                        <div className="text-sm text-muted-foreground">{task.id}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="text-sm">{task.process_definition_key}</div>
                        <div className="text-xs text-muted-foreground">Order: {task.order_id}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(task.status)}
                        <Badge variant={getStatusBadgeVariant(task.status)}>
                          {task.status.replace('_', ' ')}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getPriorityBadgeVariant(task.priority)}>
                        {task.priority}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div>
                        {task.technician_name ? (
                          <div>
                            <div className="text-sm font-medium">{task.technician_name}</div>
                            <div className="text-xs text-muted-foreground">Lead: {task.lead_name}</div>
                          </div>
                        ) : (
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => {/* Open assignment dialog */}}
                          >
                            <UserCheck className="h-4 w-4 mr-1" />
                            Assign
                          </Button>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {task.scheduled_start ? (
                          <div>
                            <div>{new Date(task.scheduled_start).toLocaleDateString()}</div>
                            <div className="text-xs text-muted-foreground">
                              {new Date(task.scheduled_start).toLocaleTimeString()} - 
                              {task.scheduled_end && new Date(task.scheduled_end).toLocaleTimeString()}
                            </div>
                          </div>
                        ) : (
                          <span className="text-muted-foreground">Not scheduled</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1 text-sm">
                        <MapPin className="h-3 w-3 text-muted-foreground" />
                        {task.location || 'N/A'}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => setSelectedTask(task)}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-2xl">
                            <DialogHeader>
                              <DialogTitle>Task Details - {selectedTask?.name}</DialogTitle>
                              <DialogDescription>
                                View task information and progress
                              </DialogDescription>
                            </DialogHeader>
                            {selectedTask && (
                              <Tabs defaultValue="details" className="w-full">
                                <TabsList>
                                  <TabsTrigger value="details">Details</TabsTrigger>
                                  <TabsTrigger value="assignment">Assignment</TabsTrigger>
                                  <TabsTrigger value="timeline">Timeline</TabsTrigger>
                                </TabsList>
                                <TabsContent value="details" className="space-y-4">
                                  <div className="grid grid-cols-2 gap-4">
                                    <div>
                                      <h4 className="font-semibold">Task Information</h4>
                                      <p><strong>Name:</strong> {selectedTask.name}</p>
                                      <p><strong>Type:</strong> {selectedTask.type}</p>
                                      <p><strong>Status:</strong> {selectedTask.status}</p>
                                      <p><strong>Priority:</strong> {selectedTask.priority}</p>
                                      <p><strong>Description:</strong> {selectedTask.description}</p>
                                    </div>
                                    <div>
                                      <h4 className="font-semibold">Process Context</h4>
                                      <p><strong>Process:</strong> {selectedTask.process_definition_key}</p>
                                      <p><strong>Order ID:</strong> {selectedTask.order_id}</p>
                                      <p><strong>Process ID:</strong> {selectedTask.process_id}</p>
                                      <p><strong>Duration:</strong> {selectedTask.estimated_duration}min</p>
                                    </div>
                                  </div>
                                  <div>
                                    <h4 className="font-semibold">Required Skills</h4>
                                    <div className="flex gap-2 mt-2">
                                      {selectedTask.required_skills.map((skill) => (
                                        <Badge key={skill} variant="outline">{skill}</Badge>
                                      ))}
                                    </div>
                                  </div>
                                </TabsContent>
                                <TabsContent value="assignment">
                                  <div className="space-y-4">
                                    <div>
                                      <h4 className="font-semibold">Current Assignment</h4>
                                      <p><strong>Technician:</strong> {selectedTask.technician_name || 'Unassigned'}</p>
                                      <p><strong>Lead:</strong> {selectedTask.lead_name || 'Unassigned'}</p>
                                    </div>
                                    {!selectedTask.assigned_technician_id && (
                                      <Button onClick={() => {/* Open assignment form */}}>
                                        <UserCheck className="h-4 w-4 mr-2" />
                                        Assign Task
                                      </Button>
                                    )}
                                  </div>
                                </TabsContent>
                                <TabsContent value="timeline">
                                  <div className="space-y-4">
                                    <div>
                                      <h4 className="font-semibold">Schedule</h4>
                                      <p><strong>Scheduled Start:</strong> {selectedTask.scheduled_start ? new Date(selectedTask.scheduled_start).toLocaleString() : 'Not scheduled'}</p>
                                      <p><strong>Scheduled End:</strong> {selectedTask.scheduled_end ? new Date(selectedTask.scheduled_end).toLocaleString() : 'Not scheduled'}</p>
                                    </div>
                                    <div>
                                      <h4 className="font-semibold">Actual Times</h4>
                                      <p><strong>Actual Start:</strong> {selectedTask.actual_start ? new Date(selectedTask.actual_start).toLocaleString() : 'Not started'}</p>
                                      <p><strong>Actual End:</strong> {selectedTask.actual_end ? new Date(selectedTask.actual_end).toLocaleString() : 'Not completed'}</p>
                                    </div>
                                    <div>
                                      <h4 className="font-semibold">Timestamps</h4>
                                      <p><strong>Created:</strong> {new Date(selectedTask.created_at).toLocaleString()}</p>
                                      <p><strong>Updated:</strong> {new Date(selectedTask.updated_at).toLocaleString()}</p>
                                    </div>
                                  </div>
                                </TabsContent>
                              </Tabs>
                            )}
                          </DialogContent>
                        </Dialog>
                        {task.status === 'in_progress' && (
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => completeTask(task.id)}
                          >
                            <CheckCircle2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {filteredTasks.length === 0 && !loading && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No tasks found matching your criteria.</p>
        </div>
      )}
    </div>
  )
}

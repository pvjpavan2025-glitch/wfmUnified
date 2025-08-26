"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
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
} from "lucide-react"
import { useAuth } from "../contexts/auth-context"

interface Task {
  id: string
  title: string
  location: string
  status: "In Progress" | "Pending" | "Completed"
  priority: "High" | "Medium" | "Low"
  technician: string
  dueDate: string
}

export default function TaskManagement() {
  const { user, logout } = useAuth()
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("All Status")

  const tasks: Task[] = [
    {
      id: "JOB-001",
      title: "Fiber Installation",
      location: "Cleveland, Ohio",
      status: "In Progress",
      priority: "High",
      technician: "Jacob Williams",
      dueDate: "22/08/25",
    },
    {
      id: "JOB-002",
      title: "Cable Laying",
      location: "Mount street, NYC",
      status: "Pending",
      priority: "Medium",
      technician: "Sarah Williams",
      dueDate: "29/08/25",
    },
    {
      id: "JOB-003",
      title: "Splicing Work",
      location: "Kutch, Gujarat",
      status: "Pending",
      priority: "High",
      technician: "Assign",
      dueDate: "29/09/25",
    },
    {
      id: "JOB-003",
      title: "Cable Installation",
      location: "Panaji, Goa",
      status: "Completed",
      priority: "Low",
      technician: "Joseph Joestar",
      dueDate: "29/04/25",
    },
  ]

  const sidebarItems = [
    { icon: LayoutDashboard, label: "Dashboard", active: false, href: "/dashboard" },
    { icon: CheckSquare, label: "Orders", active: true, href: "/tasks" },
    { icon: Calendar, label: "Calendar", active: false, href: "/calendar" },
    { icon: Users, label: "Technicians", active: false, href: "/technicians" },
    { icon: Building2, label: "Vendors", active: false, href: "/vendors" },
    { icon: BarChart3, label: "Reports", active: false, href: "/reports" },
    { icon: Settings, label: "Settings", active: false, href: "/settings" },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case "In Progress":
        return "bg-blue-100 text-blue-800 border-blue-200"
      case "Pending":
        return "bg-yellow-100 text-yellow-800 border-yellow-200"
      case "Completed":
        return "bg-green-100 text-green-800 border-green-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "High":
        return "bg-red-100 text-red-800 border-red-200"
      case "Medium":
        return "bg-yellow-100 text-yellow-800 border-yellow-200"
      case "Low":
        return "bg-green-100 text-green-800 border-green-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  const getTechnicianColor = (technician: string) => {
    if (technician === "Assign") {
      return "bg-orange-500 text-white hover:bg-orange-600"
    }
    return "bg-transparent text-gray-900"
  }

  const filteredTasks = tasks.filter((task) => {
    const matchesSearch =
      task.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      task.location.toLowerCase().includes(searchTerm.toLowerCase()) ||
      task.technician.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesStatus = statusFilter === "All Status" || task.status === statusFilter

    return matchesSearch && matchesStatus
  })

  return (
    <div>
      {/* Order Management Content */}
      <div className="p-0 md:p-2 lg:p-4">
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Order Management</h2>
            <p className="text-gray-600">Manage and Track all field service jobs</p>
          </div>

          {/* Search and Filter Bar */}
          <div className="flex items-center gap-4 mb-6">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Search Tasks"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 bg-white border-gray-300 focus:border-orange-500 focus:ring-orange-500"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48 bg-white border-gray-300">
                <Filter className="w-4 h-4 mr-2 text-gray-400" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="All Status">All Status</SelectItem>
                <SelectItem value="In Progress">In Progress</SelectItem>
                <SelectItem value="Pending">Pending</SelectItem>
                <SelectItem value="Completed">Completed</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Tasks Table */}
          <Card className="border border-gray-200">
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="text-left py-4 px-6 text-sm font-medium text-gray-600">Task ID</th>
                      <th className="text-left py-4 px-6 text-sm font-medium text-gray-600">Task Title</th>
                      <th className="text-left py-4 px-6 text-sm font-medium text-gray-600">Location</th>
                      <th className="text-left py-4 px-6 text-sm font-medium text-gray-600">Status</th>
                      <th className="text-left py-4 px-6 text-sm font-medium text-gray-600">Priority</th>
                      <th className="text-left py-4 px-6 text-sm font-medium text-gray-600">Technician</th>
                      <th className="text-left py-4 px-6 text-sm font-medium text-gray-600">Due Date</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {filteredTasks.map((task, index) => (
                      <tr key={index} className="hover:bg-gray-50 transition-colors">
                        <td className="py-4 px-6 text-sm font-medium text-gray-900">{task.id}</td>
                        <td className="py-4 px-6 text-sm text-gray-900">{task.title}</td>
                        <td className="py-4 px-6 text-sm text-gray-600">
                          <div className="flex items-center gap-1">
                            <MapPin className="w-3 h-3 text-gray-400" />
                            {task.location}
                          </div>
                        </td>
                        <td className="py-4 px-6">
                          <Badge className={`text-xs font-medium border ${getStatusColor(task.status)}`}>
                            {task.status}
                          </Badge>
                        </td>
                        <td className="py-4 px-6">
                          <Badge className={`text-xs font-medium border ${getPriorityColor(task.priority)}`}>
                            {task.priority}
                          </Badge>
                        </td>
                        <td className="py-4 px-6">
                          {task.technician === "Assign" ? (
                            <Button
                              size="sm"
                              className={`text-xs px-3 py-1 rounded-full ${getTechnicianColor(task.technician)}`}
                            >
                              {task.technician}
                            </Button>
                          ) : (
                            <span className="text-sm text-gray-900">{task.technician}</span>
                          )}
                        </td>
                        <td className="py-4 px-6 text-sm text-gray-600">{task.dueDate}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {filteredTasks.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-500">No tasks found matching your criteria.</p>
            </div>
          )}
      </div>
    </div>
  )
}

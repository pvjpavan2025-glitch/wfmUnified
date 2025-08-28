"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
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
  Search,
  ChevronLeft,
  ChevronRight,
  LogOut,
} from "lucide-react"
import { useAuth } from "../contexts/auth-context"

interface Technician {
  id: string
  name: string
  specialization: string
  avatar: string
}

interface ScheduledTask {
  id: string
  jobNumber: string
  startTime: string
  endTime: string
  technicianId: string
  status: "in-progress" | "completed" | "newly-assigned"
  title: string
}

export default function TasksCalendar() {
  const { user, logout } = useAuth()
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("show-all")
  const [currentDate, setCurrentDate] = useState(new Date(2025, 6, 31)) // July 31, 2025

  const technicians: Technician[] = [
    { id: "1", name: "Joseph Joestar", specialization: "Fiber Installation", avatar: "JJ" },
    { id: "2", name: "Jonathan Joestar", specialization: "Repair Tech", avatar: "JN" },
    { id: "3", name: "Dio Brando", specialization: "Splicer Tech", avatar: "DB" },
    { id: "4", name: "Ceaser Zeppeli", specialization: "Fiber Installation", avatar: "CZ" },
    { id: "5", name: "Lisa Lisa", specialization: "Cable line installation", avatar: "LL" },
    { id: "6", name: "George Joestar", specialization: "Cable line installation", avatar: "GJ" },
    { id: "7", name: "Jotaro Kujo", specialization: "Cable line installation", avatar: "JK" },
  ]

  const scheduledTasks: ScheduledTask[] = [
    {
      id: "1",
      jobNumber: "JOB - 001",
      startTime: "6:30",
      endTime: "7:30",
      technicianId: "1",
      status: "in-progress",
      title: "Fiber Installation",
    },
    {
      id: "2",
      jobNumber: "JOB - 003",
      startTime: "8:00",
      endTime: "10:00",
      technicianId: "1",
      status: "in-progress",
      title: "Cable Repair",
    },
    {
      id: "3",
      jobNumber: "JOB - 010",
      startTime: "7:00",
      endTime: "8:00",
      technicianId: "3",
      status: "in-progress",
      title: "Splicing Work",
    },
    {
      id: "4",
      jobNumber: "JOB - 010",
      startTime: "9:00",
      endTime: "10:00",
      technicianId: "3",
      status: "completed",
      title: "Splicing Work",
    },
    {
      id: "5",
      jobNumber: "JOB - 010",
      startTime: "9:00",
      endTime: "10:00",
      technicianId: "4",
      status: "in-progress",
      title: "Fiber Installation",
    },
    {
      id: "6",
      jobNumber: "VEN - 010",
      startTime: "8:00",
      endTime: "10:00",
      technicianId: "5",
      status: "in-progress",
      title: "Vendor Installation",
    },
    {
      id: "7",
      jobNumber: "JOB - 010",
      startTime: "9:00",
      endTime: "10:00",
      technicianId: "6",
      status: "completed",
      title: "Cable Installation",
    },
    {
      id: "8",
      jobNumber: "JOB - 011",
      startTime: "8:00",
      endTime: "9:00",
      technicianId: "7",
      status: "in-progress",
      title: "Cable Installation",
    },
    {
      id: "9",
      jobNumber: "JOB - 010",
      startTime: "9:00",
      endTime: "10:00",
      technicianId: "7",
      status: "newly-assigned",
      title: "Cable Installation",
    },
    {
      id: "10",
      jobNumber: "JOB - 011",
      startTime: "10:30",
      endTime: "11:30",
      technicianId: "1",
      status: "in-progress",
      title: "Fiber Installation",
    },
  ]

  const sidebarItems = [
    { icon: LayoutDashboard, label: "Dashboard", active: false, href: "/dashboard" },
    { icon: CheckSquare, label: "Orders", active: false, href: "/tasks" },
    { icon: Calendar, label: "Calendar", active: true, href: "/calendar" },
    { icon: Users, label: "Technicians", active: false, href: "/technicians" },
    { icon: Building2, label: "Vendors", active: false, href: "/vendors" },
    { icon: BarChart3, label: "Reports", active: false, href: "/reports" },
    { icon: Settings, label: "Settings", active: false, href: "/settings" },
  ]

  const timeSlots = ["6 AM", "7 AM", "8 AM", "9 AM", "10 AM", "11 AM"]

  const getTaskStyle = (status: string) => {
    switch (status) {
      case "in-progress":
        return "bg-orange-300 text-orange-800 border-orange-400"
      case "completed":
        return "bg-gray-300 text-gray-700 border-gray-400"
      case "newly-assigned":
        return "bg-orange-200 text-orange-700 border-orange-300"
      default:
        return "bg-orange-300 text-orange-800 border-orange-400"
    }
  }

  const getTaskPosition = (startTime: string, endTime: string) => {
    const parseTime = (time: string) => {
      const [hours, minutes] = time.split(":").map(Number)
      return hours + minutes / 60
    }

    const start = parseTime(startTime)
    const end = parseTime(endTime)
    const duration = end - start

    // Calculate position relative to 6 AM start
    const leftPercent = ((start - 6) / 6) * 100
    const widthPercent = (duration / 6) * 100

    return { left: `${leftPercent}%`, width: `${widthPercent}%` }
  }

  const filteredTasks = scheduledTasks.filter((task) => {
    if (statusFilter !== "show-all" && task.status !== statusFilter) {
      return false
    }
    return true
  })

  const filteredTechnicians = technicians.filter(
    (tech) =>
      tech.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tech.specialization.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  const formatDate = (date: Date) => {
    const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    const months = [
      "January",
      "February",
      "March",
      "April",
      "May",
      "June",
      "July",
      "August",
      "September",
      "October",
      "November",
      "December",
    ]

    return `${days[date.getDay()]}, ${months[date.getMonth()]} ${date.getDate()}, ${date.getFullYear()}`
  }

  const navigateDate = (direction: "prev" | "next") => {
    const newDate = new Date(currentDate)
    newDate.setDate(currentDate.getDate() + (direction === "next" ? 1 : -1))
    setCurrentDate(newDate)
  }

  return (
    <div className="p-0 md:p-2 lg:p-4">
        {/* Calendar Content */}
        <div>
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Tasks Calendar</h2>
            <p className="text-gray-600">View all the scheduled tasks</p>
          </div>

          <div className="flex gap-6">
            {/* Left Panel - Technicians */}
            <div className="w-80 bg-white rounded-lg border border-gray-200">
              <div className="p-4 border-b border-gray-200">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <Input
                    placeholder="Search"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 bg-white border-gray-300 focus:border-orange-500 focus:ring-orange-500"
                  />
                </div>
              </div>
              <div className="p-4 space-y-4 max-h-96 overflow-y-auto">
                {filteredTechnicians.map((tech) => (
                  <div key={tech.id} className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
                      <span className="text-sm font-medium text-gray-600">{tech.avatar}</span>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{tech.name}</p>
                      <p className="text-sm text-gray-500">{tech.specialization}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right Panel - Calendar */}
            <div className="flex-1 bg-white rounded-lg border border-gray-200">
              {/* Date Navigation */}
              <div className="flex items-center justify-center gap-4 p-4 border-b border-gray-200">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigateDate("prev")}
                  className="text-gray-600 hover:text-gray-900"
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <div className="bg-orange-500 text-white px-6 py-2 rounded-lg font-medium">
                  {formatDate(currentDate)}
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigateDate("next")}
                  className="text-gray-600 hover:text-gray-900"
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>

              {/* Time Header */}
              <div className="grid grid-cols-7 border-b border-gray-200">
                <div className="p-4"></div>
                {timeSlots.map((time) => (
                  <div key={time} className="p-4 text-center font-medium text-gray-700 border-l border-gray-200">
                    {time}
                  </div>
                ))}
              </div>

              {/* Calendar Grid */}
              <div className="relative">
                {filteredTechnicians.map((tech, techIndex) => (
                  <div key={tech.id} className="grid grid-cols-7 border-b border-gray-200 min-h-16">
                    <div className="p-4 border-r border-gray-200 bg-gray-50">
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 bg-gray-300 rounded-full flex items-center justify-center">
                          <span className="text-xs font-medium text-gray-600">{tech.avatar}</span>
                        </div>
                        <span className="text-sm font-medium text-gray-700 truncate">{tech.name}</span>
                      </div>
                    </div>
                    <div className="col-span-6 relative p-2">
                      {filteredTasks
                        .filter((task) => task.technicianId === tech.id)
                        .map((task) => {
                          const position = getTaskPosition(task.startTime, task.endTime)
                          return (
                            <div
                              key={task.id}
                              className={`absolute top-2 bottom-2 rounded-md border px-2 py-1 text-xs font-medium ${getTaskStyle(task.status)}`}
                              style={position}
                            >
                              <div className="truncate">{task.jobNumber}</div>
                              <div className="text-xs opacity-75">
                                {task.startTime} - {task.endTime}
                              </div>
                            </div>
                          )
                        })}
                    </div>
                  </div>
                ))}
              </div>

              {/* Status Filter Buttons */}
              <div className="p-6 border-t border-gray-200">
                <div className="flex gap-4 justify-center">
                  <Button
                    variant={statusFilter === "in-progress" ? "default" : "outline"}
                    onClick={() => setStatusFilter(statusFilter === "in-progress" ? "show-all" : "in-progress")}
                    className={
                      statusFilter === "in-progress"
                        ? "bg-orange-300 text-orange-800 hover:bg-orange-400"
                        : "text-gray-600"
                    }
                  >
                    IN PROGRESS
                  </Button>
                  <Button
                    variant={statusFilter === "completed" ? "default" : "outline"}
                    onClick={() => setStatusFilter(statusFilter === "completed" ? "show-all" : "completed")}
                    className={
                      statusFilter === "completed" ? "bg-gray-400 text-gray-700 hover:bg-gray-500" : "text-gray-600"
                    }
                  >
                    TASK COMPLETED
                  </Button>
                  <Button
                    variant={statusFilter === "newly-assigned" ? "default" : "outline"}
                    onClick={() => setStatusFilter(statusFilter === "newly-assigned" ? "show-all" : "newly-assigned")}
                    className={
                      statusFilter === "newly-assigned"
                        ? "bg-orange-200 text-orange-700 hover:bg-orange-300"
                        : "text-gray-600"
                    }
                  >
                    NEWLY ASSIGNED
                  </Button>
                  <Button
                    variant={statusFilter === "show-all" ? "default" : "outline"}
                    onClick={() => setStatusFilter("show-all")}
                    className={
                      statusFilter === "show-all"
                        ? "bg-white text-orange-500 border-orange-500 hover:bg-orange-50"
                        : "text-gray-600"
                    }
                  >
                    SHOW ALL
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
    </div>
  )
}

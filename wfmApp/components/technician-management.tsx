"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
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
  Phone,
  Mail,
  Clock,
  MessageCircle,
  MapPin,
  Filter,
  Wrench,
  LogOut,
  UserCheck,
  UserX,
} from "lucide-react"
import { useAuth } from "../contexts/auth-context"

interface Technician {
  id: string
  name: string
  specialization: string
  phone: string
  email: string
  shift: string
  languages: string[]
  location: string
  status: "Available" | "On Duty" | "On Leave"
  avatar: string
}

export default function TechnicianManagement() {
  const { user, logout } = useAuth()
  const [skillFilter, setSkillFilter] = useState("Select Skill")
  const [proximityFilter, setProximityFilter] = useState("Select Proximity")
  const [shiftFilter, setShiftFilter] = useState("Select Shift")

  const technicians: Technician[] = [
    {
      id: "1",
      name: "Jacob William",
      specialization: "Splicing Specialist",
      phone: "+14 64589 12756",
      email: "jacobwilliams@hotmail.com",
      shift: "Day Shift",
      languages: ["English", "Spanish"],
      location: "Austin, Tx",
      status: "Available",
      avatar: "JW",
    },
    {
      id: "2",
      name: "Sarah William",
      specialization: "Installation Specialist",
      phone: "+14 64589 12756",
      email: "sarahwilliams@hotmail.com",
      shift: "Night Shift",
      languages: ["English", "French"],
      location: "Dallas, TX",
      status: "Available",
      avatar: "SW",
    },
    {
      id: "3",
      name: "Joseph Joestar",
      specialization: "Splicing Testing Specialist",
      phone: "+14 64589 12756",
      email: "joesphjoestar@hotmail.com",
      shift: "Day Shift",
      languages: ["English", "Japanese"],
      location: "Goa, Panaji",
      status: "On Duty",
      avatar: "JW",
    },
    {
      id: "4",
      name: "Jacob William",
      specialization: "Splicing Specialist",
      phone: "+14 64589 12756",
      email: "jacobwilliams@hotmail.com",
      shift: "Day Shift",
      languages: ["English", "Spanish"],
      location: "Austin, Tx",
      status: "On Leave",
      avatar: "JW",
    },
  ]

  const sidebarItems = [
    { icon: LayoutDashboard, label: "Dashboard", active: false, href: "/dashboard" },
    { icon: CheckSquare, label: "Orders", active: false, href: "/tasks" },
    { icon: Calendar, label: "Calendar", active: false, href: "/calendar" },
    { icon: Users, label: "Technicians", active: true, href: "/technicians" },
    { icon: Building2, label: "Vendors", active: false, href: "/vendors" },
    { icon: BarChart3, label: "Reports", active: false, href: "/reports" },
    { icon: Settings, label: "Settings", active: false, href: "/settings" },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Available":
        return "bg-orange-100 text-orange-800 border-orange-200"
      case "On Duty":
        return "bg-orange-100 text-orange-800 border-orange-200"
      case "On Leave":
        return "bg-gray-100 text-gray-700 border-gray-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  const getStatusCounts = () => {
    const available = technicians.filter((t) => t.status === "Available").length
    const onDuty = technicians.filter((t) => t.status === "On Duty").length
    const onLeave = technicians.filter((t) => t.status === "On Leave").length
    return { available, onDuty, onLeave }
  }

  const statusCounts = getStatusCounts()

  const filteredTechnicians = technicians.filter((tech) => {
    if (skillFilter !== "Select Skill" && !tech.specialization.toLowerCase().includes(skillFilter.toLowerCase())) {
      return false
    }
    if (
      proximityFilter !== "Select Proximity" &&
      !tech.location.toLowerCase().includes(proximityFilter.toLowerCase())
    ) {
      return false
    }
    if (shiftFilter !== "Select Shift" && tech.shift !== shiftFilter) {
      return false
    }
    return true
  })

  return (
    <div>
      {/* Technician Management Content */}
      <div className="p-0 md:p-2 lg:p-4">
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Technician Management</h2>
            <p className="text-gray-600">Manage and Assign Field Technicians</p>
          </div>

          {/* Status Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <Card className="border border-gray-200">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
                    <UserCheck className="w-6 h-6 text-orange-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">{statusCounts.available}</p>
                    <p className="text-sm text-gray-600">Available</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border border-gray-200">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
                    <Users className="w-6 h-6 text-orange-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">{statusCounts.onDuty}</p>
                    <p className="text-sm text-gray-600">On Duty</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border border-gray-200">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
                    <UserX className="w-6 h-6 text-orange-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">{statusCounts.onLeave}</p>
                    <p className="text-sm text-gray-600">On Leave</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Filter Section */}
          <div className="mb-8">
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2 text-orange-600">
                <Filter className="w-5 h-5" />
                <span className="font-medium">Filter By</span>
              </div>

              <div className="flex gap-4">
                <Select value={skillFilter} onValueChange={setSkillFilter}>
                  <SelectTrigger className="w-48 bg-white border-gray-300">
                    <Wrench className="w-4 h-4 mr-2 text-gray-400" />
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Select Skill">Select Skill</SelectItem>
                    <SelectItem value="Splicing">Splicing Specialist</SelectItem>
                    <SelectItem value="Installation">Installation Specialist</SelectItem>
                    <SelectItem value="Testing">Testing Specialist</SelectItem>
                  </SelectContent>
                </Select>

                <Select value={proximityFilter} onValueChange={setProximityFilter}>
                  <SelectTrigger className="w-48 bg-white border-gray-300">
                    <MapPin className="w-4 h-4 mr-2 text-gray-400" />
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Select Proximity">Select Proximity</SelectItem>
                    <SelectItem value="Austin">Austin, TX</SelectItem>
                    <SelectItem value="Dallas">Dallas, TX</SelectItem>
                    <SelectItem value="Goa">Goa, Panaji</SelectItem>
                  </SelectContent>
                </Select>

                <Select value={shiftFilter} onValueChange={setShiftFilter}>
                  <SelectTrigger className="w-48 bg-white border-gray-300">
                    <Clock className="w-4 h-4 mr-2 text-gray-400" />
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Select Shift">Select Shift</SelectItem>
                    <SelectItem value="Day Shift">Day Shift</SelectItem>
                    <SelectItem value="Night Shift">Night Shift</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* Technicians Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
            {filteredTechnicians.map((tech) => (
              <Card key={tech.id} className="border border-gray-200 hover:shadow-lg transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-gray-300 rounded-full flex items-center justify-center">
                        <span className="font-medium text-gray-700">{tech.avatar}</span>
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">{tech.name}</h3>
                        <p className="text-sm text-gray-600">{tech.specialization}</p>
                      </div>
                    </div>
                    <Badge className={`text-xs font-medium border ${getStatusColor(tech.status)}`}>{tech.status}</Badge>
                  </div>

                  <div className="space-y-3 mb-6">
                    <div className="flex items-center gap-3 text-sm text-gray-600">
                      <Phone className="w-4 h-4" />
                      <span>{tech.phone}</span>
                    </div>
                    <div className="flex items-center gap-3 text-sm text-gray-600">
                      <Mail className="w-4 h-4" />
                      <span>{tech.email}</span>
                    </div>
                    <div className="flex items-center gap-3 text-sm text-gray-600">
                      <Clock className="w-4 h-4" />
                      <span>{tech.shift}</span>
                    </div>
                    <div className="flex items-center gap-3 text-sm text-gray-600">
                      <MessageCircle className="w-4 h-4" />
                      <span>{tech.languages.join(", ")}</span>
                    </div>
                    <div className="flex items-center gap-3 text-sm text-gray-600">
                      <MapPin className="w-4 h-4" />
                      <span>{tech.location}</span>
                    </div>
                  </div>

                  <Button className="w-full bg-orange-500 hover:bg-orange-600 text-white">View Profile</Button>
                </CardContent>
              </Card>
            ))}
          </div>

          {filteredTechnicians.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-500">No technicians found matching your criteria.</p>
            </div>
          )}
      </div>
    </div>
  )
}

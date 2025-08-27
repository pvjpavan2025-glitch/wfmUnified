import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { LayoutDashboard, CheckSquare, Calendar, Users, Building2, BarChart3, Settings, Bell, User, MapPin, Clock, TrendingUp, TrendingDown } from 'lucide-react'

export default function Component() {
  const sidebarItems = [
    { icon: LayoutDashboard, label: "Dashboard", active: true },
    { icon: CheckSquare, label: "Orders" },
    { icon: Calendar, label: "Calendar" },
    { icon: Users, label: "Technicians" },
    { icon: Building2, label: "Vendors" },
    { icon: BarChart3, label: "Reports" },
    { icon: Settings, label: "Settings" },
  ]

  const metrics = [
    {
      title: "Active Jobs",
      value: "24",
      change: "+12% from last month",
      trend: "up",
      icon: CheckSquare
    },
    {
      title: "Available Technicians", 
      value: "18",
      change: "+5% from last month",
      trend: "up",
      icon: Users
    },
    {
      title: "Scheduled Today",
      value: "8", 
      change: "-2% from last month",
      trend: "down",
      icon: Calendar
    },
    {
      title: "Completion Rate",
      value: "94%",
      change: "+3% from last month", 
      trend: "up",
      icon: TrendingUp
    }
  ]

  const recentJobs = [
    {
      id: "JOB-001",
      title: "Fiber Installation",
      location: "125 Oak St, Cedar Park, TX",
      dueDate: "04/15/2024",
      progress: 50,
      priority: "High",
      assignee: "Jacob Wilson",
      status: "In Progress"
    },
    {
      id: "JOB-002", 
      title: "Cable Laying",
      location: "464 Maple Ave, Lakewood, TX",
      dueDate: "04/20/2024",
      progress: 75,
      priority: "Medium", 
      assignee: "Sarah Miller",
      status: "Pending"
    },
    {
      id: "JOB-003",
      title: "Splicing Work", 
      location: "4 Paintapple Ave, Mountains, TX",
      dueDate: "04/23/2024",
      progress: 33,
      priority: "Low",
      assignee: "Brian Harris", 
      status: "Completed"
    }
  ]

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "High": return "bg-red-100 text-red-800"
      case "Medium": return "bg-yellow-100 text-yellow-800" 
      case "Low": return "bg-green-100 text-green-800"
      default: return "bg-gray-100 text-gray-800"
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "In Progress": return "bg-blue-100 text-blue-800"
      case "Pending": return "bg-yellow-100 text-yellow-800"
      case "Completed": return "bg-green-100 text-green-800"
      default: return "bg-gray-100 text-gray-800"
    }
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-64 bg-white border-r border-gray-200">
        {/* Logo */}
        <div className="flex items-center gap-3 p-6 border-b border-gray-200">
          <div className="w-10 h-10 bg-orange-500 rounded-full flex items-center justify-center">
            <LayoutDashboard className="w-5 h-5 text-white" />
          </div>
          <span className="font-medium text-gray-900">App Name</span>
        </div>

        {/* Navigation */}
        <nav className="p-4">
          <ul className="space-y-1">
            {sidebarItems.map((item, index) => (
              <li key={index}>
                <a
                  href="#"
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    item.active
                      ? "bg-orange-500 text-white"
                      : "text-gray-700 hover:bg-gray-100"
                  }`}
                >
                  <item.icon className="w-4 h-4" />
                  {item.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Workforce Management</h1>
              <p className="text-sm text-gray-500">Admin Dashboard</p>
            </div>
            <div className="flex items-center gap-4">
              <Bell className="w-5 h-5 text-gray-400" />
              <User className="w-5 h-5 text-gray-400" />
            </div>
          </div>
        </header>

        {/* Dashboard Content */}
        <main className="p-6">
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Dashboard</h2>
            <p className="text-gray-600">Overview of Workforce Management operations</p>
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {metrics.map((metric, index) => (
              <Card key={index} className="border border-gray-200">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-gray-600">
                    {metric.title}
                  </CardTitle>
                  <metric.icon className="w-4 h-4 text-orange-500" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-gray-900 mb-1">
                    {metric.value}
                  </div>
                  <p className={`text-xs flex items-center gap-1 ${
                    metric.trend === "up" ? "text-green-600" : "text-red-600"
                  }`}>
                    {metric.trend === "up" ? (
                      <TrendingUp className="w-3 h-3" />
                    ) : (
                      <TrendingDown className="w-3 h-3" />
                    )}
                    {metric.change}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Recent Jobs */}
          <Card className="border border-gray-200">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-gray-900">Recent Jobs</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {recentJobs.map((job, index) => (
                <div key={index} className="space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-gray-500">
                          {job.id}
                        </span>
                        <Badge className={`text-xs ${getPriorityColor(job.priority)}`}>
                          {job.priority}
                        </Badge>
                      </div>
                      <h3 className="font-medium text-gray-900">{job.title}</h3>
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <div className="flex items-center gap-1">
                          <MapPin className="w-3 h-3" />
                          {job.location}
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          Due: {job.dueDate}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900 mb-1">
                        {job.assignee}
                      </div>
                      <Badge className={`text-xs ${getStatusColor(job.status)}`}>
                        {job.status}
                      </Badge>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">{job.progress}% Completed</span>
                    </div>
                    <Progress value={job.progress} className="h-2" />
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </main>
      </div>
    </div>
  )
}

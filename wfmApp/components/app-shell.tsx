"use client"

import React, { useState } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import {
  SidebarProvider,
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  SidebarRail,
  SidebarSeparator,
  useSidebar,
} from "@/components/ui/sidebar"
import { Bell, CalendarDays, CheckSquare, LayoutDashboard, Settings, Users, Building2, BarChart3, Workflow, Package, Menu, Activity, Plus, Folder, Play, FileText, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"

type NavSubItem = {
  label: string
  href: string
  icon: React.ComponentType<{ className?: string }>
}

type NavItem = {
  label: string
  href?: string
  icon: React.ComponentType<{ className?: string }>
  subItems?: NavSubItem[]
}

const navItems: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Orders", href: "/orders", icon: Package },
  { label: "Tasks", href: "/tasks", icon: CheckSquare },
  { label: "Calendar", href: "/calendar", icon: CalendarDays },
  { 
    label: "Modelling", 
    icon: Workflow,
    subItems: [
      { label: "New Process", href: "/modelling/new-process", icon: Plus },
      { label: "Manage Processes", href: "/modelling/manage-processes", icon: Folder },
      { label: "Instances", href: "/modelling/instances", icon: Play },
      { label: "Templates", href: "/modelling/templates", icon: FileText },
    ]
  },
  { label: "Vendors", href: "/vendors", icon: Building2 },
  { label: "Reports", href: "/reports", icon: BarChart3 },
  { label: "Settings", href: "/settings", icon: Settings },
]

// Custom hamburger menu component that's always visible
const HamburgerMenu = () => {
  const { toggleSidebar } = useSidebar()
  
  return (
    <button
      onClick={toggleSidebar}
      className="p-2 rounded-md hover:bg-gray-100 transition-colors"
      title="Toggle Sidebar"
    >
      <Menu className="w-5 h-5 text-gray-600" />
    </button>
  )
}

export function AppShell({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const [isModellingExpanded, setIsModellingExpanded] = useState(false)

  return (
    <SidebarProvider>
      <Sidebar collapsible="offcanvas" variant="sidebar">
        <SidebarHeader className="border-b border-gray-200">
          <div className="flex items-center gap-3 p-3">
            <div className="size-10 rounded-full flex items-center justify-center" style={{ background: "var(--wfm-orange-500, #FF7A00)" }}>
              <LayoutDashboard className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-medium text-gray-900">FSM</span>
              <p className="text-xs text-gray-500">Field Service Management</p>
            </div>
          </div>
        </SidebarHeader>
        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupContent>
              <SidebarMenu>
                {navItems.map((item) => {
                  const Icon = item.icon
                  
                  // Handle items with sub-items
                  if (item.subItems) {
                    const isModellingActive = pathname?.startsWith('/modelling')
                    return (
                      <SidebarMenuItem key={item.label}>
                        <SidebarMenuButton
                          isActive={!!isModellingActive}
                          className={cn(
                            isModellingActive
                              ? "text-white"
                              : "text-gray-700 hover:text-white",
                            "transition-colors cursor-pointer"
                          )}
                          style={isModellingActive ? { background: "var(--wfm-orange-500, #FF7A00)" } : {}}
                          onClick={() => setIsModellingExpanded(!isModellingExpanded)}
                        >
                          <Icon className="w-4 h-4" />
                          <span>{item.label}</span>
                          <ChevronRight className={cn("ml-auto h-4 w-4 transition-transform", isModellingExpanded && "rotate-90")} />
                        </SidebarMenuButton>
                        {isModellingExpanded && (
                          <SidebarMenuSub>
                            {item.subItems.map((subItem) => {
                              const subActive = pathname === subItem.href
                              const SubIcon = subItem.icon
                              return (
                                <SidebarMenuSubItem key={subItem.href}>
                                  <SidebarMenuSubButton
                                    isActive={!!subActive}
                                    className={cn(
                                      subActive
                                        ? "text-white"
                                        : "text-gray-600 hover:text-white",
                                      "transition-colors cursor-pointer"
                                    )}
                                    style={subActive ? { background: "var(--wfm-orange-500, #FF7A00)" } : {}}
                                    onClick={() => router.push(subItem.href)}
                                  >
                                    <SubIcon className="w-4 h-4" />
                                    <span>{subItem.label}</span>
                                  </SidebarMenuSubButton>
                                </SidebarMenuSubItem>
                              )
                            })}
                          </SidebarMenuSub>
                        )}
                      </SidebarMenuItem>
                    )
                  }
                  
                  // Handle regular items
                  const active = item.href && pathname?.startsWith(item.href)
                  return (
                    <SidebarMenuItem key={item.href || item.label}>
                      {item.href ? (
                        <Link href={item.href} prefetch={false} className="block">
                          <SidebarMenuButton
                            isActive={!!active}
                            className={cn(
                              active
                                ? "text-white"
                                : "text-gray-700 hover:text-white",
                              "transition-colors"
                            )}
                            style={active ? { background: "var(--wfm-orange-500, #FF7A00)" } : {}}
                          >
                            <Icon className="w-4 h-4" />
                            <span>{item.label}</span>
                          </SidebarMenuButton>
                        </Link>
                      ) : (
                        <SidebarMenuButton className="text-gray-700">
                          <Icon className="w-4 h-4" />
                          <span>{item.label}</span>
                        </SidebarMenuButton>
                      )}
                    </SidebarMenuItem>
                  )
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>
        <SidebarSeparator />
        <SidebarFooter className="text-xs text-gray-500">© 2025 Field Service</SidebarFooter>
        <SidebarRail />
      </Sidebar>

      <SidebarInset>
        <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
          <div className="flex h-14 items-center justify-between px-4">
            <div className="flex items-center gap-2">
              <div>
                <h1 className="text-lg font-semibold text-gray-900 leading-tight">{title}</h1>
                {subtitle ? <p className="text-xs text-gray-500">{subtitle}</p> : null}
              </div>
            </div>
            <div className="flex items-center gap-3 pr-1">
              <Bell className="w-5 h-5 text-gray-400" />
              <HamburgerMenu />
            </div>
          </div>
        </header>
        <div className="p-4 bg-gray-50 min-h-[calc(100svh-56px)]">{children}</div>
      </SidebarInset>
    </SidebarProvider>
  )
}

export default AppShell

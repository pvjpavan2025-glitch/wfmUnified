"use client"

import React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
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
  SidebarRail,
  SidebarSeparator,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { Bell, CalendarDays, CheckSquare, LayoutDashboard, Settings, Users, Building2, BarChart3, Workflow, Package } from "lucide-react"
import { cn } from "@/lib/utils"

type NavItem = {
  label: string
  href: string
  icon: React.ComponentType<{ className?: string }>
}

const navItems: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Orders", href: "/orders", icon: Package },
  { label: "Tasks", href: "/tasks", icon: CheckSquare },
  { label: "Calendar", href: "/calendar", icon: CalendarDays },
  { label: "Modelling", href: "/modelling", icon: Workflow },
  { label: "Vendors", href: "/vendors", icon: Building2 },
  { label: "Reports", href: "/reports", icon: BarChart3 },
  { label: "Settings", href: "/settings", icon: Settings },
]

export function AppShell({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  const pathname = usePathname()

  return (
    <SidebarProvider>
      <Sidebar collapsible="offcanvas" variant="sidebar">
        <SidebarHeader className="border-b border-gray-200">
          <div className="flex items-center gap-3 p-3">
            <div className="size-10 rounded-full flex items-center justify-center" style={{ background: "var(--wfm-orange-500, #FF7A00)" }}>
              <LayoutDashboard className="w-5 h-5 text-white" />
            </div>
            <span className="font-medium text-gray-900">App Name</span>
          </div>
        </SidebarHeader>
        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupContent>
              <SidebarMenu>
                {navItems.map((item) => {
                  const active = pathname?.startsWith(item.href)
                  const Icon = item.icon
                  return (
                    <SidebarMenuItem key={item.href}>
                      {/* Disable prefetch to avoid background RSC fetches for all sidebar routes */}
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
              <SidebarTrigger />
              <div>
                <h1 className="text-lg font-semibold text-gray-900 leading-tight">{title}</h1>
                {subtitle ? <p className="text-xs text-gray-500">{subtitle}</p> : null}
              </div>
            </div>
            <div className="flex items-center gap-3 pr-1">
              <Bell className="w-5 h-5 text-gray-400" />
            </div>
          </div>
        </header>
        <div className="p-4 bg-gray-50 min-h-[calc(100svh-56px)]">{children}</div>
      </SidebarInset>
    </SidebarProvider>
  )
}

export default AppShell

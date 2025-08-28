import { ProtectedRoute } from '@/components/protected-route'
import AppShell from '@/components/app-shell'
import TasksCalendar from '@/components/tasks-calendar'

export default function CalendarPage() {
  return (
    <ProtectedRoute>
      <AppShell title="Calendar" subtitle="View all the scheduled tasks">
        <TasksCalendar />
      </AppShell>
    </ProtectedRoute>
  )
}

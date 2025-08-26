import { ProtectedRoute } from '../../components/protected-route'
import AppShell from '@/components/app-shell'
import TaskManagement from '@/components/task-management'

export default function TasksPage() {
  return (
    <ProtectedRoute>
      <AppShell title="Work Orders" subtitle="Manage and Track all field service jobs">
        <TaskManagement />
      </AppShell>
    </ProtectedRoute>
  )
}

import { ProtectedRoute } from '../../components/protected-route'
import AppShell from '@/components/app-shell'
import DashboardContent from '@/components/dashboard-content'

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <AppShell title="Field Service Management" subtitle="Admin Dashboard">
        <DashboardContent />
      </AppShell>
    </ProtectedRoute>
  )
}

import AppShell from '@/components/app-shell'
import { ProtectedRoute } from '@/components/protected-route'

export default function ReportsPage() {
  return (
    <ProtectedRoute>
      <AppShell title="Reports" subtitle="Analytics and insights (coming soon)">
        <div className="bg-white rounded-lg border border-gray-200 p-6 text-gray-700">
          <p>Reports module is coming soon.</p>
        </div>
      </AppShell>
    </ProtectedRoute>
  )
}

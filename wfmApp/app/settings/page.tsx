import AppShell from '@/components/app-shell'
import { ProtectedRoute } from '@/components/protected-route'

export default function SettingsPage() {
  return (
    <ProtectedRoute>
      <AppShell title="Settings" subtitle="Application preferences (coming soon)">
        <div className="bg-white rounded-lg border border-gray-200 p-6 text-gray-700">
          <p>Settings module is coming soon.</p>
        </div>
      </AppShell>
    </ProtectedRoute>
  )
}

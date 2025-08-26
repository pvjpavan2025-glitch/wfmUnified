import { ProtectedRoute } from "../../components/protected-route"
import AppShell from '@/components/app-shell'
import TechnicianManagement from "@/components/technician-management"

export default function TechniciansPage() {
  return (
    <ProtectedRoute>
      <AppShell title="Technicians" subtitle="Manage and Assign Field Technicians">
        <TechnicianManagement />
      </AppShell>
    </ProtectedRoute>
  )
}

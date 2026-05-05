import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { LoginPage } from '../features/auth/LoginPage'
import { ActivatePage } from '../features/auth/ActivatePage'
import { ActivateSuccessPage } from '../features/auth/ActivateSuccessPage'
import { HomePage } from '../features/home/HomePage'
import { AuthProvider, useAuth } from '../features/auth/authContext'
import { ServiceOrdersPage } from '../features/serviceOrders/ServiceOrdersPage'
import { ServiceOrderDetailPage } from '../features/serviceOrders/ServiceOrderDetailPage'
import { HousekeepingTaskBoardPage } from '../modules/housekeeping/pages/HousekeepingTaskBoardPage'
import { HousekeepingRoomsPage } from '../modules/housekeeping/pages/HousekeepingRoomsPage'
import { HousekeepingKpiPage } from '../modules/housekeeping/pages/HousekeepingKpiPage'
import { HousekeepingAuditLogsPage } from '../modules/housekeeping/pages/HousekeepingAuditLogsPage'
import { MaintenanceOrdersPage } from '../modules/maintenance/pages/MaintenanceOrdersPage'
import { MaintenanceOrderDetailPage } from '../modules/maintenance/pages/MaintenanceOrderDetailPage'
import { MaintenanceOrderFormPage } from '../modules/maintenance/pages/MaintenanceOrderFormPage'
import { PMSchedulesPage } from '../modules/maintenance/pages/PMSchedulesPage'
import { PMCalendarPage } from '../modules/maintenance/pages/PMCalendarPage'
import { AssetsPage } from '../modules/maintenance/pages/AssetsPage'
import { AssetDetailPage, AssetEditPage } from '../modules/maintenance/pages/AssetDetailPage'
import { QRScanPage } from '../modules/maintenance/pages/QRScanPage'
import { MaintenanceAuditLogsPage } from '../modules/maintenance/pages/MaintenanceAuditLogsPage'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { auth } = useAuth()
  if (!auth?.accessToken) {
    return <Navigate to="/login" replace />
  }
  return children
}

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/activate" element={<ActivatePage />} />
          <Route path="/activate/success" element={<ActivateSuccessPage />} />
          <Route
            path="/home"
            element={
              <PrivateRoute>
                <HomePage />
              </PrivateRoute>
            }
          />
          <Route
            path="/service-orders"
            element={
              <PrivateRoute>
                <ServiceOrdersPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/service-orders/:id"
            element={
              <PrivateRoute>
                <ServiceOrderDetailPage />
              </PrivateRoute>
            }
          />
          <Route path="/housekeeping/tasks" element={<PrivateRoute><HousekeepingTaskBoardPage /></PrivateRoute>} />
          <Route path="/housekeeping/rooms" element={<PrivateRoute><HousekeepingRoomsPage /></PrivateRoute>} />
          <Route path="/housekeeping/kpi" element={<PrivateRoute><HousekeepingKpiPage /></PrivateRoute>} />
          <Route path="/housekeeping/audit-logs" element={<PrivateRoute><HousekeepingAuditLogsPage /></PrivateRoute>} />
          <Route path="/maintenance/orders" element={<PrivateRoute><MaintenanceOrdersPage /></PrivateRoute>} />
          <Route path="/maintenance/orders/new" element={<PrivateRoute><MaintenanceOrderFormPage /></PrivateRoute>} />
          <Route path="/maintenance/orders/:id" element={<PrivateRoute><MaintenanceOrderDetailPage /></PrivateRoute>} />
          <Route path="/maintenance/orders/:id/edit" element={<PrivateRoute><MaintenanceOrderFormPage /></PrivateRoute>} />
          <Route path="/maintenance/pm-schedules" element={<PrivateRoute><PMSchedulesPage /></PrivateRoute>} />
          <Route path="/maintenance/pm-calendar" element={<PrivateRoute><PMCalendarPage /></PrivateRoute>} />
          <Route path="/maintenance/assets" element={<PrivateRoute><AssetsPage /></PrivateRoute>} />
          <Route path="/maintenance/assets/new" element={<PrivateRoute><AssetsPage /></PrivateRoute>} />
          <Route path="/maintenance/assets/:id" element={<PrivateRoute><AssetDetailPage /></PrivateRoute>} />
          <Route path="/maintenance/assets/:id/edit" element={<PrivateRoute><AssetEditPage /></PrivateRoute>} />
          <Route path="/maintenance/qr-scan" element={<PrivateRoute><QRScanPage /></PrivateRoute>} />
          <Route path="/maintenance/audit-logs" element={<PrivateRoute><MaintenanceAuditLogsPage /></PrivateRoute>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

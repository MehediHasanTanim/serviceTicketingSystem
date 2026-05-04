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
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

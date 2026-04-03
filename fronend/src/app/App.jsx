import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { LoginPage } from '../features/auth/LoginPage.jsx'
import { HomePage } from '../features/home/HomePage.jsx'
import { AuthProvider, useAuth } from '../features/auth/authContext.jsx'

function PrivateRoute({ children }) {
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
          <Route
            path="/home"
            element={
              <PrivateRoute>
                <HomePage />
              </PrivateRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

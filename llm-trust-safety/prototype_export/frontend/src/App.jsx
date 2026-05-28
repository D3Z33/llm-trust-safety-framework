import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './hooks/useAuth'
import Sidebar from './components/Sidebar'
import { ToastContainer } from './components/ui'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import EvaluatePage from './pages/EvaluatePage'
import LogsPage from './pages/LogsPage'
import SessionsPage from './pages/SessionsPage'
import OWASPPage from './pages/OWASPPage'
import AlertasPage from './pages/AlertasPage'
import ConformidadePage from './pages/ConformidadePage'
import ThreatIntelPage from './pages/ThreatIntelPage'
import PoliticasPage from './pages/PoliticasPage'
import AnalyticsPage from './pages/AnalyticsPage'
import UsuariosPage from './pages/UsuariosPage'
import ConfiguracoesPage from './pages/ConfiguracoesPage'

function ProtectedLayout({ children, minRole }) {
  const { isAuthenticated, loading, user } = useAuth()

  if (loading) return (
    <div className="flex items-center justify-center h-screen bg-gray-950">
      <div className="w-12 h-12 rounded-full border-4 border-blue-500/20 border-t-blue-500 animate-spin" />
    </div>
  )
  if (!isAuthenticated) return <Navigate to="/login" replace />

  const ROLE_RANK = { admin: 3, analyst: 2, viewer: 1, api_user: 1 }
  if (minRole && (ROLE_RANK[user?.role] || 0) < (ROLE_RANK[minRole] || 0)) {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-950">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  )
}

function AppRoutes() {
  const { isAuthenticated } = useAuth()
  return (
    <Routes>
      <Route path="/login" element={
        isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />
      } />
      <Route path="/dashboard" element={<ProtectedLayout><DashboardPage /></ProtectedLayout>} />
      <Route path="/avaliar" element={<ProtectedLayout><EvaluatePage /></ProtectedLayout>} />
      <Route path="/analytics" element={<ProtectedLayout><AnalyticsPage /></ProtectedLayout>} />
      <Route path="/logs" element={<ProtectedLayout><LogsPage /></ProtectedLayout>} />
      <Route path="/sessoes" element={<ProtectedLayout><SessionsPage /></ProtectedLayout>} />
      <Route path="/alertas" element={<ProtectedLayout><AlertasPage /></ProtectedLayout>} />
      <Route path="/conformidade" element={<ProtectedLayout><ConformidadePage /></ProtectedLayout>} />
      <Route path="/ameacas" element={<ProtectedLayout><ThreatIntelPage /></ProtectedLayout>} />
      <Route path="/owasp" element={<ProtectedLayout><OWASPPage /></ProtectedLayout>} />
      <Route path="/politicas" element={<ProtectedLayout minRole="analyst"><PoliticasPage /></ProtectedLayout>} />
      <Route path="/usuarios" element={<ProtectedLayout minRole="admin"><UsuariosPage /></ProtectedLayout>} />
      <Route path="/configuracoes" element={<ProtectedLayout minRole="analyst"><ConfiguracoesPage /></ProtectedLayout>} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
        <ToastContainer />
      </AuthProvider>
    </BrowserRouter>
  )
}

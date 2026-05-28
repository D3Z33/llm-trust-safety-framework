import { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from '../utils/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Verificar token salvo ao iniciar
    const token = localStorage.getItem('ltf_token')
    const savedUser = localStorage.getItem('ltf_user')

    if (token && savedUser) {
      try {
        const userData = JSON.parse(savedUser)
        setUser(userData)
        setIsAuthenticated(true)
      } catch {
        localStorage.removeItem('ltf_token')
        localStorage.removeItem('ltf_user')
      }
    }
    setLoading(false)
  }, [])

  const login = async (username, password) => {
    const res = await authAPI.login(username, password)
    const { access_token, refresh_token, user: userData } = res.data

    localStorage.setItem('ltf_token', access_token)
    if (refresh_token) localStorage.setItem('ltf_refresh', refresh_token)
    localStorage.setItem('ltf_user', JSON.stringify(userData))

    setUser(userData)
    setIsAuthenticated(true)
    return userData
  }

  const logout = () => {
    localStorage.removeItem('ltf_token')
    localStorage.removeItem('ltf_refresh')
    localStorage.removeItem('ltf_user')
    setUser(null)
    setIsAuthenticated(false)
    window.location.href = '/login'
  }

  const updateUser = (updates) => {
    const updated = { ...user, ...updates }
    setUser(updated)
    localStorage.setItem('ltf_user', JSON.stringify(updated))
  }

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, loading, login, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth deve ser usado dentro de AuthProvider')
  return ctx
}

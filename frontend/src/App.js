import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import { Toaster } from '@/components/ui/sonner';
import { toast } from 'sonner';
import AuthPage from './pages/AuthPage';
import DashboardPage from './pages/DashboardPage';
import CriteriaPage from './pages/CriteriaPage';
import ClausesPage from './pages/ClausesPage';
import AuditPage from './pages/AuditPage';
import RecommendationsPage from './pages/RecommendationsPage';
import ReportsPage from './pages/ReportsPage';
import ERMRiskPage from './pages/ERMRiskPage';
import '@/App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const AppContext = React.createContext();

// Configure axios interceptor to add token to all requests
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Configure axios interceptor to handle 401 errors
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
      window.location.href = '/auth';
    }
    return Promise.reject(error);
  }
);

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchCurrentUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchCurrentUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Error fetching user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { access_token, user: userData } = response.data;
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(userData);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      toast.success('Login berhasil!');
      return true;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login gagal');
      return false;
    }
  };

  const register = async (email, password, name, role) => {
    try {
      await axios.post(`${API}/auth/register`, { email, password, name, role });
      toast.success('Registrasi berhasil! Silakan login.');
      return true;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registrasi gagal');
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
    toast.info('Anda telah logout');
  };

  const contextValue = {
    user,
    login,
    register,
    logout,
    API,
    isAuthenticated: !!user
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6">
        <div className="w-full max-w-md rounded-[32px] border border-white/70 bg-white/75 p-10 text-center shadow-[0_28px_90px_rgba(34,57,49,0.14)] backdrop-blur-xl">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-[22px] bg-[linear-gradient(135deg,#0f5f53_0%,#2b8a78_100%)] shadow-[0_18px_40px_rgba(15,95,83,0.24)]">
            <div className="h-7 w-7 animate-spin rounded-full border-[3px] border-white/40 border-t-white"></div>
          </div>
          <h1 className="mt-6 text-3xl font-extrabold text-slate-950">InsightK3</h1>
          <p className="mt-2 text-sm text-slate-600">Menyiapkan workspace audit dan risk intelligence.</p>
        </div>
      </div>
    );
  }

  return (
    <AppContext.Provider value={contextValue}>
      <BrowserRouter>
        <div className="App">
          <Routes>
            <Route
              path="/auth"
              element={!user ? <AuthPage /> : <Navigate to="/" replace />}
            />
            <Route
              path="/"
              element={user ? <DashboardPage /> : <Navigate to="/auth" replace />}
            />
            <Route
              path="/criteria"
              element={user ? <CriteriaPage /> : <Navigate to="/auth" replace />}
            />
            <Route
              path="/clauses"
              element={user ? <ClausesPage /> : <Navigate to="/auth" replace />}
            />
            <Route
              path="/audit"
              element={user ? <AuditPage /> : <Navigate to="/auth" replace />}
            />
            <Route
              path="/recommendations"
              element={user ? <RecommendationsPage /> : <Navigate to="/auth" replace />}
            />
            <Route
              path="/reports"
              element={user ? <ReportsPage /> : <Navigate to="/auth" replace />}
            />
            <Route
              path="/erm-risk"
              element={user ? <ERMRiskPage /> : <Navigate to="/auth" replace />}
            />
          </Routes>
          <Toaster position="top-right" richColors />
        </div>
      </BrowserRouter>
    </AppContext.Provider>
  );
}

export default App;

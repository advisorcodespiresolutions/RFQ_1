import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';

// Components
import Layout from './components/Layout/Layout';
import Login from './pages/Auth/Login';
import Dashboard from './pages/Dashboard/Dashboard';
import Partners from './pages/Partners/Partners';
import PartnerDetail from './pages/Partners/PartnerDetail';
import Feedback from './pages/Feedback/Feedback';
import Analytics from './pages/Analytics/Analytics';
import Admin from './pages/Admin/Admin';
import VendorProfile from './pages/Vendor/VendorProfile';
import VendorDocuments from './pages/Vendor/VendorDocuments';

// Context
import { AuthProvider, useAuth } from './contexts/AuthContext';

// Types
import { UserRole } from './types/auth';

// Styles
import './App.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Protected Route Component
const ProtectedRoute: React.FC<{ 
  children: React.ReactNode; 
  allowedRoles?: UserRole[];
}> = ({ children, allowedRoles }) => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

// Main App Component
const AppContent: React.FC = () => {
  const { user } = useAuth();

  if (!user) {
    return (
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </Router>
    );
  }

  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          
          <Route path="/partners" element={
            <ProtectedRoute allowedRoles={[UserRole.ADMIN, UserRole.IT_MANAGER]}>
              <Partners />
            </ProtectedRoute>
          } />
          
          <Route path="/partners/:id" element={
            <ProtectedRoute allowedRoles={[UserRole.ADMIN, UserRole.IT_MANAGER]}>
              <PartnerDetail />
            </ProtectedRoute>
          } />
          
          <Route path="/feedback" element={
            <ProtectedRoute allowedRoles={[UserRole.ADMIN, UserRole.IT_MANAGER]}>
              <Feedback />
            </ProtectedRoute>
          } />
          
          <Route path="/analytics" element={
            <ProtectedRoute allowedRoles={[UserRole.ADMIN, UserRole.IT_MANAGER]}>
              <Analytics />
            </ProtectedRoute>
          } />
          
          <Route path="/admin" element={
            <ProtectedRoute allowedRoles={[UserRole.ADMIN, UserRole.SUPER_ADMIN]}>
              <Admin />
            </ProtectedRoute>
          } />
          
          <Route path="/vendor/profile" element={
            <ProtectedRoute allowedRoles={[UserRole.VENDOR]}>
              <VendorProfile />
            </ProtectedRoute>
          } />
          
          <Route path="/vendor/documents" element={
            <ProtectedRoute allowedRoles={[UserRole.VENDOR]}>
              <VendorDocuments />
            </ProtectedRoute>
          } />
          
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Layout>
    </Router>
  );
};

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <AppContent />
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
            success: {
              duration: 3000,
              iconTheme: {
                primary: '#10B981',
                secondary: '#fff',
              },
            },
            error: {
              duration: 5000,
              iconTheme: {
                primary: '#EF4444',
                secondary: '#fff',
              },
            },
          }}
        />
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';

// Layout
import Layout from './components/Layout/Layout';

// Pages
import Dashboard from './pages/Dashboard';
import QuotesList from './pages/Quotes/QuotesList';
import QuoteDetail from './pages/Quotes/QuoteDetail';
import CreateQuote from './pages/Quotes/CreateQuote';
import FileUpload from './pages/Files/FileUpload';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import Login from './pages/Auth/Login';

// Contexts
import { AuthProvider } from './contexts/AuthContext';
import { useAuth } from './contexts/AuthContext';

// Styles
import './index.css';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Layout>{children}</Layout>;
};

// Main App Component
const AppContent: React.FC = () => {
  const { isAuthenticated } = useAuth();

  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route 
          path="/login" 
          element={
            isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />
          } 
        />

        {/* Protected Routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/quotes"
          element={
            <ProtectedRoute>
              <QuotesList />
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/quotes/new"
          element={
            <ProtectedRoute>
              <CreateQuote />
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/quotes/:id"
          element={
            <ProtectedRoute>
              <QuoteDetail />
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/files/upload"
          element={
            <ProtectedRoute>
              <FileUpload />
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/analytics"
          element={
            <ProtectedRoute>
              <Analytics />
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <Settings />
            </ProtectedRoute>
          }
        />

        {/* Default Route */}
        <Route 
          path="/" 
          element={<Navigate to="/dashboard" replace />} 
        />
        
        {/* Catch all route */}
        <Route 
          path="*" 
          element={
            <ProtectedRoute>
              <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                  <h1 className="text-4xl font-bold text-gray-900 mb-4">404</h1>
                  <p className="text-gray-600">Page not found</p>
                </div>
              </div>
            </ProtectedRoute>
          } 
        />
      </Routes>
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
              style: {
                background: '#22c55e',
              },
            },
            error: {
              duration: 5000,
              style: {
                background: '#ef4444',
              },
            },
          }}
        />
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
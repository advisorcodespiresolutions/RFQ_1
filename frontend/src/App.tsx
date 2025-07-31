import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';
import TimeClock from './components/TimeClock';
import ManagerDashboard from './components/ManagerDashboard';
import './App.css';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Toaster position="top-right" />
          
          {/* Header */}
          <header className="bg-white shadow-sm border-b">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between items-center py-4">
                <div className="flex items-center">
                  <h1 className="text-xl font-semibold text-gray-900">
                    Time & Attendance System
                  </h1>
                  <span className="ml-2 px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                    California Retail
                  </span>
                </div>
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-gray-500">
                    California Labor Code Compliant
                  </span>
                </div>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <Routes>
              <Route path="/" element={<Navigate to="/time-clock" replace />} />
              <Route 
                path="/time-clock" 
                element={
                  <div className="max-w-4xl mx-auto">
                    <div className="text-center mb-8">
                      <h2 className="text-3xl font-bold text-gray-900 mb-2">
                        Employee Time Clock
                      </h2>
                      <p className="text-gray-600">
                        Clock in and out with California compliance tracking
                      </p>
                    </div>
                    <TimeClock 
                      employeeId={1}
                      employeeName="John Doe"
                      locationName="Downtown Store"
                    />
                  </div>
                } 
              />
              <Route 
                path="/manager" 
                element={
                  <ManagerDashboard managerId={1} />
                } 
              />
              <Route 
                path="/reports" 
                element={
                  <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">
                      Reports & Analytics
                    </h2>
                    <p className="text-gray-600">
                      Comprehensive reporting and compliance analytics coming soon...
                    </p>
                  </div>
                } 
              />
            </Routes>
          </main>

          {/* Footer */}
          <footer className="bg-white border-t mt-12">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
              <div className="flex justify-between items-center">
                <div className="text-sm text-gray-500">
                  © 2024 Time & Attendance System. California Labor Code Compliant.
                </div>
                <div className="flex space-x-6 text-sm text-gray-500">
                  <span>§510 Compliance</span>
                  <span>§554 Compliance</span>
                  <span>AB 1522 Compliance</span>
                </div>
              </div>
            </div>
          </footer>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
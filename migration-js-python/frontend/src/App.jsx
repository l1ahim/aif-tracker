import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { SignIn, SignUp, useAuth } from '@clerk/clerk-react'

import Dashboard from './pages/Dashboard'
import Transactions from './pages/Transactions'
import Budget from './pages/Budget'
import Settings from './pages/Settings'
import Layout from './components/Layout'
import './App.css'

// Check if we're in development mode without Clerk
const isDevelopmentMode = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY === undefined || 
                         import.meta.env.VITE_CLERK_PUBLISHABLE_KEY === 'pk_test_development_fallback'

// Development auth hook
const useDevelopmentAuth = () => ({
  isSignedIn: true,
  isLoaded: true,
  user: {
    id: 'dev-user-123',
    firstName: 'Development',
    lastName: 'User'
  }
})

function App() {
  const auth = isDevelopmentMode ? useDevelopmentAuth() : useAuth()
  const { isSignedIn, isLoaded } = auth

  if (!isLoaded) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Loading...</p>
        </div>
      </div>
    )
  }

  // Show development notice
  if (isDevelopmentMode && isSignedIn) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-yellow-700">
                <strong>Development Mode:</strong> Clerk authentication is not configured. 
                Add your VITE_CLERK_PUBLISHABLE_KEY to .env file for full auth functionality.
              </p>
            </div>
          </div>
        </div>
        <Layout>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/transactions" element={<Transactions />} />
            <Route path="/budget" element={<Budget />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Layout>
      </div>
    )
  }

  if (!isSignedIn && !isDevelopmentMode) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Routes>
          <Route path="/sign-up" element={<SignUp />} />
          <Route path="*" element={<SignIn />} />
        </Routes>
      </div>
    )
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/transactions" element={<Transactions />} />
        <Route path="/budget" element={<Budget />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  )
}

export default App

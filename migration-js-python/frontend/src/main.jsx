import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ClerkProvider } from '@clerk/clerk-react'
import { QueryClient, QueryClientProvider } from 'react-query'
import { Toaster } from 'react-hot-toast'

import App from './App.jsx'
import './index.css'

// Initialize Clerk with fallback for development
const clerkPubKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY || 'pk_test_development_fallback'

// For development without Clerk, create a mock provider
const isDevelopmentMode = clerkPubKey === 'pk_test_development_fallback'

// Initialize React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

// Development wrapper when Clerk is not configured
const DevelopmentAuthWrapper = ({ children }) => {
  return (
    <div className="development-auth">
      {children}
    </div>
  )
}

const AuthProvider = isDevelopmentMode ? DevelopmentAuthWrapper : ClerkProvider

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AuthProvider publishableKey={clerkPubKey}>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <App />
          <Toaster position="top-right" />
        </BrowserRouter>
      </QueryClientProvider>
    </AuthProvider>
  </React.StrictMode>,
)

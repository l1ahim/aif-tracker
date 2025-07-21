import { useState } from 'react'
import { useAuth } from '@clerk/clerk-react'
import toast from 'react-hot-toast'

const isDevelopmentMode = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY === undefined || 
                         import.meta.env.VITE_CLERK_PUBLISHABLE_KEY === 'pk_test_development_fallback'

// Check if we're in development or production
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const useApi = () => {
  const auth = isDevelopmentMode ? { getToken: () => Promise.resolve('dev-token-123') } : useAuth()
  const { getToken } = auth
  const [loading, setLoading] = useState(false)

  const apiCall = async (url, options = {}) => {
    setLoading(true)
    try {
      console.log(`API Call: ${API_BASE_URL}${url}`, options)
      
      const token = await getToken()
      
      const response = await fetch(`${API_BASE_URL}${url}`, {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Authorization': `Bearer ${token}`,
          ...options.headers,
        },
        ...options,
      })

      console.log('API Response status:', response.status)
      console.log('API Response headers:', response.headers)

      if (!response.ok) {
        const errorData = await response.text()
        console.error('API Error response:', errorData)
        throw new Error(`HTTP ${response.status}: ${errorData}`)
      }

      const data = await response.json()
      console.log('API Response data:', data)
      return data
    } catch (error) {
      console.error('API Call failed:', error)
      
      // Check if it's a network error
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error(`Cannot connect to backend server at ${API_BASE_URL}. Please ensure the server is running.`)
      }
      
      throw error
    } finally {
      setLoading(false)
    }
  }

  const uploadFile = async (endpoint, file, additionalData = {}) => {
    setLoading(true)
    try {
      const token = await getToken()
      const formData = new FormData()
      formData.append('file', file)
      
      // Add additional form data
      Object.keys(additionalData).forEach(key => {
        formData.append(key, additionalData[key])
      })

      console.log('Uploading to:', `${API_BASE_URL}${endpoint}`)
      console.log('File type:', file.type)
      console.log('File size:', file.size)

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error('Upload failed:', response.status, errorText)
        
        let errorData
        try {
          errorData = JSON.parse(errorText)
          
          // Handle duplicate receipt error specifically
          if (response.status === 400 && 
              typeof errorData.detail === 'object' && 
              errorData.detail.message === "This receipt has already been processed") {
            const details = errorData.detail
            throw new Error(`Duplicate receipt: ${details.formatted_date}|${details.amount}|${details.merchant}`)
          }
        } catch (parseError) {
          if (parseError.message && parseError.message.startsWith("Duplicate receipt:")) {
            throw parseError
          }
          errorData = { detail: `HTTP ${response.status}: ${errorText}` }
        }
        
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      const data = await response.json()
      return data
    } catch (error) {
      console.error('Network/Upload error:', error)
      
      // Check if it's a network error
      if (error instanceof TypeError && error.message.includes('fetch')) {
        console.error('Backend appears to be down or unreachable')
        toast.error('Unable to connect to server. Please check if the backend is running.')
        
        // Return mock data in development
        if (isDevelopmentMode && endpoint.includes('scan-receipt')) {
          toast.success('Using mock data (backend not available)')
          return {
            id: 'mock-' + Date.now(),
            amount: 25.99,
            description: 'Mock Receipt Scan - Backend Offline',
            merchant: 'Mock Store',
            category: 'Food & Dining',
            date: new Date().toISOString(),
            ai_confidence: 0.85,
            processing_status: 'completed'
          }
        }
      }
      
      // In development mode, return mock data for scan-receipt
      if (isDevelopmentMode && endpoint.includes('scan-receipt')) {
        return {
          id: 'mock-' + Date.now(),
          amount: 25.99,
          description: 'Mock Receipt Scan',
          merchant: 'Mock Store',
          category: 'Food & Dining',
          date: new Date().toISOString(),
          ai_confidence: 0.85,
          processing_status: 'completed'
        }
      }
      
      toast.error(error.message)
      throw error
    } finally {
      setLoading(false)
    }
  }

  return { apiCall, uploadFile, loading }
}

// Mock data for development
function getMockData(endpoint) {
  const mockData = {
    '/transactions/stats/monthly': {
      total_spent: 1250.75,
      total_income: 3000.00,
      transaction_count: 15,
      by_category: {
        'Food & Dining': { total: 450.25, count: 8 },
        'Transportation': { total: 200.50, count: 3 },
        'Shopping': { total: 350.00, count: 2 },
        'Entertainment': { total: 150.00, count: 2 }
      }
    },
    '/transactions': [
      {
        id: '1',
        amount: 125.50,
        description: 'Coffee Shop',
        category: 'Food & Dining',
        date: new Date().toISOString(),
        merchant: 'Starbucks'
      },
      {
        id: '2',
        amount: 385.20,
        description: 'Grocery Shopping',
        category: 'Food & Dining',
        date: new Date(Date.now() - 86400000).toISOString(),
        merchant: 'Carrefour'
      }
    ]
  }

  // Check if endpoint matches any mock data
  for (const [key, value] of Object.entries(mockData)) {
    if (endpoint.includes(key)) {
      return value
    }
  }

  return []
}

// Specific API hooks
export const useTransactions = () => {
  const { apiCall, uploadFile, loading } = useApi()

  const getMonthlyStats = (year, month, timestamp) => {
    return apiCall(`/transactions/stats/monthly?year=${year}&month=${month}&_t=${timestamp || Date.now()}`)
  }

  const getTransactions = (params = {}) => {
    const queryParams = { ...params, _t: Date.now() }
    const queryString = new URLSearchParams(queryParams).toString()
    return apiCall(`/transactions?${queryString}`)
  }

  const scanReceipt = (file) => {
    return uploadFile('/transactions/scan-receipt', file)
  }

  const createTransaction = async (transactionData) => {
    console.log('Creating transaction:', transactionData)
    
    // Validate required fields before sending
    const requiredFields = ['description', 'merchant', 'amount', 'category', 'transaction_type', 'date']
    const missing = requiredFields.filter(field => !transactionData[field])
    
    if (missing.length > 0) {
      throw new Error(`Missing required fields: ${missing.join(', ')}`)
    }
    
    return apiCall('/api/transactions', {
      method: 'POST',
      body: JSON.stringify(transactionData)
    })
  }

  const deleteTransaction = (transactionId) => {
    return apiCall(`/transactions/${transactionId}`, {
      method: 'DELETE'
    })
  }

  const updateTransaction = (transactionId, updateData) => {
    return apiCall(`/transactions/${transactionId}`, {
      method: 'PUT',
      body: JSON.stringify(updateData),
    })
  }

  return {
    getTransactions,
    scanReceipt,
    createTransaction,
    updateTransaction,
    deleteTransaction,
    getMonthlyStats,
    loading,
  }
}
     
  const deleteTransaction = (transactionId) => {
    return apiCall(`/transactions/${transactionId}`, {
      method: 'DELETE'
    })
  }

  const updateTransaction = (transactionId, updateData) => {
    return apiCall(`/transactions/${transactionId}`, {
      method: 'PUT',
      body: JSON.stringify(updateData),
    })
  }

  return {
    getTransactions,
    scanReceipt,
    createTransaction,
    updateTransaction,
    deleteTransaction,
    getMonthlyStats,
    loading,
  }
    

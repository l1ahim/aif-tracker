import React, { useState, useEffect } from 'react'
import { useTransactions } from '../hooks/useApi'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { Plus, Calendar, DollarSign } from 'lucide-react'
import { ManualTransactionForm } from '../components/ManualTransactionForm'
import toast from 'react-hot-toast'

export default function Transactions() {
  const { getTransactions, deleteTransaction, updateTransaction, createTransaction, loading } = useTransactions()
  const [transactions, setTransactions] = useState([])
  const [expandedDescriptions, setExpandedDescriptions] = useState(new Set())
  const [selectedPeriod, setSelectedPeriod] = useState(30)
  const [showManualForm, setShowManualForm] = useState(false)

  const handleUpdateTransaction = async (transactionId, field, value) => {
    if (!value.trim()) return
    
    try {
      await updateTransaction(transactionId, { [field]: value })
      
      setTransactions(prev => prev.map(t => 
        t.id === transactionId ? { ...t, [field]: value } : t
      ))
    } catch (error) {
      console.error('Failed to update transaction:', error)
    }
  }

  const handleDelete = async (transactionId) => {
    if (window.confirm('Are you sure you want to delete this transaction?')) {
      try {
        await deleteTransaction(transactionId)
        setTransactions(prev => prev.filter(t => t.id !== transactionId))
        toast.success('Transaction deleted successfully')
      } catch (error) {
        console.error('Failed to delete transaction:', error)
        toast.error('Failed to delete transaction')
      }
    }
  }

  const handleManualTransactionSubmit = async (transactionData) => {
    try {
      console.log('=== TRANSACTION SUBMISSION DEBUG ===')
      console.log('1. Original form data:', transactionData)
      
      const payload = {
        description: transactionData.description,
        merchant: transactionData.merchant,
        amount: Number(transactionData.amount),
        category: transactionData.category,
        transaction_type: transactionData.transaction_type,
        date: transactionData.date,
        processing_status: 'completed',
        manually_verified: true
      }
      
      console.log('3. Final payload to send:', payload)
      console.log('4. Calling createTransaction...')
      
      const newTransaction = await createTransaction(payload)
      
      if (!newTransaction) {
        throw new Error('No transaction returned from server')
      }
      
      setTransactions(prev => [newTransaction, ...prev])
      setShowManualForm(false)
      toast.success('Transaction added successfully!')
    } catch (error) {
      console.error('=== TRANSACTION SUBMISSION ERROR ===')
      console.error('Full error object:', error)
      
      let errorMessage = 'Unknown error'
      
      if (error.response?.data) {
        const data = error.response.data
        if (typeof data === 'string') {
          errorMessage = data
        } else if (data?.detail) {
          if (Array.isArray(data.detail)) {
            errorMessage = data.detail.map(d => d.msg || d.message || JSON.stringify(d)).join(', ')
          } else {
            errorMessage = data.detail
          }
        } else if (data?.message) {
          errorMessage = data.message
        } else if (data?.error) {
          errorMessage = data.error
        } else {
          errorMessage = JSON.stringify(data)
        }
      } else if (error.message) {
        errorMessage = error.message
      }
      
      if (error.response?.status === 400) {
        toast.error(`Invalid data: ${errorMessage}`)
      } else if (error.response?.status === 422) {
        toast.error(`Validation error: ${errorMessage}`)
      } else if (error.response?.status === 500) {
        toast.error(`Server error: ${errorMessage}`)
      } else if (!error.response) {
        toast.error('Cannot connect to backend server. Please check if the server is running.')
      } else {
        toast.error(`Failed to add transaction: ${errorMessage}`)
      }
      
      throw error
    }
  }

  const toggleDescription = (transactionId) => {
    setExpandedDescriptions(prev => {
      const newSet = new Set(prev)
      if (newSet.has(transactionId)) {
        newSet.delete(transactionId)
      } else {
        newSet.add(transactionId)
      }
      return newSet
    })
  }

  useEffect(() => {
    const loadTransactions = async () => {
      try {
        console.log('Testing backend connection...')
        const data = await getTransactions()
        if (Array.isArray(data)) {
          const sorted = data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
          setTransactions(sorted)
          console.log('Backend connection successful')
        } else {
          console.error('Invalid transaction data received:', data)
          setTransactions([])
          toast.error('Failed to load transactions: Invalid data format')
        }
      } catch (error) {
        console.error('Backend connection failed:', error)
        setTransactions([])
        if (error.message.includes('Cannot connect')) {
          toast.error('Backend server is not running. Please start the server.')
        } else {
          toast.error('Failed to load transactions')
        }
      }
    }
    
    loadTransactions()
  }, [])

  // Calculate merchant spending data for selected period
  const getMerchantData = () => {
    const cutoffDate = new Date()
    cutoffDate.setDate(cutoffDate.getDate() - selectedPeriod)
    
    const merchantTotals = {}
    const filteredTransactions = transactions.filter(t => {
      // Add safety checks
      if (!t || !t.date || t.transaction_type !== 'expense') return false
      
      try {
        return new Date(t.date) >= cutoffDate
      } catch (error) {
        console.warn('Invalid date format:', t.date)
        return false
      }
    })
    
    filteredTransactions.forEach(transaction => {
      const merchant = transaction.merchant || 'Unknown'
      const amount = parseFloat(transaction.amount) || 0
      merchantTotals[merchant] = (merchantTotals[merchant] || 0) + amount
    })
    
    return Object.entries(merchantTotals)
      .map(([merchant, total]) => ({ name: merchant, value: total }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 6) // Top 6 merchants for better fit
  }

  const merchantData = getMerchantData()
  const COLORS = ['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16']

  if (loading && transactions.length === 0) {
    return <div className="p-6">Loading transactions...</div>
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header with Add Transaction Button */}
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Transactions</h1>
        <button
          onClick={() => setShowManualForm(true)}
          className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Add Transaction</span>
        </button>
      </div>

      {/* Manual Transaction Form Modal */}
      <ManualTransactionForm
        isOpen={showManualForm}
        onClose={() => setShowManualForm(false)}
        onSubmit={handleManualTransactionSubmit}
        loading={loading}
      />
      
      {/* Merchant Spending Chart */}
      {merchantData.length > 0 && (
        <div className="bg-white shadow rounded-lg p-4 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Spending by Merchant</h2>
            <select 
              value={selectedPeriod} 
              onChange={(e) => setSelectedPeriod(Number(e.target.value))}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm"
            >
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 3 months</option>
              <option value={365}>Last year</option>
            </select>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={merchantData}
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {merchantData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [`${value.toFixed(2)} lei`, 'Amount']} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="space-y-2">
              {merchantData.map((item, index) => {
                const total = merchantData.reduce((sum, m) => sum + m.value, 0)
                const percentage = ((item.value / total) * 100).toFixed(1)
                return (
                  <div key={item.name} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <div className="flex items-center space-x-2">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: COLORS[index % COLORS.length] }}
                      ></div>
                      <span className="text-sm font-medium text-gray-700">{item.name}</span>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-bold text-gray-900">{item.value.toFixed(2)} lei</div>
                      <div className="text-xs text-gray-500">{percentage}%</div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}
      
      {/* Transactions Table */}
      <div className="bg-white shadow rounded-lg overflow-hidden overflow-x-auto">
        <div className="px-6 py-4 bg-gray-50 border-b">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-900">All Transactions</h2>
            <div className="text-sm text-gray-600">
              All Time Total: <span className="font-bold">{transactions.filter(t => t.transaction_type === 'expense').reduce((sum, t) => sum + t.amount, 0).toFixed(2)} lei</span>
            </div>
          </div>
        </div>
        
        <table className="w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Description
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Merchant
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Amount
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Category
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {transactions.length === 0 ? (
              <tr>
                <td colSpan="6" className="px-6 py-8 text-center text-gray-500">
                  <div className="flex flex-col items-center space-y-3">
                    <DollarSign className="w-12 h-12 text-gray-300" />
                    <p>No transactions found</p>
                    <button
                      onClick={() => setShowManualForm(true)}
                      className="text-blue-600 hover:text-blue-800 font-medium"
                    >
                      Add your first transaction
                    </button>
                  </div>
                </td>
              </tr>
            ) : (
              transactions.map((transaction) => (
                <tr key={transaction.id}>
                  <td className="px-3 py-4 text-sm text-gray-900 max-w-xs">
                    <div className={expandedDescriptions.has(transaction.id) ? '' : 'truncate'}>
                      {transaction.description || 'No description'}
                    </div>
                    {transaction.description && transaction.description.length > 50 && (
                      <button
                        onClick={() => toggleDescription(transaction.id)}
                        className="text-blue-600 hover:text-blue-800 text-xs mt-1 block"
                      >
                        {expandedDescriptions.has(transaction.id) ? 'Show less' : 'Show more'}
                      </button>
                    )}
                  </td>
                  <td className="px-3 py-4 text-sm text-gray-600 font-medium max-w-xs">
                    {transaction.merchant || (
                      <input 
                        type="text" 
                        placeholder="Add merchant" 
                        className="text-xs border border-gray-300 rounded px-2 py-1 w-full"
                        onBlur={(e) => handleUpdateTransaction(transaction.id, 'merchant', e.target.value)}
                      />
                    )}
                  </td>
                  <td className="px-3 py-4 whitespace-nowrap text-sm font-bold">
                    <span className={transaction.transaction_type === 'income' ? 'text-green-600' : 'text-red-600'}>
                      {transaction.transaction_type === 'income' ? '+' : '-'}{transaction.amount.toFixed(2)} lei
                    </span>
                  </td>
                  <td className="px-3 py-4 text-sm text-gray-500 max-w-xs">
                    {transaction.category || (
                      <input 
                        type="text" 
                        placeholder="Add category" 
                        className="text-xs border border-gray-300 rounded px-2 py-1 w-full"
                        onBlur={(e) => handleUpdateTransaction(transaction.id, 'category', e.target.value)}
                      />
                    )}
                  </td>
                  <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div>Transaction: {new Date(transaction.date).toLocaleDateString()}</div>
                    <div className="text-xs text-gray-400">
                      Added: {new Date(transaction.created_at).toLocaleDateString()}
                    </div>
                  </td>
                  <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-500">
                    <button
                      onClick={() => handleDelete(transaction.id)}
                      className="text-red-600 hover:text-red-900 font-medium text-xs"
                      disabled={loading}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
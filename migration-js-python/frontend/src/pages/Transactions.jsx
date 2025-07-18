import React, { useState, useEffect } from 'react'
import { useTransactions } from '../hooks/useApi'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'

export default function Transactions() {
  const { getTransactions, deleteTransaction, updateTransaction, loading } = useTransactions()
  const [transactions, setTransactions] = useState([])
  const [expandedDescriptions, setExpandedDescriptions] = useState(new Set())
  const [selectedPeriod, setSelectedPeriod] = useState(30) // days

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
      } catch (error) {
        console.error('Failed to delete transaction:', error)
      }
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
    getTransactions()
      .then(data => {
        const sorted = data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        setTransactions(sorted)
      })
      .catch(console.error)
  }, [])

  // Calculate merchant spending data for selected period
  const getMerchantData = () => {
    const cutoffDate = new Date()
    cutoffDate.setDate(cutoffDate.getDate() - selectedPeriod)
    
    const merchantTotals = {}
    const filteredTransactions = transactions.filter(t => 
      t.transaction_type === 'expense' && 
      new Date(t.date) >= cutoffDate
    )
    
    filteredTransactions.forEach(transaction => {
      const merchant = transaction.merchant || 'Unknown'
      merchantTotals[merchant] = (merchantTotals[merchant] || 0) + transaction.amount
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
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Transactions</h1>
      
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
                <td colSpan="6" className="px-6 py-4 text-center text-gray-500">
                  No transactions found
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
                  <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-900 font-bold">
                    {transaction.amount.toFixed(2)} lei
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
                    <div>Receipt: {new Date(transaction.date).toLocaleDateString()}</div>
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

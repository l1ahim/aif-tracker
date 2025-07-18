import React, { useState, useEffect } from 'react'
import { useTransactions } from '../hooks/useApi'
import { ReceiptScanner } from '../components/ReceiptScanner'
import { TrendingUp, DollarSign, CreditCard, Target } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Dashboard() {
  const { getMonthlyStats, getTransactions, loading } = useTransactions()
  const [dashboardData, setDashboardData] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const now = new Date()
        const timestamp = new Date().getTime()
        const monthlyStats = await getMonthlyStats(now.getFullYear(), now.getMonth() + 1, timestamp)
        const recentTransactions = await getTransactions({ limit: 5, _t: timestamp })
        
        // Generate AI insights based on data
        const aiTip = await generateAIInsight(monthlyStats, recentTransactions)
        
        setDashboardData({
          monthly_stats: monthlyStats,
          recent_transactions: recentTransactions || [],
          ai_tip: aiTip,
          budget_alerts: [],
          top_merchants: []
        })
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
        setDashboardData({
          monthly_stats: {
            total_spent: 0,
            transaction_count: 0,
            by_category: {},
            average_transaction: 0
          },
          recent_transactions: [],
          ai_tip: "💡 Start scanning receipts to get personalized spending insights!",
          budget_alerts: [],
          top_merchants: []
        })
      }
    }
    
    fetchDashboardData()
  }, [getMonthlyStats, getTransactions, refreshKey])

  const generateAIInsight = async (monthlyStats, recentTransactions) => {
    if (!monthlyStats || monthlyStats.transaction_count === 0) {
      return "💡 Start scanning receipts to get personalized spending insights!"
    }
    
    try {
      const { apiCall } = useTransactions()
      const insight = await apiCall('/ai/generate-insight', {
        method: 'POST',
        body: JSON.stringify({
          monthly_stats: monthlyStats,
          recent_transactions: recentTransactions?.slice(0, 5) || []
        })
      })
      return insight.message || "💡 Keep tracking your expenses for better insights!"
    } catch (error) {
      console.error('Failed to generate AI insight:', error)
      return "💡 Keep tracking your expenses for better insights!"
    }
  }

  const handleTransactionCreated = (newTransaction) => {
    // Force immediate data refresh
    const refreshData = async () => {
      try {
        const now = new Date()
        const timestamp = Date.now()
        const monthlyStats = await getMonthlyStats(now.getFullYear(), now.getMonth() + 1, timestamp)
        const recentTransactions = await getTransactions({ limit: 5, _t: timestamp })
        
        setDashboardData(prev => ({
          ...prev,
          monthly_stats: monthlyStats,
          recent_transactions: recentTransactions || []
        }))
      } catch (error) {
        console.error('Failed to refresh dashboard:', error)
      }
    }
    
    // Refresh immediately and after a short delay
    refreshData()
    setTimeout(refreshData, 1000)
    
    toast.success('Transaction added successfully!')
  }

  // Only show full-screen loader on initial load
  if (loading && !dashboardData) {
    return (
      <div className="p-6 flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Loading your financial insights...</p>
        </div>
      </div>
    )
  }

  const stats = dashboardData?.monthly_stats || {}

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="p-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Financial Dashboard</h1>
          <p className="text-gray-600 mt-2">Your spending insights and financial overview</p>
        </div>

        {/* AI Tip Banner */}
        {dashboardData?.ai_tip && (
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-start space-x-3">
              <TrendingUp className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="font-medium text-blue-900">AI Insight</h3>
                <p className="text-blue-700 mt-1">{dashboardData.ai_tip}</p>
              </div>
            </div>
          </div>
        )}

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Spent</p>
                <p className="text-2xl font-bold text-red-600">
                  {typeof stats.total_spent === 'number' ? stats.total_spent.toFixed(2) : '0.00'} lei
                </p>
                <p className="text-xs text-gray-500 mt-1">This month</p>
              </div>
              <div className="p-3 bg-red-50 rounded-lg">
                <DollarSign className="w-6 h-6 text-red-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Transactions</p>
                <p className="text-2xl font-bold text-blue-600">
                  {stats.transaction_count || 0}
                </p>
                <p className="text-xs text-gray-500 mt-1">This month</p>
              </div>
              <div className="p-3 bg-blue-50 rounded-lg">
                <CreditCard className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Categories</p>
                <p className="text-2xl font-bold text-green-600">
                  {Object.keys(stats.by_category || {}).length}
                </p>
                <p className="text-xs text-gray-500 mt-1">Active categories</p>
              </div>
              <div className="p-3 bg-green-50 rounded-lg">
                <Target className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg. Transaction</p>
                <p className="text-2xl font-bold text-purple-600">
                  {stats.average_transaction?.toFixed(2) || '0.00'} lei
                </p>
                <p className="text-xs text-gray-500 mt-1">Per transaction</p>
              </div>
              <div className="p-3 bg-purple-50 rounded-lg">
                <TrendingUp className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </div>
        </div>

        {/* Budget Alerts - only show if there are alerts */}
        {dashboardData?.budget_alerts?.length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Budget Alerts</h2>
            <div className="space-y-3">
              {dashboardData.budget_alerts.map((alert, index) => (
                <div key={index} className={`p-4 rounded-lg border ${
                  alert.type === 'over_budget' 
                    ? 'bg-red-50 border-red-200' 
                    : 'bg-yellow-50 border-yellow-200'
                }`}>
                  <div className="flex justify-between items-center">
                    <div>
                      <p className={`font-medium ${
                        alert.type === 'over_budget' ? 'text-red-800' : 'text-yellow-800'
                      }`}>
                        {alert.category} - {alert.percentage.toFixed(0)}% of budget used
                      </p>
                      <p className={`text-sm ${
                        alert.type === 'over_budget' ? 'text-red-600' : 'text-yellow-600'
                      }`}>
                        ${alert.current.toFixed(2)} of ${alert.limit.toFixed(2)}
                      </p>
                    </div>
                    <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                      alert.type === 'over_budget' 
                        ? 'bg-red-100 text-red-800' 
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {alert.type === 'over_budget' ? 'Over Budget' : 'Warning'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Receipt Scanner */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Add Expense</h2>
              <ReceiptScanner onTransactionCreated={handleTransactionCreated} />
            </div>
          </div>

          {/* Spending Overview */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Spending Breakdown</h2>
              {stats.by_category && Object.keys(stats.by_category).length > 0 ? (
                <div className="space-y-4">
                  {Object.entries(stats.by_category).slice(0, 6).map(([category, data]) => {
                    const percentage = (data.total / stats.total_spent) * 100
                    return (
                      <div key={category} className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex justify-between items-center mb-1">
                            <span className="text-sm font-medium text-gray-700">{category}</span>
                            <span className="text-sm text-gray-600">{data.total.toFixed(2)} lei</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                              style={{ width: `${percentage}%` }}
                            ></div>
                          </div>
                          <div className="flex justify-between items-center mt-1">
                            <span className="text-xs text-gray-500">{data.count} transactions</span>
                            <span className="text-xs text-gray-500">{percentage.toFixed(1)}%</span>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-gray-400 mb-2">
                    <CreditCard className="w-12 h-12 mx-auto" />
                  </div>
                  <p className="text-gray-500">No spending data available</p>
                  <p className="text-sm text-gray-400">Start by adding your first expense!</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Top Merchants - only show if there are merchants */}
        {dashboardData?.top_merchants?.length > 0 && (
          <div className="mt-8 bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Merchants</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {dashboardData.top_merchants.map((merchant, index) => (
                <div key={index} className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium text-gray-900">{merchant.merchant}</p>
                      <p className="text-sm text-gray-600">{merchant.transaction_count} visits</p>
                    </div>
                    <p className="text-lg font-bold text-gray-900">{merchant.total_spent.toFixed(2)} lei</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recent Transactions */}
        {dashboardData?.recent_transactions?.length > 0 && (
          <div className="mt-8 bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Transactions</h2>
            <div className="space-y-3">
              {dashboardData.recent_transactions.slice(0, 5).map((transaction, index) => (
                <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">{transaction.merchant || 'Unknown Merchant'}</p>
                    <p className="text-sm text-gray-600">{transaction.description}</p>
                    <p className="text-xs text-gray-500">{transaction.category}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-gray-900">{transaction.amount.toFixed(2)} lei</p>
                    <p className="text-xs text-gray-500">
                      {new Date(transaction.date).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

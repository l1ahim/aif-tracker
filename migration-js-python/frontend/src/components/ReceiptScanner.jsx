import React, { useCallback, useState, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import { Camera, Upload, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

import { useTransactions } from '../hooks/useApi'
import { useApi } from '../hooks/useApi'

export const ReceiptScanner = ({ onTransactionCreated }) => {
  const { scanReceipt, loading } = useTransactions()
  const { apiCall } = useApi()
  const [previewImage, setPreviewImage] = useState(null)
  const [aiStatus, setAiStatus] = useState(null)
  const [backendStatus, setBackendStatus] = useState('checking')

  useEffect(() => {
    // Check backend status
    const checkBackend = async () => {
      try {
        const response = await fetch('http://localhost:8000/health')
        if (response.ok) {
          setBackendStatus('online')
          // Get AI provider status
          apiCall('/transactions/ai-status')
            .then(setAiStatus)
            .catch(console.error)
        } else {
          setBackendStatus('offline')
        }
      } catch (error) {
        console.error('Backend check failed:', error)
        setBackendStatus('offline')
      }
    }
    
    checkBackend()
  }, [])

  const onDrop = useCallback(async (acceptedFiles) => {
    if (!acceptedFiles.length) return

    const results = []
    let successCount = 0
    let duplicateCount = 0
    let errorCount = 0

    for (const file of acceptedFiles) {
      try {
        const result = await scanReceipt(file)
        results.push(result)
        successCount++
        
        // Call parent callback for each successful transaction
        if (onTransactionCreated) {
          onTransactionCreated(result)
        }
        
      } catch (error) {
        if (error.message && error.message.startsWith("Duplicate receipt:")) {
          duplicateCount++
        } else {
          errorCount++
        }
      }
    }

    // Show summary toast
    if (successCount > 0) {
      toast.success(`${successCount} receipt${successCount > 1 ? 's' : ''} processed successfully!`)
    }
    if (duplicateCount > 0) {
      toast.error(`${duplicateCount} duplicate receipt${duplicateCount > 1 ? 's' : ''} skipped`)
    }
    if (errorCount > 0) {
      toast.error(`${errorCount} receipt${errorCount > 1 ? 's' : ''} failed to process`)
    }
  }, [scanReceipt, onTransactionCreated])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.webp', '.heif', '.heic']
    },
    multiple: true,
    disabled: loading
  })

  return (
    <div className="w-full max-w-md mx-auto">
      {/* Backend Status */}
      {backendStatus === 'offline' && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
            <span className="text-sm text-yellow-800">
              Backend offline - using demo mode
            </span>
          </div>
        </div>
      )}

      {backendStatus === 'online' && (
        <div className="mb-4 p-2 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-xs text-green-700">Backend connected</span>
          </div>
        </div>
      )}

      {/* AI Provider Status */}
      {aiStatus && (
        <div className="mb-4 text-xs text-gray-500 text-center">
          <span>AI Provider: </span>
          <span className="font-medium capitalize">
            {aiStatus.active_provider === 'none' ? 'Not configured' : aiStatus.active_provider}
          </span>
          {aiStatus.active_provider === 'azure' && aiStatus.provider_details.azure.form_recognizer && (
            <span className="ml-1 text-green-600">+ Form Recognizer</span>
          )}
        </div>
      )}
      
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${isDragActive 
            ? 'border-blue-400 bg-blue-50' 
            : 'border-gray-300 hover:border-gray-400'
          }
          ${loading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />
        
        {previewImage ? (
          <div className="space-y-4">
            <img 
              src={previewImage} 
              alt="Receipt preview" 
              className="max-w-full h-32 object-contain mx-auto rounded"
            />
            {loading && (
              <div className="flex items-center justify-center space-x-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm text-gray-600">Processing receipt...</span>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex justify-center">
              {loading ? (
                <Loader2 className="w-12 h-12 text-gray-400 animate-spin" />
              ) : (
                <Camera className="w-12 h-12 text-gray-400" />
              )}
            </div>
            
            <div>
              <p className="text-lg font-medium text-gray-900">
                {isDragActive ? 'Drop your receipts here' : 'Scan Receipts'}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                Drag & drop photos or click to browse (multiple files supported)
              </p>
            </div>
            
            <div className="flex items-center justify-center space-x-2 text-xs text-gray-400">
              <Upload className="w-3 h-3" />
              <span>PNG, JPG, JPEG, WebP, HEIF, HEIC up to 10MB</span>
            </div>
          </div>
        )}
      </div>
      
      {loading && !previewImage && (
        <div className="mt-4 text-center">
          <div className="inline-flex items-center space-x-2 text-sm text-blue-600">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Processing receipt...</span>
          </div>
        </div>
      )}
    </div>
  )
}

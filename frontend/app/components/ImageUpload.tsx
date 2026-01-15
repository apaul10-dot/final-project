'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'
import { TestData } from '../types'

interface ImageUploadProps {
  onUploadComplete: (data: TestData) => void
}

export default function ImageUpload({ onUploadComplete }: ImageUploadProps) {
  const [uploading, setUploading] = useState(false)
  const [uploadedImages, setUploadedImages] = useState<File[]>([])

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setUploadedImages(prev => [...prev, ...acceptedFiles])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp']
    },
    multiple: true
  })

  const handleUpload = async () => {
    if (uploadedImages.length === 0) {
      alert('Please select at least one image to upload.')
      return
    }

    setUploading(true)
    try {
      // Check backend connection - try API endpoint directly (skip health check)
      // The upload endpoint will fail if backend is down anyway

      const formData = new FormData()
      uploadedImages.forEach((file) => {
        formData.append('images', file)
      })

      const response = await axios.post<TestData>(
        'http://localhost:8000/api/upload-test',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 120000, // 120 second timeout (2 minutes) for OCR processing
        }
      )

      if (!response.data || !response.data.test_id) {
        throw new Error('Invalid response from server')
      }

      onUploadComplete(response.data)
    } catch (error) {
      console.error('Upload error:', error)
      if (axios.isAxiosError(error)) {
        if (error.code === 'ECONNREFUSED') {
          alert('Cannot connect to server. Please make sure the backend is running.')
        } else if (error.response) {
          alert(`Server error: ${error.response.status} - ${error.response.data?.detail || 'Unknown error'}`)
        } else {
          alert(`Upload error: ${error.message}`)
        }
      } else {
        alert(`Error uploading images: ${error instanceof Error ? error.message : 'Unknown error'}`)
      }
    } finally {
      setUploading(false)
    }
  }

  const removeImage = (index: number) => {
    setUploadedImages(prev => prev.filter((_, i) => i !== index))
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-semibold mb-4">Upload Test Images</h2>
      
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-blue-400'
        }`}
      >
        <input {...getInputProps()} />
        <div className="space-y-2">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            stroke="currentColor"
            fill="none"
            viewBox="0 0 48 48"
          >
            <path
              d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <p className="text-gray-600">
            {isDragActive
              ? 'Drop the images here...'
              : 'Drag & drop test images here, or click to select'}
          </p>
          <p className="text-sm text-gray-500">Supports PNG, JPG, JPEG, GIF, WEBP</p>
        </div>
      </div>

      {uploadedImages.length > 0 && (
        <div className="mt-6">
          <h3 className="font-medium mb-2">Selected Images ({uploadedImages.length})</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
            {uploadedImages.map((file, index) => (
              <div key={index} className="relative group">
                <img
                  src={URL.createObjectURL(file)}
                  alt={`Preview ${index + 1}`}
                  className="w-full h-32 object-cover rounded-lg"
                />
                <button
                  onClick={() => removeImage(index)}
                  className="absolute top-2 right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  ×
                </button>
                <p className="text-xs text-gray-600 mt-1 truncate">{file.name}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={uploading || uploadedImages.length === 0}
        className="w-full mt-4 bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        {uploading ? 'Uploading...' : 'Upload & Analyze'}
      </button>
    </div>
  )
}




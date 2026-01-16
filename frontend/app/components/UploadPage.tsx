'use client'

import { useState, useEffect, useRef } from 'react'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'
import ArrowButton from './ArrowButton'

interface UploadPageProps {
  userName: string
  subject: string
  onUploadComplete: (data: any) => void
}

export default function UploadPage({ userName, subject, onUploadComplete }: UploadPageProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [notes, setNotes] = useState('')
  const [showNext, setShowNext] = useState(false)
  const [fadeIn, setFadeIn] = useState(false)
  const [uploading, setUploading] = useState(false)

  useEffect(() => {
    setFadeIn(true)
  }, [])

  useEffect(() => {
    setShowNext(selectedFile !== null)
  }, [selectedFile])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setSelectedFile(acceptedFiles[0])
      }
    },
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp']
    },
    multiple: false
  })

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && selectedFile) {
      handleNext()
    }
  }

  const handleNext = async () => {
    if (!selectedFile) return
    
    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('images', selectedFile)
      if (notes.trim()) {
        formData.append('notes', notes.trim())
      }
      // Add subject to form data
      if (subject) {
        formData.append('subject', subject)
      }

      const response = await axios.post(
        'http://localhost:8000/api/upload-test',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 120000,
        }
      )

      if (response.data && response.data.test_id) {
        onUploadComplete(response.data)
      }
    } catch (error) {
      console.error('Upload error:', error)
      alert('Error uploading file. Please try again.')
      setUploading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4" onKeyPress={handleKeyPress} tabIndex={0}>
      <div className={`text-center max-w-3xl w-full transition-opacity duration-700 ${fadeIn ? 'opacity-100' : 'opacity-0'}`}>
        <h1 className="text-4xl md:text-5xl font-light text-black mb-8 tracking-tight">
          I'd be pleased to help you with {subject}, {userName}.
        </h1>
        
        <p className="text-xl text-gray-700 font-light mb-8">
          Please upload your desired file, {userName}.
        </p>

        <div
          {...getRootProps()}
          className={`mb-8 p-12 border-2 border-dashed rounded-xl transition-all duration-300 cursor-pointer
            ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white hover:border-blue-400'}
          `}
        >
          <input {...getInputProps()} />
          {selectedFile ? (
            <div className="space-y-4">
              <p className="text-lg text-black">{selectedFile.name}</p>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setSelectedFile(null)
                }}
                className="text-sm text-gray-500 hover:text-red-500"
              >
                Remove
              </button>
            </div>
          ) : (
            <p className="text-gray-600">
              {isDragActive ? 'Drop the file here...' : 'Drag & drop your file here, or click to select'}
            </p>
          )}
        </div>

        <div className="mb-8">
          <p className="text-sm text-gray-600 mb-2">Additional notes (optional)</p>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full max-w-md px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 transition-all duration-300 bg-white text-black placeholder-gray-400 resize-none"
            placeholder="Any additional information..."
            rows={3}
          />
        </div>

        {showNext && !uploading && (
          <div className="flex justify-center opacity-0 animate-fadeIn">
            <ArrowButton onClick={handleNext} />
          </div>
        )}

        {uploading && (
          <div className="text-gray-600">Uploading...</div>
        )}
      </div>
    </div>
  )
}


'use client'

import { useState } from 'react'

interface FeedbackModalProps {
  onSubmit: () => void
  onClose: () => void
  submitted: boolean
}

export default function FeedbackModal({ onSubmit, onClose, submitted }: FeedbackModalProps) {
  const [feedback, setFeedback] = useState('')

  const handleSubmit = () => {
    if (feedback.trim()) {
      onSubmit()
    }
  }

  if (submitted) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
          <p className="text-xl text-black font-light text-center">
            Thank you for your feedback! Your feedback has been reported to the devs to improve ExplainIt
          </p>
          <button
            onClick={onClose}
            className="mt-6 w-full px-6 py-3 bg-blue-500 text-white rounded-lg text-lg font-medium hover:bg-blue-600 transition-all duration-300"
          >
            Close
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
        <h2 className="text-2xl font-light text-black mb-4">
          Why were you dissatisfied today?
        </h2>
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 transition-all duration-300 bg-white text-black placeholder-gray-400 resize-none mb-6"
          placeholder="Enter your feedback..."
          rows={4}
        />
        <div className="flex gap-4">
          <button
            onClick={handleSubmit}
            className="flex-1 px-6 py-3 bg-blue-500 text-white rounded-lg text-lg font-medium hover:bg-blue-600 transition-all duration-300"
          >
            Submit to devs
          </button>
          <button
            onClick={onClose}
            className="flex-1 px-6 py-3 bg-gray-200 text-black rounded-lg text-lg font-medium hover:bg-gray-300 transition-all duration-300"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}


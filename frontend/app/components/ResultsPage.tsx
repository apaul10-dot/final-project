'use client'

import { useState, useEffect } from 'react'
import FeedbackModal from './FeedbackModal'

interface ResultsPageProps {
  answers: Record<number, string>
  results: Record<number, boolean>
  userName: string
}

export default function ResultsPage({ answers, results, userName }: ResultsPageProps) {
  const [fadeIn, setFadeIn] = useState(false)
  const [showFeedback, setShowFeedback] = useState(false)
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false)

  useEffect(() => {
    // Show loading for 7 seconds, then fade in results
    setTimeout(() => {
      setFadeIn(true)
    }, 7000)
  }, [])

  const handleEmojiClick = (emoji: string) => {
    // All emojis show feedback popup
    setShowFeedback(true)
  }

  const handleFeedbackSubmit = () => {
    setFeedbackSubmitted(true)
    setTimeout(() => {
      setShowFeedback(false)
    }, 2000)
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-12">
      {!fadeIn ? (
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-8"></div>
          <p className="text-xl text-gray-700 font-light">Processing your answers...</p>
        </div>
      ) : (
        <div className={`max-w-4xl w-full transition-opacity duration-700 ${fadeIn ? 'opacity-100' : 'opacity-0'}`}>
          <div className="space-y-12 mb-16">
            {Object.entries(answers).map(([key, answer]) => {
              const questionId = parseInt(key)
              const isCorrect = results[questionId]
              return (
                <div key={questionId} className="flex items-start gap-4">
                  <div className="flex-1">
                    <p className="text-lg text-black font-light mb-2">Your answer:</p>
                    <p className="text-xl text-gray-800">{answer}</p>
                  </div>
                  <div className="text-4xl">
                    {isCorrect ? (
                      <span className="text-green-500">✓</span>
                    ) : (
                      <span className="text-red-500">✗</span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>

          <div className="text-center">
            <p className="text-xl text-black font-light mb-6">
              How was your experience with ExplainIt today?
            </p>
            <div className="flex justify-center gap-8">
              <button
                onClick={() => handleEmojiClick('sad')}
                className="text-6xl hover:scale-110 transition-transform duration-300"
              >
                😢
              </button>
              <button
                onClick={() => handleEmojiClick('neutral')}
                className="text-6xl hover:scale-110 transition-transform duration-300"
              >
                😐
              </button>
              <button
                onClick={() => handleEmojiClick('happy')}
                className="text-6xl hover:scale-110 transition-transform duration-300"
              >
                😊
              </button>
            </div>
          </div>
        </div>
      )}

      {showFeedback && (
        <FeedbackModal
          onSubmit={handleFeedbackSubmit}
          onClose={() => setShowFeedback(false)}
          submitted={feedbackSubmitted}
        />
      )}
    </div>
  )
}


'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import { TestData, Mistake } from '../types'
import 'katex/dist/katex.min.css'
import { InlineMath } from 'react-katex'

interface MistakeAnalysisProps {
  testData: TestData
  onAnalysisComplete: (mistakes: Mistake[]) => void
}

export default function MistakeAnalysis({ testData, onAnalysisComplete }: MistakeAnalysisProps) {
  const [analyzing, setAnalyzing] = useState(false)
  const [mistakes, setMistakes] = useState<Mistake[]>([])
  const [summary, setSummary] = useState('')
  const [userAnswers, setUserAnswers] = useState<Record<number, string>>({})
  const [correctAnswers, setCorrectAnswers] = useState<Record<number, string>>({})

  useEffect(() => {
    // Auto-analyze when component mounts
    handleAnalyze()
  }, [])

  const handleAnalyze = async () => {
    setAnalyzing(true)
    try {
      // For now, we'll use the extracted equations as user answers
      // In a real app, you'd have a UI to input answers or mark correct/incorrect
      const response = await axios.post('http://localhost:8000/api/analyze-mistakes', {
        test_id: testData.test_id,
        user_answers: userAnswers,
        correct_answers: correctAnswers,
      })

      setMistakes(response.data.mistakes || [])
      setSummary(response.data.summary || '')
      
      if (response.data.mistakes && response.data.mistakes.length > 0) {
        onAnalysisComplete(response.data.mistakes)
      }
    } catch (error) {
      console.error('Analysis error:', error)
      alert('Error analyzing mistakes. Please try again.')
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-semibold mb-4">Mistake Analysis</h2>

      {analyzing ? (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Analyzing your mistakes...</p>
        </div>
      ) : (
        <>
          {summary && (
            <div className="mb-6 p-4 bg-blue-50 rounded-lg">
              <h3 className="font-semibold mb-2">Summary</h3>
              <p className="text-gray-700">{summary}</p>
            </div>
          )}

          {mistakes.length > 0 ? (
            <div className="space-y-6">
              {mistakes.map((mistake, index) => (
                <div
                  key={index}
                  className="border-l-4 border-red-500 pl-4 py-2 bg-red-50 rounded-r-lg"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-lg">
                      Question #{mistake.question_number}
                    </h3>
                    <span className="px-3 py-1 bg-red-200 text-red-800 rounded-full text-sm font-medium">
                      {mistake.weak_area}
                    </span>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <p className="font-medium text-gray-700">What you did wrong:</p>
                      <p className="text-gray-600">{mistake.mistake_description}</p>
                    </div>

                    <div>
                      <p className="font-medium text-gray-700">Why it's wrong:</p>
                      <p className="text-gray-600">{mistake.why_wrong}</p>
                    </div>

                    <div>
                      <p className="font-medium text-gray-700">How to fix it:</p>
                      <p className="text-gray-600">{mistake.how_to_fix}</p>
                    </div>

                    {mistake.user_answer && (
                      <div>
                        <p className="font-medium text-gray-700">Your answer:</p>
                        <div className="bg-gray-100 p-2 rounded">
                          <InlineMath math={mistake.user_answer} />
                        </div>
                      </div>
                    )}

                    {mistake.correct_answer && (
                      <div>
                        <p className="font-medium text-green-700">Correct answer:</p>
                        <div className="bg-green-50 p-2 rounded">
                          <InlineMath math={mistake.correct_answer} />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-600">
                No mistakes detected. Great job! Or please provide answers for analysis.
              </p>
            </div>
          )}

          {mistakes.length > 0 && (
            <div className="mt-6 p-4 bg-green-50 rounded-lg">
              <p className="text-green-800 font-medium">
                ✓ Analysis complete! Practice questions are being generated...
              </p>
            </div>
          )}
        </>
      )}
    </div>
  )
}


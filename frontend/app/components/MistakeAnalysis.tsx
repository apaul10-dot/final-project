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
  const [userAnswers, setUserAnswers] = useState<Record<string, string>>({})
  const [correctAnswers, setCorrectAnswers] = useState<Record<string, string>>({})
  const [rawText, setRawText] = useState('')

  useEffect(() => {
    // Use extracted answers from upload
    if (testData && testData.user_answers) {
      setUserAnswers(testData.user_answers)
    }
    // Auto-analyze when component mounts
    handleAnalyze()
  }, [testData])

  const handleAnalyze = async () => {
    setAnalyzing(true)
    try {
      // Check backend connection
      try {
        const healthCheck = await axios.get('/health')
        if (!healthCheck.data || !healthCheck.data.status) {
          throw new Error('Backend health check failed')
        }
      } catch (error) {
        throw new Error('Cannot connect to backend server. Please make sure the server is running.')
      }

      if (!testData || !testData.test_id) {
        throw new Error('Test data is missing. Please upload a test first.')
      }

      // Use extracted answers from testData, or fallback to userAnswers state
      const answersToUse = Object.keys(testData.user_answers || {}).length > 0 
        ? testData.user_answers 
        : userAnswers

      if (Object.keys(answersToUse).length === 0) {
        throw new Error('No answers found in the uploaded test images. Please make sure your test images contain visible answers.')
      }

      const response = await axios.post('/api/analyze-mistakes', {
        test_id: testData.test_id,
        user_answers: answersToUse,
        correct_answers: correctAnswers,
      }, {
        timeout: 60000, // 60 second timeout for AI analysis
      })

      if (!response.data) {
        throw new Error('Invalid response from server')
      }

      const mistakes = response.data.mistakes || []
      const summary = response.data.summary || ''

      setMistakes(mistakes)
      setSummary(summary)
      
      // Always call onAnalysisComplete, even if no mistakes (for UI flow)
      onAnalysisComplete(mistakes)
      
      // Show appropriate message
      if (mistakes.length === 0) {
        // Check if we have answers to analyze
        const answersToUse = Object.keys(testData.user_answers || {}).length > 0 
          ? testData.user_answers 
          : userAnswers
        
        if (Object.keys(answersToUse).length === 0) {
          // This shouldn't happen if validation worked, but just in case
          console.warn('No answers found for analysis')
        } else {
          // Answers were analyzed but no mistakes found
          console.log('Analysis complete: No mistakes detected')
        }
      } else {
        console.log(`Analysis complete: ${mistakes.length} mistake(s) found`)
      }
    } catch (error) {
      console.error('Analysis error:', error)
      if (axios.isAxiosError(error)) {
        if (error.code === 'ECONNREFUSED') {
          alert('Cannot connect to server. Please make sure the backend is running.')
        } else if (error.response) {
          alert(`Server error: ${error.response.status} - ${error.response.data?.detail || 'Unknown error'}`)
        } else {
          alert(`Analysis error: ${error.message}`)
        }
      } else {
        alert(`Error analyzing mistakes: ${error instanceof Error ? error.message : 'Unknown error'}`)
      }
    } finally {
      setAnalyzing(false)
    }
  }

  const handleAnalyzeText = async () => {
    if (!rawText.trim()) {
      alert('Please paste questions and answers to analyze.')
      return
    }

    setAnalyzing(true)
    try {
      // Check backend connection
      try {
        const healthCheck = await axios.get('/health')
        if (!healthCheck.data || !healthCheck.data.status) {
          throw new Error('Backend health check failed')
        }
      } catch (error) {
        throw new Error('Cannot connect to backend server. Please make sure the server is running.')
      }

      const response = await axios.post('/api/analyze-text', {
        test_id: testData?.test_id || 'text-analysis',
        text: rawText,
      }, {
        timeout: 60000,
      })

      if (!response.data) {
        throw new Error('Invalid response from server')
      }

      const mistakes = response.data.mistakes || []
      const summary = response.data.summary || ''

      setMistakes(mistakes)
      setSummary(summary)
      onAnalysisComplete(mistakes)
    } catch (error) {
      console.error('Analysis error (text):', error)
      if (axios.isAxiosError(error)) {
        if (error.code === 'ECONNREFUSED') {
          alert('Cannot connect to server. Please make sure the backend is running.')
        } else if (error.response) {
          alert(`Server error: ${error.response.status} - ${error.response.data?.detail || 'Unknown error'}`)
        } else {
          alert(`Analysis error: ${error.message}`)
        }
      } else {
        alert(`Error analyzing pasted text: ${error instanceof Error ? error.message : 'Unknown error'}`)
      }
    } finally {
      setAnalyzing(false)
    }
  }

  // Show extracted answers if available
  const extractedAnswers = testData?.user_answers || {}
  const hasExtractedAnswers = Object.keys(extractedAnswers).length > 0

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-semibold mb-4">Mistake Analysis</h2>

      {/* Pasted text analysis */}
      <div className="mb-4 bg-gray-50 p-4 rounded-lg border border-gray-200">
        <h3 className="font-semibold text-gray-800 mb-2">Paste questions & answers (optional)</h3>
        <p className="text-sm text-gray-600 mb-2">If you copied text instead of uploading images, paste it here and click Analyze Text.</p>
        <textarea
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
          className="w-full border rounded p-2 text-sm h-24 mb-2"
          placeholder={`Example:\n1. What is 2+2? Answer: 5\n2. Derivative of sin(x)? Answer: cos(x)`}
        />
        <button
          onClick={handleAnalyzeText}
          disabled={analyzing}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {analyzing ? 'Analyzing...' : 'Analyze Text'}
        </button>
      </div>

      {hasExtractedAnswers && !analyzing && (
        <div className="mb-4 p-4 bg-green-50 rounded-lg border border-green-200">
          <h3 className="font-semibold text-green-800 mb-2">✓ Answers Extracted from Images</h3>
          <p className="text-sm text-green-700 mb-2">
            Found {Object.keys(extractedAnswers).length} answer{Object.keys(extractedAnswers).length !== 1 ? 's' : ''} in your test images:
          </p>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {Object.entries(extractedAnswers).slice(0, 5).map(([qNum, answer]) => (
              <div key={qNum} className="text-sm text-green-800">
                <span className="font-medium">Q{qNum}:</span> {answer.length > 50 ? answer.substring(0, 50) + '...' : answer}
              </div>
            ))}
            {Object.keys(extractedAnswers).length > 5 && (
              <div className="text-sm text-green-600">... and {Object.keys(extractedAnswers).length - 5} more</div>
            )}
          </div>
        </div>
      )}

      {analyzing ? (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Analyzing your mistakes...</p>
          {hasExtractedAnswers && (
            <p className="mt-2 text-sm text-gray-500">
              Using {Object.keys(extractedAnswers).length} extracted answer{Object.keys(extractedAnswers).length !== 1 ? 's' : ''}
            </p>
          )}
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
              <p className="text-green-800 font-medium mb-2">
                ✓ Analysis complete! {mistakes.length} mistake{mistakes.length !== 1 ? 's' : ''} identified.
              </p>
              <p className="text-green-700 text-sm">
                Click "Generate Practice Questions" below to create personalized practice problems.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  )
}




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
        const healthCheck = await axios.get('http://localhost:8000/health')
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
      let answersToUse = Object.keys(testData.user_answers || {}).length > 0 
        ? testData.user_answers 
        : userAnswers

      // CRITICAL FIX: If no answers extracted but we have text, automatically extract from text
      if (Object.keys(answersToUse).length === 0 && testData.extracted_text && testData.extracted_text.trim().length > 20) {
        console.log('No answers from upload, automatically extracting from extracted text...')
        try {
          // Use analyze-text endpoint which will extract answers AND analyze them
          const textResponse = await axios.post('http://localhost:8000/api/analyze-text', {
            test_id: testData.test_id,
            text: testData.extracted_text,
          }, {
            timeout: 60000,
          })
          
          // analyze-text now returns user_answers and questions in the response!
          if (textResponse.data) {
            const extractedAnswers = textResponse.data.user_answers || {}
            const extractedQuestions = textResponse.data.questions || {}
            const mistakes = textResponse.data.mistakes || []
            const summary = textResponse.data.summary || ''
            
            // If we got answers from analyze-text, use them!
            if (Object.keys(extractedAnswers).length > 0) {
              console.log(`✅ Successfully extracted ${Object.keys(extractedAnswers).length} answers from text!`)
              
              // Update state with extracted answers
              setUserAnswers(extractedAnswers)
              
              // Use the extracted answers for analysis
              answersToUse = extractedAnswers
              
              // If analyze-text already analyzed (has mistakes), use those results directly
              if (mistakes.length > 0 || (summary && !summary.toLowerCase().includes('no answers'))) {
                setMistakes(mistakes)
                setSummary(summary)
                onAnalysisComplete(mistakes)
                setAnalyzing(false)
                return // Success! Don't continue to analyze-mistakes
              }
              
              // Otherwise, continue to analyze-mistakes with extracted answers
            } else {
              console.log('⚠️ analyze-text returned but no answers found')
              setAnalyzing(false)
              alert(`Answers were not automatically extracted from the image.`)
              return
            }
          }
        } catch (textError) {
          console.warn('Failed to extract from text:', textError)
          setAnalyzing(false)
          alert(`Could not automatically extract answers.`)
          return
        }
      }

      // Final check - if still no answers after all attempts
      if (Object.keys(answersToUse).length === 0) {
        setAnalyzing(false)
        alert('No answers were automatically extracted.')
        return
      }

      const response = await axios.post('http://localhost:8000/api/analyze-mistakes', {
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


  // Show extracted answers if available
  const extractedAnswers = testData?.user_answers || {}
  const hasExtractedAnswers = Object.keys(extractedAnswers).length > 0

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-3xl font-bold mb-6 text-gray-900">Mistake Analysis</h2>


      {hasExtractedAnswers && !analyzing && (
        <div className="mb-5 p-5 bg-green-50 rounded-lg border-2 border-green-300">
          <h3 className="font-bold text-lg text-green-900 mb-3">✓ Answers Extracted from Images</h3>
          <p className="text-base text-green-800 mb-3">
            Found {Object.keys(extractedAnswers).length} answer{Object.keys(extractedAnswers).length !== 1 ? 's' : ''} in your test images:
          </p>
          <div className="space-y-2 max-h-32 overflow-y-auto">
            {Object.entries(extractedAnswers).slice(0, 5).map(([qNum, answer]) => (
              <div key={qNum} className="text-base text-green-900">
                <span className="font-bold">Q{qNum}:</span> {answer.length > 50 ? answer.substring(0, 50) + '...' : answer}
              </div>
            ))}
            {Object.keys(extractedAnswers).length > 5 && (
              <div className="text-base text-green-700 font-medium">... and {Object.keys(extractedAnswers).length - 5} more</div>
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
            <div className="mb-6 p-6 bg-blue-50 rounded-lg border-2 border-blue-200">
              <h3 className="font-bold text-xl mb-3 text-gray-900">Summary</h3>
              <p className="text-gray-800 text-lg leading-relaxed">{summary}</p>
            </div>
          )}

          {mistakes.length > 0 ? (
            <div className="space-y-6">
              {mistakes.map((mistake, index) => (
                <div
                  key={index}
                  className="border-l-4 border-red-500 pl-4 py-2 bg-red-50 rounded-r-lg"
                >
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-bold text-2xl text-gray-900">
                      Question #{mistake.question_number}
                    </h3>
                    <span className="px-4 py-2 bg-red-200 text-red-900 rounded-full text-base font-bold">
                      {mistake.weak_area}
                    </span>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <p className="font-bold text-lg text-gray-800 mb-2">What you did wrong:</p>
                      <p className="text-gray-700 text-base leading-relaxed">{mistake.mistake_description}</p>
                    </div>

                    <div>
                      <p className="font-bold text-lg text-gray-800 mb-2">Why it's wrong:</p>
                      <p className="text-gray-700 text-base leading-relaxed">{mistake.why_wrong}</p>
                    </div>

                    <div>
                      <p className="font-bold text-lg text-gray-800 mb-2">How to fix it:</p>
                      <p className="text-gray-700 text-base leading-relaxed">{mistake.how_to_fix}</p>
                    </div>

                    {mistake.user_answer && (
                      <div>
                        <p className="font-bold text-lg text-gray-800 mb-2">Your answer:</p>
                        <div className="bg-gray-100 p-3 rounded border border-gray-300">
                          <InlineMath math={mistake.user_answer} />
                        </div>
                      </div>
                    )}

                    {mistake.correct_answer && (
                      <div>
                        <p className="font-bold text-lg text-green-800 mb-2">Correct answer:</p>
                        <div className="bg-green-50 p-3 rounded border-2 border-green-300">
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
            <div className="mt-6 p-5 bg-green-50 rounded-lg border-2 border-green-200">
              <p className="text-green-900 font-bold text-lg mb-2">
                ✓ Analysis complete! {mistakes.length} mistake{mistakes.length !== 1 ? 's' : ''} identified.
              </p>
              <p className="text-green-800 text-base">
                Click "Generate Practice Questions" below to create personalized practice problems.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  )
}




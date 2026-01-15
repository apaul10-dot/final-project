'use client'

import { useState } from 'react'
import ImageUpload from './components/ImageUpload'
import MistakeAnalysis from './components/MistakeAnalysis'
import PracticeQuestions from './components/PracticeQuestions'
import { TestData, Mistake, PracticeQuestion as PracticeQuestionType } from './types'

export default function Home() {
  const [currentStep, setCurrentStep] = useState<'upload' | 'analysis' | 'practice'>('upload')
  const [testData, setTestData] = useState<TestData | null>(null)
  const [mistakes, setMistakes] = useState<Mistake[]>([])
  const [practiceQuestions, setPracticeQuestions] = useState<PracticeQuestionType[]>([])
  const [generatingPractice, setGeneratingPractice] = useState(false)

  const handleUploadComplete = (data: TestData) => {
    setTestData(data)
    setCurrentStep('analysis')
  }

  const handleAnalysisComplete = (analysisMistakes: Mistake[]) => {
    setMistakes(analysisMistakes)
    // Don't auto-generate, wait for user to click button
  }

  const handleGeneratePractice = async () => {
    if (mistakes.length === 0) {
      alert('Please analyze mistakes first before generating practice questions.')
      return
    }
    setGeneratingPractice(true)
    await generatePracticeQuestions(mistakes)
    setGeneratingPractice(false)
  }

  const generatePracticeQuestions = async (mistakes: Mistake[]) => {
    if (!testData) {
      alert('Test data not found. Please upload a test first.')
      return
    }

    if (mistakes.length === 0) {
      alert('No mistakes found. Please analyze your test first.')
      return
    }

    try {
      // Build original questions from mistakes (extract question numbers and answers)
      const originalQuestions: Record<string, string> = {}
      mistakes.forEach(m => {
        if (m.question_number) {
          const qNum = m.question_number.toString()
          originalQuestions[qNum] = m.user_answer || m.correct_answer || `Question ${qNum}`
        }
      })

      // Check backend connection
      const healthCheck = await fetch('http://localhost:8000/health')
      if (!healthCheck.ok) {
        throw new Error('Backend server is not responding')
      }

      const response = await fetch('http://localhost:8000/api/generate-practice', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          test_id: testData.test_id,
          mistake_ids: mistakes.map(m => m.id || m.question_number?.toString() || ''),
          mistakes: mistakes.map(m => ({
            question_number: m.question_number,
            mistake_description: m.mistake_description,
            why_wrong: m.why_wrong,
            how_to_fix: m.how_to_fix,
            weak_area: m.weak_area,
            user_answer: m.user_answer,
            correct_answer: m.correct_answer,
          })),
          original_questions: originalQuestions,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || `Server error: ${response.status}`)
      }

      const data = await response.json()
      
      if (!data.questions || data.questions.length === 0) {
        alert('No practice questions were generated. Please try again.')
        return
      }

      setPracticeQuestions(data.questions)
      setCurrentStep('practice')
    } catch (error) {
      console.error('Error generating practice questions:', error)
      alert(`Error generating practice questions: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            ExplainIt
          </h1>
          <p className="text-gray-600">
            Upload your tests, identify mistakes, and strengthen your weak areas
          </p>
        </div>

        {/* Progress Steps */}
        <div className="mb-8 flex justify-center">
          <div className="flex items-center space-x-4">
            <StepIndicator step={1} active={currentStep === 'upload'} completed={currentStep !== 'upload'} label="Upload Test" />
            <div className="w-16 h-1 bg-gray-300"></div>
            <StepIndicator step={2} active={currentStep === 'analysis'} completed={currentStep === 'practice'} label="Analyze Mistakes" />
            <div className="w-16 h-1 bg-gray-300"></div>
            <StepIndicator step={3} active={currentStep === 'practice'} completed={false} label="Practice" />
          </div>
        </div>

        {/* Content */}
        {currentStep === 'upload' && (
          <ImageUpload onUploadComplete={handleUploadComplete} />
        )}

        {currentStep === 'analysis' && testData && (
          <>
            <MistakeAnalysis
              testData={testData}
              onAnalysisComplete={handleAnalysisComplete}
            />
            {mistakes.length > 0 && (
              <div className="mt-4 flex justify-center">
                <button
                  onClick={handleGeneratePractice}
                  disabled={generatingPractice}
                  className="px-6 py-3 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                >
                  {generatingPractice ? (
                    <>
                      <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      Generating Practice Questions...
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Generate Practice Questions
                    </>
                  )}
                </button>
              </div>
            )}
          </>
        )}

        {currentStep === 'practice' && practiceQuestions.length > 0 && (
          <PracticeQuestions
            questions={practiceQuestions}
            testId={testData?.test_id || ''}
          />
        )}
      </div>
    </main>
  )
}

function StepIndicator({ step, active, completed, label }: { step: number; active: boolean; completed: boolean; label: string }) {
  return (
    <div className="flex flex-col items-center">
      <div
        className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
          active
            ? 'bg-blue-600 text-white'
            : completed
            ? 'bg-green-500 text-white'
            : 'bg-gray-300 text-gray-600'
        }`}
      >
        {completed ? '✓' : step}
      </div>
      <span className="mt-2 text-sm text-gray-600">{label}</span>
    </div>
  )
}




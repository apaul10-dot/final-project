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

  const handleUploadComplete = (data: TestData) => {
    setTestData(data)
    setCurrentStep('analysis')
  }

  const handleAnalysisComplete = (analysisMistakes: Mistake[]) => {
    setMistakes(analysisMistakes)
    // Auto-generate practice questions
    generatePracticeQuestions(analysisMistakes.map(m => m.id || ''))
  }

  const generatePracticeQuestions = async (mistakeIds: string[]) => {
    if (!testData) return

    try {
      const response = await fetch('http://localhost:8000/api/generate-practice', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          test_id: testData.test_id,
          mistake_ids: mistakeIds,
        }),
      })

      const data = await response.json()
      setPracticeQuestions(data.questions)
      setCurrentStep('practice')
    } catch (error) {
      console.error('Error generating practice questions:', error)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Test Analysis & Practice
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
          <MistakeAnalysis
            testData={testData}
            onAnalysisComplete={handleAnalysisComplete}
          />
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


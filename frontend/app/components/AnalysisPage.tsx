'use client'

import { useState, useEffect } from 'react'
import 'katex/dist/katex.min.css'
import { InlineMath } from 'react-katex'

interface AnalysisPageProps {
  analysisData: any
  onNext: () => void
}

export default function AnalysisPage({ analysisData, onNext }: AnalysisPageProps) {
  const [fadeIn, setFadeIn] = useState(false)

  useEffect(() => {
    setFadeIn(true)
  }, [])

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleNext()
    }
  }

  const handleNext = () => {
    onNext()
  }

  const mistakes = analysisData?.mistakes || []
  const summary = analysisData?.summary || ''

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-12" onKeyPress={handleKeyPress} tabIndex={0}>
      <div className={`max-w-4xl w-full transition-opacity duration-700 ${fadeIn ? 'opacity-100' : 'opacity-0'}`}>
        {summary && (
          <div className="mb-12 text-center">
            <p className="text-2xl text-black font-light leading-relaxed">{summary}</p>
          </div>
        )}

        <div className="space-y-8 mb-12">
          {mistakes.map((mistake: any, index: number) => (
            <div
              key={index}
              className="border-l-4 border-blue-500 pl-6 py-4 bg-white"
            >
              <h3 className="text-2xl font-light text-black mb-4">
                Question #{mistake.question_number}
              </h3>
              
              <div className="space-y-4 text-lg text-gray-800 font-light">
                <div>
                  <p className="font-medium mb-2">What you did wrong:</p>
                  <p className="leading-relaxed">{mistake.mistake_description}</p>
                </div>

                <div>
                  <p className="font-medium mb-2">Why it's wrong:</p>
                  <p className="leading-relaxed">{mistake.why_wrong}</p>
                </div>

                <div>
                  <p className="font-medium mb-2">How to fix it:</p>
                  <p className="leading-relaxed">{mistake.how_to_fix}</p>
                </div>

                {mistake.user_answer && (
                  <div>
                    <p className="font-medium mb-2">Your answer:</p>
                    <div className="bg-gray-100 p-3 rounded">
                      <InlineMath math={mistake.user_answer} />
                    </div>
                  </div>
                )}

                {mistake.correct_answer && (
                  <div>
                    <p className="font-medium mb-2">Correct answer:</p>
                    <div className="bg-blue-50 p-3 rounded">
                      <InlineMath math={mistake.correct_answer} />
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="text-center">
          <button
            onClick={handleNext}
            className="px-8 py-3 bg-blue-500 text-white rounded-lg text-lg font-medium hover:bg-blue-600 transition-all duration-300"
          >
            I understand
          </button>
        </div>
      </div>
    </div>
  )
}


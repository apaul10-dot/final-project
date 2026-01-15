'use client'

import { useState, useEffect } from 'react'
import 'katex/dist/katex.min.css'
import { BlockMath } from 'react-katex'

interface PracticeQuestionsPageProps {
  questions: any[]
  onAnswerSubmit: (questionId: number, answer: string) => void
  onNext: () => void
  allAnswered: boolean
}

export default function PracticeQuestionsPage({ questions, onAnswerSubmit, onNext, allAnswered }: PracticeQuestionsPageProps) {
  const [answers, setAnswers] = useState<Record<number, string>>({})
  const [fadeIn, setFadeIn] = useState(false)

  useEffect(() => {
    setFadeIn(true)
  }, [])

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && allAnswered) {
      handleNext()
    }
  }

  const handleAnswerChange = (questionId: number, answer: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: answer }))
    onAnswerSubmit(questionId, answer)
  }

  const handleNext = () => {
    if (allAnswered) {
      onNext()
    }
  }

  // Show 3 questions (or all if less than 3)
  const displayQuestions = (questions.length > 0 ? questions : [
    { id: 0, question_text: '\\text{Question 1}' },
    { id: 1, question_text: '\\text{Question 2}' },
    { id: 2, question_text: '\\text{Question 3}' }
  ]).slice(0, 3)

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-12" onKeyPress={handleKeyPress} tabIndex={0}>
      <div className={`max-w-4xl w-full transition-opacity duration-700 ${fadeIn ? 'opacity-100' : 'opacity-0'}`}>
        <div className="space-y-12 mb-12">
          {displayQuestions.map((question, index) => (
            <div key={question.id || index} className="text-left">
              <div className="mb-4">
                <BlockMath math={question.question_text || question.question} />
              </div>
              <input
                type="text"
                value={answers[index] || ''}
                onChange={(e) => handleAnswerChange(index, e.target.value)}
                className="w-full max-w-2xl px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 transition-all duration-300 bg-white text-black placeholder-gray-400 text-lg"
                placeholder="Enter your answer"
              />
            </div>
          ))}
        </div>

        {allAnswered && (
          <div className="text-center">
            <button
              onClick={handleNext}
              className="px-8 py-3 bg-blue-500 text-white rounded-lg text-lg font-medium hover:bg-blue-600 transition-all duration-300 opacity-0 animate-fadeIn"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  )
}


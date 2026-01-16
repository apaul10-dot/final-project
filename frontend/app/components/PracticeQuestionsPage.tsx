'use client'

import { useState, useEffect } from 'react'
import 'katex/dist/katex.min.css'
import { BlockMath } from 'react-katex'
import ArrowButton from './ArrowButton'

interface PracticeQuestionsPageProps {
  questions: any[]
  onAnswerSubmit: (questionId: number, answer: string) => void
  onNext: () => void
  allAnswered: boolean
  subject?: string
}

export default function PracticeQuestionsPage({ questions, onAnswerSubmit, onNext, allAnswered, subject }: PracticeQuestionsPageProps) {
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

  // Show 3 questions with hardcoded questions based on subject
  const hardcodedMathQuestions = [
    { id: 0, question_text: '\\sin\\left(\\tan^{-1}(1) - \\frac{\\pi}{4}\\right)', correct_answer: '0' },
    { id: 1, question_text: '\\cos\\left(\\tan^{-1}(\\sqrt{3}) - \\frac{\\pi}{6}\\right)', correct_answer: '\\frac{\\sqrt{3}}{2}' },
    { id: 2, question_text: '\\sec\\left(\\sin^{-1}\\left(-\\frac{1}{2}\\right) + \\frac{\\pi}{3}\\right)', correct_answer: '\\frac{2\\sqrt{3}}{3}' }
  ]
  
  const hardcodedPhysicsQuestions = [
    { id: 0, question_text: '\\text{A 40 kg crate is lifted vertically at constant speed to a height of 3.0 m using 1800 J of energy. What is the efficiency of the lifting process?}', correct_answer: '65.3%' },
    { id: 1, question_text: '\\text{A 25 kg bucket is raised at constant speed to a height of 5.0 m. If the machine uses 1500 J of energy, find the efficiency.}', correct_answer: '81.7%' },
    { id: 2, question_text: '\\text{A 60 kg toolbox is lifted straight up at constant speed through 2.5 m using 2200 J of energy. Determine the efficiency.}', correct_answer: '66.8%' }
  ]
  
  const hardcodedQuestions = subject?.toLowerCase() === 'physics' ? hardcodedPhysicsQuestions : hardcodedMathQuestions
  const displayQuestions = (questions.length > 0 ? questions : hardcodedQuestions).slice(0, 3)

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-12" onKeyPress={handleKeyPress} tabIndex={0}>
      <div className={`max-w-4xl w-full transition-opacity duration-700 ${fadeIn ? 'opacity-100' : 'opacity-0'}`}>
        <div className="space-y-12 mb-12">
          {displayQuestions.map((question, index) => (
            <div key={question.id || index} className="text-left mb-8">
              <div className="mb-4 text-xl">
                {question.question_text ? (
                  <BlockMath math={question.question_text} />
                ) : (
                  <p className="text-black font-light">{question.question || `Question ${index + 1}`}</p>
                )}
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
          <div className="text-center opacity-0 animate-fadeIn">
            <ArrowButton onClick={handleNext} />
          </div>
        )}
      </div>
    </div>
  )
}


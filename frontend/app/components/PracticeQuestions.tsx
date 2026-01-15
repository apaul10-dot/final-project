'use client'

import { useState } from 'react'
import axios from 'axios'
import { useDropzone } from 'react-dropzone'
import { PracticeQuestion, PracticeAnswer } from '../types'
import 'katex/dist/katex.min.css'
import { InlineMath, BlockMath } from 'react-katex'

interface PracticeQuestionsProps {
  questions: PracticeQuestion[]
  testId: string
}

export default function PracticeQuestions({ questions, testId }: PracticeQuestionsProps) {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [submittedAnswers, setSubmittedAnswers] = useState<Record<number, PracticeAnswer>>({})
  const [submitting, setSubmitting] = useState(false)
  const [answerImage, setAnswerImage] = useState<File | null>(null)

  const currentQuestion = questions[currentQuestionIndex]
  const currentAnswer = submittedAnswers[currentQuestionIndex]

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setAnswerImage(acceptedFiles[0])
      }
    },
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp']
    },
    multiple: false
  })

  const handleSubmitAnswer = async () => {
    if (!answerImage || !currentQuestion.id) return

    setSubmitting(true)
    try {
      const formData = new FormData()
      formData.append('answer_image', answerImage)
      formData.append('question_id', currentQuestion.id || '')
      if (currentQuestion.question_text) {
        formData.append('question_text', currentQuestion.question_text)
      }
      if (currentQuestion.correct_answer) {
        formData.append('correct_answer', currentQuestion.correct_answer)
      }

      const response = await axios.post<PracticeAnswer>(
        'http://localhost:8000/api/submit-practice-answer',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      )

      setSubmittedAnswers(prev => ({
        ...prev,
        [currentQuestionIndex]: response.data
      }))
    } catch (error) {
      console.error('Error submitting answer:', error)
      alert('Error submitting answer. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleNextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1)
      setAnswerImage(null)
    }
  }

  const handlePreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1)
      setAnswerImage(null)
    }
  }

  const progress = ((currentQuestionIndex + 1) / questions.length) * 100
  const completedCount = Object.keys(submittedAnswers).length

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <h2 className="text-2xl font-semibold">Practice Questions</h2>
          <span className="text-gray-600">
            Question {currentQuestionIndex + 1} of {questions.length}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      </div>

      {currentQuestion && (
        <div className="space-y-6">
          {/* Question */}
          <div className="border-l-4 border-blue-500 pl-4 py-2 bg-blue-50 rounded-r-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="px-3 py-1 bg-blue-200 text-blue-800 rounded-full text-sm font-medium">
                {currentQuestion.topic} • {currentQuestion.difficulty}
              </span>
            </div>
            <div className="text-lg text-gray-800">
              <BlockMath math={currentQuestion.question_text} />
            </div>
          </div>

          {/* Answer Submission */}
          {!currentAnswer ? (
            <div>
              <h3 className="font-semibold mb-3">Submit your answer:</h3>
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                  isDragActive
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 hover:border-blue-400'
                }`}
              >
                <input {...getInputProps()} />
                {answerImage ? (
                  <div className="space-y-2">
                    <img
                      src={URL.createObjectURL(answerImage)}
                      alt="Answer preview"
                      className="max-h-64 mx-auto rounded-lg"
                    />
                    <p className="text-sm text-gray-600">{answerImage.name}</p>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setAnswerImage(null)
                      }}
                      className="text-red-600 text-sm"
                    >
                      Remove
                    </button>
                  </div>
                ) : (
                  <div>
                    <p className="text-gray-600">
                      {isDragActive
                        ? 'Drop the image here...'
                        : 'Drag & drop your answer image here, or click to select'}
                    </p>
                  </div>
                )}
              </div>

              <button
                onClick={handleSubmitAnswer}
                disabled={!answerImage || submitting}
                className="w-full mt-4 bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {submitting ? 'Submitting...' : 'Submit Answer'}
              </button>
            </div>
          ) : (
            /* Feedback */
            <div
              className={`border-l-4 rounded-r-lg p-4 ${
                currentAnswer.is_correct
                  ? 'border-green-500 bg-green-50'
                  : 'border-red-500 bg-red-50'
              }`}
            >
              <div className="flex items-center mb-3">
                {currentAnswer.is_correct ? (
                  <>
                    <svg className="w-6 h-6 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <h3 className="text-lg font-semibold text-green-800">Correct! Great job!</h3>
                  </>
                ) : (
                  <>
                    <svg className="w-6 h-6 text-red-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <h3 className="text-lg font-semibold text-red-800">Not quite right</h3>
                  </>
                )}
              </div>

              <div className="space-y-3">
                <div>
                  <p className="font-medium text-gray-700 mb-1">Feedback:</p>
                  <p className="text-gray-600">{currentAnswer.feedback}</p>
                </div>

                {currentAnswer.explanation && (
                  <div>
                    <p className="font-medium text-gray-700 mb-1">Explanation:</p>
                    <p className="text-gray-600">{currentAnswer.explanation}</p>
                  </div>
                )}

                <div>
                  <p className="font-medium text-gray-700 mb-1">Correct Answer:</p>
                  <div className="bg-white p-2 rounded">
                    <BlockMath math={currentQuestion.correct_answer} />
                  </div>
                </div>

                {currentQuestion.solution_steps && currentQuestion.solution_steps.length > 0 && (
                  <div>
                    <p className="font-medium text-gray-700 mb-2">Solution Steps:</p>
                    <ol className="list-decimal list-inside space-y-1 text-gray-600">
                      {currentQuestion.solution_steps.map((step, idx) => (
                        <li key={idx}>{step}</li>
                      ))}
                    </ol>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Navigation */}
          <div className="flex justify-between pt-4 border-t">
            <button
              onClick={handlePreviousQuestion}
              disabled={currentQuestionIndex === 0}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              Previous
            </button>
            <button
              onClick={handleNextQuestion}
              disabled={currentQuestionIndex === questions.length - 1}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Completion Summary */}
      {completedCount === questions.length && (
        <div className="mt-6 p-4 bg-green-50 rounded-lg border border-green-200">
          <h3 className="font-semibold text-green-800 mb-2">🎉 Practice Session Complete!</h3>
          <p className="text-green-700">
            You've completed all {questions.length} practice questions. Keep practicing to strengthen your weak areas!
          </p>
        </div>
      )}
    </div>
  )
}




'use client'

import { useState, useEffect } from 'react'

interface SubjectSelectionProps {
  userName: string
  onSelect: (subject: string) => void
}

const subjects = ['Math', 'Physics', 'Chemistry', 'Biology', 'English', 'History']

export default function SubjectSelection({ userName, onSelect }: SubjectSelectionProps) {
  const [selectedSubject, setSelectedSubject] = useState('')
  const [showNext, setShowNext] = useState(false)
  const [fadeIn, setFadeIn] = useState(false)

  useEffect(() => {
    setFadeIn(true)
  }, [])

  useEffect(() => {
    setShowNext(selectedSubject.length > 0)
  }, [selectedSubject])

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && selectedSubject.length > 0) {
      handleNext()
    }
  }

  const handleNext = () => {
    if (selectedSubject.length > 0) {
      onSelect(selectedSubject)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4" onKeyPress={handleKeyPress} tabIndex={0}>
      <div className={`text-center max-w-4xl w-full transition-opacity duration-700 ${fadeIn ? 'opacity-100' : 'opacity-0'}`}>
        <h1 className="text-5xl md:text-6xl font-light text-black mb-12 tracking-tight">
          Welcome, {userName}
        </h1>
        
        <p className="text-xl text-gray-700 font-light mb-12">
          What subject will you need help with today?
        </p>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-12">
          {subjects.map((subject, index) => (
            <button
              key={subject}
              onClick={() => setSelectedSubject(subject)}
              className={`px-8 py-6 rounded-xl border-2 transition-all duration-300 text-lg font-light animate-float
                ${selectedSubject === subject 
                  ? 'border-blue-500 bg-blue-50 text-blue-700' 
                  : 'border-gray-300 bg-white text-black hover:border-blue-300'
                }`}
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              {subject}
            </button>
          ))}
        </div>

        {showNext && (
          <button
            onClick={handleNext}
            className="px-8 py-3 bg-blue-500 text-white rounded-lg text-lg font-medium hover:bg-blue-600 transition-all duration-300 opacity-0 animate-fadeIn"
          >
            Next
          </button>
        )}
      </div>
    </div>
  )
}


'use client'

import { useState, useEffect, useRef } from 'react'
import ArrowButton from './ArrowButton'

interface WelcomePageProps {
  onComplete: (name: string) => void
}

export default function WelcomePage({ onComplete }: WelcomePageProps) {
  const [name, setName] = useState('')
  const [showNext, setShowNext] = useState(false)
  const [fadeIn, setFadeIn] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    setFadeIn(true)
    inputRef.current?.focus()
  }, [])

  useEffect(() => {
    setShowNext(name.trim().length > 0)
  }, [name])

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && name.trim().length > 0) {
      handleNext()
    }
  }

  const handleNext = () => {
    if (name.trim().length > 0) {
      onComplete(name.trim())
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4">
      <div className={`text-center transition-opacity duration-700 ${fadeIn ? 'opacity-100' : 'opacity-0'}`}>
        <h1 className="text-6xl md:text-7xl font-light text-black mb-12 tracking-tight">
          Welcome to Explain<span className="text-blue-500">It</span>.
        </h1>
        
        <div className="mt-16 space-y-6">
          <p className="text-xl text-gray-700 font-light">Enter your name</p>
          <input
            ref={inputRef}
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyPress={handleKeyPress}
            className="w-full max-w-md px-6 py-4 text-lg border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 transition-all duration-300 bg-white text-black placeholder-gray-400"
            placeholder="Your name"
          />
          
          {showNext && (
            <div className="mt-8 flex justify-center opacity-0 animate-fadeIn">
              <ArrowButton onClick={handleNext} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}


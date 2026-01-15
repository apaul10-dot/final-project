'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'

interface LoadingScreenProps {
  onComplete: (data: any) => void
  testData: any
}

const funFacts = [
  "Did you know? The human brain can process images in just 13 milliseconds!",
  "Fun fact: Honey never spoils. Archaeologists have found 3000-year-old honey that's still edible!",
  "Interesting: Octopuses have three hearts and blue blood!",
  "Did you know? A day on Venus is longer than its year!",
  "Fun fact: Bananas are berries, but strawberries aren't!",
  "Interesting: The human body contains enough iron to make a 3-inch nail!",
  "Did you know? Wombat poop is cube-shaped!",
  "Fun fact: A group of flamingos is called a 'flamboyance'!",
]

export default function LoadingScreen({ onComplete, testData }: LoadingScreenProps) {
  const [currentFactIndex, setCurrentFactIndex] = useState(0)
  const [fadeIn, setFadeIn] = useState(false)
  const [startTime] = useState(Date.now())

  useEffect(() => {
    setFadeIn(true)
    
    // Change fact every 7 seconds
    const factInterval = setInterval(() => {
      setCurrentFactIndex((prev) => (prev + 1) % funFacts.length)
    }, 7000)

    // Wait 20 seconds then analyze
    const analyzeTimeout = setTimeout(async () => {
      try {
        const response = await axios.post('http://localhost:8000/api/analyze-mistakes', {
          test_id: testData.test_id,
          user_answers: testData.user_answers || {},
        }, {
          timeout: 60000,
        })

        if (response.data) {
          // Generate practice questions (limit to 3)
          try {
            const practiceResponse = await axios.post('http://localhost:8000/api/generate-practice', {
              test_id: testData.test_id,
              mistake_ids: (response.data.mistakes || []).map((m: any) => m.question_number?.toString() || ''),
              mistakes: response.data.mistakes || [],
              original_questions: testData.questions || {},
            }, {
              timeout: 60000,
            })

            const practiceQuestions = (practiceResponse.data?.questions || []).slice(0, 3)
            onComplete({
              ...response.data,
              practiceQuestions: practiceQuestions,
            })
          } catch (practiceError) {
            console.error('Practice generation error:', practiceError)
            // Still proceed with analysis but no practice questions
            onComplete({
              ...response.data,
              practiceQuestions: [],
            })
          }
        }
      } catch (error) {
        console.error('Analysis error:', error)
        // Still proceed with empty data
        onComplete({ mistakes: [], summary: '', practiceQuestions: [] })
      }
    }, 20000)

    return () => {
      clearInterval(factInterval)
      clearTimeout(analyzeTimeout)
    }
  }, [testData, onComplete])

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4">
      <div className={`text-center transition-opacity duration-700 ${fadeIn ? 'opacity-100' : 'opacity-0'}`}>
        <div className="mb-12 animate-float">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
        </div>
        
        <div 
          key={currentFactIndex}
          className="animate-fadeIn"
        >
          <p className="text-xl text-gray-700 font-light max-w-2xl">
            {funFacts[currentFactIndex]}
          </p>
        </div>
      </div>
    </div>
  )
}


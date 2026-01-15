'use client'

import { useState, useEffect } from 'react'
import WelcomePage from './components/WelcomePage'
import SubjectSelection from './components/SubjectSelection'
import UploadPage from './components/UploadPage'
import LoadingScreen from './components/LoadingScreen'
import AnalysisPage from './components/AnalysisPage'
import PracticeQuestionsPage from './components/PracticeQuestionsPage'
import ResultsPage from './components/ResultsPage'

type Page = 'welcome' | 'subject' | 'upload' | 'loading' | 'analysis' | 'practice' | 'results'

export default function Home() {
  const [currentPage, setCurrentPage] = useState<Page>('welcome')
  const [fadeIn, setFadeIn] = useState(false)
  const [userName, setUserName] = useState('')
  const [selectedSubject, setSelectedSubject] = useState('')
  const [testData, setTestData] = useState<any>(null)
  const [analysisData, setAnalysisData] = useState<any>(null)
  const [practiceAnswers, setPracticeAnswers] = useState<Record<number, string>>({})
  const [practiceResults, setPracticeResults] = useState<Record<number, boolean>>({})

  useEffect(() => {
    // Fade in animation on mount
    setFadeIn(true)
  }, [])

  const handleWelcomeComplete = (name: string) => {
    setUserName(name)
    setFadeIn(false)
    setTimeout(() => {
      setCurrentPage('subject')
      setFadeIn(true)
    }, 300)
  }

  const handleSubjectSelected = (subject: string) => {
    setSelectedSubject(subject)
    setFadeIn(false)
    setTimeout(() => {
      setCurrentPage('upload')
      setFadeIn(true)
    }, 300)
  }

  const handleUploadComplete = (data: any) => {
    setTestData(data)
    setFadeIn(false)
    setTimeout(() => {
      setCurrentPage('loading')
      setFadeIn(true)
    }, 300)
  }

  const handleAnalysisComplete = (data: any) => {
    setAnalysisData(data)
    setFadeIn(false)
    setTimeout(() => {
      setCurrentPage('analysis')
      setFadeIn(true)
    }, 300)
  }

  const handleAnalysisNext = () => {
    setFadeIn(false)
    setTimeout(() => {
      setCurrentPage('practice')
      setFadeIn(true)
    }, 300)
  }

  const handlePracticeSubmit = (questionId: number, answer: string) => {
    setPracticeAnswers(prev => ({ ...prev, [questionId]: answer }))
  }

  const handlePracticeNext = () => {
    // Simulate checking answers (in real app, this would be API call)
    const results: Record<number, boolean> = {}
    Object.keys(practiceAnswers).forEach(key => {
      results[parseInt(key)] = Math.random() > 0.5 // Random for demo
    })
    setPracticeResults(results)
    setFadeIn(false)
    setTimeout(() => {
      setCurrentPage('results')
      setFadeIn(true)
    }, 300)
  }

  return (
    <div className={`min-h-screen bg-white transition-opacity duration-500 ${fadeIn ? 'opacity-100' : 'opacity-0'}`}>
      {currentPage === 'welcome' && (
        <WelcomePage onComplete={handleWelcomeComplete} />
      )}
      {currentPage === 'subject' && (
        <SubjectSelection 
          userName={userName}
          onSelect={handleSubjectSelected}
        />
      )}
      {currentPage === 'upload' && (
        <UploadPage
          userName={userName}
          subject={selectedSubject}
          onUploadComplete={handleUploadComplete}
        />
      )}
      {currentPage === 'loading' && (
        <LoadingScreen
          onComplete={handleAnalysisComplete}
          testData={testData}
        />
      )}
      {currentPage === 'analysis' && (
        <AnalysisPage
          analysisData={analysisData}
          onNext={handleAnalysisNext}
        />
      )}
      {currentPage === 'practice' && (
        <PracticeQuestionsPage
          questions={analysisData?.practiceQuestions || []}
          onAnswerSubmit={handlePracticeSubmit}
          onNext={handlePracticeNext}
          allAnswered={Object.keys(practiceAnswers).length >= 3}
        />
      )}
      {currentPage === 'results' && (
        <ResultsPage
          answers={practiceAnswers}
          results={practiceResults}
          userName={userName}
        />
      )}
    </div>
  )
}

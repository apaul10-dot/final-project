'use client'

import { useState, useEffect } from 'react'
import WelcomePage from './components/WelcomePage'
import SubjectSelection from './components/SubjectSelection'
import UploadPage from './components/UploadPage'
import LoadingScreen from './components/LoadingScreen'
import AnalysisPage from './components/AnalysisPage'
import PracticeQuestionsPage from './components/PracticeQuestionsPage'
import ResultsPage from './components/ResultsPage'

type Page = 'welcome' | 'subject' | 'upload' | 'loading' | 'loading-practice' | 'analysis' | 'practice' | 'loading-results' | 'results'

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
    // Store subject in testData for later use
    const dataWithSubject = { ...data, subject: selectedSubject }
    setTestData(dataWithSubject)
    // Go straight to loading screen (no initial delay)
    setFadeIn(false)
    setTimeout(() => {
      setCurrentPage('loading')
      setFadeIn(true)
    }, 100)
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
    // Show loading screen for 10 seconds before practice
    setFadeIn(false)
    setTimeout(() => {
      setCurrentPage('loading-practice')
      setFadeIn(true)
    }, 300)
  }

  const handlePracticeLoadingComplete = () => {
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
    // Check answers against hardcoded correct answers based on subject
    const results: Record<number, boolean> = {}
    
    // Math answers (special angles)
    const mathAnswers: Record<number, string[]> = {
      0: ['0'],
      1: ['\\frac{\\sqrt{3}}{2}', 'sqrt(3)/2', '√3/2', '0.866', 'sqrt3/2'],
      2: ['\\frac{2\\sqrt{3}}{3}', '2sqrt(3)/3', '2√3/3', '1.155', '2sqrt3/3']
    }
    
    // Physics answers (efficiency percentages)
    const physicsAnswers: Record<number, string[]> = {
      0: ['65.3%', '65.3', '0.653'],
      1: ['81.7%', '81.7', '0.817'],
      2: ['66.8%', '66.8', '0.668']
    }
    
    const correctAnswers = selectedSubject?.toLowerCase() === 'physics' ? physicsAnswers : mathAnswers
    
    Object.keys(practiceAnswers).forEach(key => {
      const questionId = parseInt(key)
      const userAnswer = practiceAnswers[questionId].trim().toLowerCase().replace(/\s+/g, '')
      const possibleAnswers = correctAnswers[questionId] || []
      
      // Check if user answer matches any of the correct answer formats
      results[questionId] = possibleAnswers.some(correct => {
        const normalizedCorrect = correct.toLowerCase().replace(/\s+/g, '').replace(/[%\\]/g, '')
        const normalizedUser = userAnswer.replace(/[%\\]/g, '')
        return normalizedUser === normalizedCorrect || 
               (normalizedUser.includes('65.3') && questionId === 0) ||
               (normalizedUser.includes('81.7') && questionId === 1) ||
               (normalizedUser.includes('66.8') && questionId === 2) ||
               (normalizedUser === '0' && questionId === 0) ||
               (normalizedUser.includes('sqrt3') && questionId === 1) ||
               (normalizedUser.includes('2sqrt3') && questionId === 2)
      })
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
          duration={25000}
          showAnalysis={true}
        />
      )}
      {currentPage === 'loading-practice' && (
        <LoadingScreen
          onComplete={handlePracticeLoadingComplete}
              testData={testData}
          duration={7000}
          showAnalysis={false}
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
          subject={selectedSubject}
        />
      )}
      {currentPage === 'loading-results' && (
        <LoadingScreen
          onComplete={handleResultsLoadingComplete}
          testData={testData}
          duration={5000}
          showAnalysis={false}
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

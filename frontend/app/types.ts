export interface TestData {
  test_id: string
  extracted_text: string
  equations: string[]
  message: string
}

export interface Mistake {
  id?: string
  question_number: number
  mistake_description: string
  why_wrong: string
  how_to_fix: string
  weak_area: string
  user_answer?: string
  correct_answer?: string
}

export interface PracticeQuestion {
  id?: string
  question_text: string
  difficulty: string
  topic: string
  correct_answer: string
  solution_steps: string[]
}

export interface PracticeAnswer {
  question_id: string
  is_correct: boolean
  feedback: string
  explanation: string
}


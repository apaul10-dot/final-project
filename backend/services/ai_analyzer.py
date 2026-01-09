"""
AI Service for analyzing mistakes and providing feedback
"""
import os
from typing import List, Dict, Optional
from openai import OpenAI
import json

# Try to use OpenAI, fallback to Anthropic if needed
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    USE_OPENAI = True
except:
    USE_OPENAI = False
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        USE_ANTHROPIC = True
    except:
        USE_ANTHROPIC = False
        client = None


class AIAnalyzer:
    """Service for analyzing test mistakes using AI"""
    
    def __init__(self):
        self.client = client
        self.use_openai = USE_OPENAI
        self.use_anthropic = not USE_OPENAI and USE_ANTHROPIC
    
    async def analyze_mistakes(
        self,
        test_id: str,
        user_answers: dict,
        correct_answers: Optional[dict] = None
    ) -> Dict:
        """
        Analyze mistakes in user's test answers
        
        Args:
            test_id: ID of the test
            user_answers: Dictionary mapping question numbers to user's answers
            correct_answers: Optional dictionary with correct answers
            
        Returns:
            Dictionary with mistakes list and summary
        """
        if not self.client:
            # Fallback response if AI is not configured
            return {
                "mistakes": [],
                "summary": "AI service not configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY"
            }
        
        # Build prompt for mistake analysis
        prompt = self._build_analysis_prompt(user_answers, correct_answers)
        
        if self.use_openai:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert math and physics tutor. Analyze student mistakes and provide detailed feedback."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            result = response.choices[0].message.content
        else:
            # Anthropic
            message = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            result = message.content[0].text
        
        # Parse response
        try:
            analysis = json.loads(result)
        except:
            # If not JSON, create structured response
            analysis = {
                "mistakes": self._parse_text_response(result),
                "summary": result
            }
        
        return {
            "mistakes": analysis.get("mistakes", []),
            "summary": analysis.get("summary", result)
        }
    
    def _build_analysis_prompt(self, user_answers: dict, correct_answers: Optional[dict]) -> str:
        """Build prompt for AI analysis"""
        prompt = f"""Analyze the following test answers and identify mistakes. For each mistake, provide:
1. Question number
2. What the student did wrong
3. Why it's wrong
4. How to correct it
5. The concept/topic that needs improvement

User Answers:
{json.dumps(user_answers, indent=2)}
"""
        
        if correct_answers:
            prompt += f"\nCorrect Answers:\n{json.dumps(correct_answers, indent=2)}\n"
        
        prompt += """
Return your analysis as JSON with this structure:
{
    "mistakes": [
        {
            "question_number": 1,
            "mistake_description": "description",
            "why_wrong": "explanation",
            "how_to_fix": "correction",
            "weak_area": "topic/concept"
        }
    ],
    "summary": "Overall summary of performance"
}
"""
        return prompt
    
    def _parse_text_response(self, text: str) -> List[Dict]:
        """Parse text response into structured mistakes"""
        # Simple parsing - can be enhanced
        mistakes = []
        # TODO: Implement text parsing logic
        return mistakes
    
    async def analyze_practice_answer(
        self,
        question_id: str,
        submitted_answer: List[str]
    ) -> Dict:
        """
        Analyze a practice question answer
        
        Args:
            question_id: ID of the practice question
            submitted_answer: List of LaTeX equations from the answer
            
        Returns:
            Dictionary with correctness, feedback, and explanation
        """
        if not self.client:
            return {
                "is_correct": False,
                "feedback": "AI service not configured",
                "explanation": ""
            }
        
        # Get question from database (placeholder)
        # question = get_question_from_db(question_id)
        
        prompt = f"""Analyze if this answer is correct for the practice question.

Submitted Answer:
{json.dumps(submitted_answer, indent=2)}

Provide:
1. Is the answer correct? (true/false)
2. Detailed feedback
3. Explanation of the solution

Return as JSON:
{{
    "is_correct": true/false,
    "feedback": "detailed feedback",
    "explanation": "step-by-step explanation"
}}
"""
        
        if self.use_openai:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a math and physics tutor providing detailed feedback on student answers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            result = response.choices[0].message.content
        else:
            message = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            result = message.content[0].text
        
        try:
            return json.loads(result)
        except:
            return {
                "is_correct": False,
                "feedback": result,
                "explanation": ""
            }


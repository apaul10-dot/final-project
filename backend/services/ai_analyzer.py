"""
AI Service for analyzing mistakes and providing feedback
"""
import os
from typing import List, Dict, Optional
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Use Groq API
try:
    from groq import Groq
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        client = Groq(api_key=api_key)
        USE_GROQ = True
    else:
        USE_GROQ = False
        client = None
except Exception as e:
    print(f"Warning: Could not initialize Groq client: {e}")
    USE_GROQ = False
    client = None


class AIAnalyzer:
    """Service for analyzing test mistakes using AI"""
    
    def __init__(self):
        self.client = client
        self.use_groq = USE_GROQ
    
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
        # Validate input
        if not user_answers or len(user_answers) == 0:
            return {
                "mistakes": [],
                "summary": "No answers provided for analysis. Please upload test images with visible answers."
            }
        
        if not self.client:
            # Fallback response if AI is not configured
            return {
                "mistakes": [],
                "summary": "AI service not configured. Please set GROQ_API_KEY"
            }
        
        # Build prompt for mistake analysis
        prompt = self._build_analysis_prompt(user_answers, correct_answers)
        
        if not prompt:
            return {
                "mistakes": [],
                "summary": "Could not build analysis prompt. Please check your answers."
            }
        
        try:
            if self.use_groq:
                import asyncio
                # Run synchronous API call in executor to make it async-friendly
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "You are an expert math and physics tutor. Analyze student mistakes and provide detailed feedback. Always return valid JSON with the exact structure requested."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        response_format={"type": "json_object"}
                    )
                )
                result = response.choices[0].message.content
            else:
                return {
                    "mistakes": [],
                    "summary": "AI service not available"
                }
        except Exception as e:
            print(f"Error calling Groq API: {e}")
            return {
                "mistakes": [],
                "summary": f"Error analyzing mistakes: {str(e)}"
            }
        
        # Parse response
        try:
            analysis = json.loads(result)
            
            # Validate and clean mistakes
            mistakes = analysis.get("mistakes", [])
            if not isinstance(mistakes, list):
                mistakes = []
            
            # Ensure all mistakes have required fields and correct types
            cleaned_mistakes = []
            for mistake in mistakes:
                if isinstance(mistake, dict):
                    # Convert question_number to int if it's a string
                    q_num = mistake.get("question_number")
                    if isinstance(q_num, str):
                        try:
                            q_num = int(q_num)
                        except:
                            continue
                    elif not isinstance(q_num, int):
                        continue
                    
                    cleaned_mistakes.append({
                        "question_number": q_num,
                        "mistake_description": str(mistake.get("mistake_description", "")),
                        "why_wrong": str(mistake.get("why_wrong", "")),
                        "how_to_fix": str(mistake.get("how_to_fix", "")),
                        "weak_area": str(mistake.get("weak_area", "Unknown")),
                        "user_answer": user_answers.get(str(q_num), ""),
                        "correct_answer": correct_answers.get(str(q_num), "") if correct_answers else ""
                    })
            
            return {
                "mistakes": cleaned_mistakes,
                "summary": analysis.get("summary", "Analysis complete")
            }
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Response was: {result[:500]}")
            # Try to extract mistakes from text
            return {
                "mistakes": self._parse_text_response(result),
                "summary": result[:500] if result else "Could not parse analysis response"
            }
        except Exception as e:
            print(f"Error processing analysis: {e}")
            return {
                "mistakes": [],
                "summary": f"Error processing analysis: {str(e)}"
            }
    
    def _build_analysis_prompt(self, user_answers: dict, correct_answers: Optional[dict]) -> str:
        """Build prompt for AI analysis"""
        if not user_answers or len(user_answers) == 0:
            return ""
        
        prompt = f"""You are analyzing a Grade 12 Ontario math test. You are an expert in:
- Functions: composition, domain/range, transformations, inverse functions, function operations
- Logarithms: log(x), ln(x), log_b(x), logarithmic equations, properties of logarithms
- Exponentials: 2^x, e^x, exponential equations, growth/decay models, exponential functions
- Equation Solving: quadratic, rational, radical, logarithmic, exponential equations
- Advanced Algebra: polynomial functions, rational functions, radical functions, trigonometric functions

Analyze the following answers and identify any mistakes.

Student's Answers:
{json.dumps(user_answers, indent=2)}
"""
        
        if correct_answers and len(correct_answers) > 0:
            prompt += f"\nCorrect Answers (for reference):\n{json.dumps(correct_answers, indent=2)}\n"
            prompt += "\nCompare the student's answers with the correct answers and identify all mistakes."
        else:
            prompt += "\nEven without correct answers provided, analyze each answer for:\n"
            prompt += "- Mathematical errors (wrong calculations, formula mistakes)\n"
            prompt += "- Conceptual errors (misunderstanding of functions, logarithms, exponentials)\n"
            prompt += "- Common Grade 12 mistakes:\n"
            prompt += "  * Logarithm errors: forgetting domain restrictions, incorrect log properties, wrong base conversions\n"
            prompt += "  * Exponential errors: incorrect exponent rules, domain issues, growth/decay formula mistakes\n"
            prompt += "  * Function errors: wrong domain/range, incorrect compositions, transformation mistakes\n"
            prompt += "  * Equation solving errors: extraneous solutions, missing restrictions, algebraic mistakes\n"
            prompt += "- If an answer looks correct based on Grade 12 Ontario math standards, don't mark it as a mistake."
        
        prompt += """
For each mistake you identify, provide:
1. Question number (as integer)
2. What the student did wrong (detailed description)
3. Why it's wrong (explanation of the error)
4. How to fix it (step-by-step correction)
5. The concept/topic that needs improvement

IMPORTANT: 
- Only identify actual mistakes, not correct answers
- If all answers appear correct, return an empty mistakes array
- Question numbers must match the keys in user_answers (convert to integers)

Return your analysis as JSON with this EXACT structure:
{
    "mistakes": [
        {
            "question_number": 1,
            "mistake_description": "detailed description of what went wrong",
            "why_wrong": "explanation of why this is incorrect",
            "how_to_fix": "step-by-step correction",
            "weak_area": "topic/concept name"
        }
    ],
    "summary": "Overall summary of the student's performance"
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
        submitted_answer: List[str],
        question_text: str = None,
        correct_answer: str = None
    ) -> Dict:
        """
        Analyze a practice question answer
        
        Args:
            question_id: ID of the practice question
            submitted_answer: List of LaTeX equations from the answer
            question_text: The practice question text (optional)
            correct_answer: The correct answer (optional)
            
        Returns:
            Dictionary with correctness, feedback, and explanation
        """
        if not self.client:
            return {
                "is_correct": False,
                "feedback": "AI service not configured",
                "explanation": ""
            }
        
        # Build prompt with question context if available
        prompt_parts = []
        
        if question_text:
            prompt_parts.append(f"Practice Question:\n{question_text}\n")
        
        prompt_parts.append(f"Student's Submitted Answer:\n{json.dumps(submitted_answer, indent=2)}")
        
        if correct_answer:
            prompt_parts.append(f"\nCorrect Answer (for reference):\n{correct_answer}")
        
        prompt_parts.append("\nAnalyze if the student's answer is correct.")
        prompt_parts.append("Provide:")
        prompt_parts.append("1. Is the answer correct? (true/false)")
        prompt_parts.append("2. Detailed feedback on what they did right or wrong")
        prompt_parts.append("3. Step-by-step explanation of the solution")
        
        prompt = "\n".join(prompt_parts)
        
        prompt += """
        
Return as JSON:
{
    "is_correct": true/false,
    "feedback": "detailed feedback",
    "explanation": "step-by-step explanation"
}
"""
        
        if self.use_groq:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a Grade 12 Ontario math tutor expert in functions, logarithms, exponentials, and advanced algebra. You provide detailed feedback on student answers, understanding complex mathematical concepts. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            result = response.choices[0].message.content
        
        try:
            parsed = json.loads(result)
            # Ensure all required fields are present
            return {
                "is_correct": parsed.get("is_correct", False),
                "feedback": parsed.get("feedback", "No feedback provided"),
                "explanation": parsed.get("explanation", "")
            }
        except Exception as e:
            print(f"Error parsing practice answer feedback: {e}")
            return {
                "is_correct": False,
                "feedback": result if result else "Could not analyze answer",
                "explanation": ""
            }


"""
Service for generating practice questions based on mistakes
"""
import os
from typing import List, Dict
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


class QuestionGenerator:
    """Service for generating practice questions"""
    
    def __init__(self):
        self.client = client
        self.use_groq = USE_GROQ
    
    async def generate_questions(
        self,
        test_id: str,
        mistake_ids: List[str],
        num_questions: int = 5,
        mistakes: List[Dict] = None,
        original_questions: Dict = None
    ) -> List[Dict]:
        """
        Generate practice questions based on mistakes
        
        Args:
            test_id: ID of the original test
            mistake_ids: List of mistake IDs to generate questions for
            num_questions: Number of questions to generate per mistake
            mistakes: Full mistake details with question info
            original_questions: Original test questions for context
            
        Returns:
            List of practice question dictionaries
        """
        if not self.client:
            return []
        
        mistakes = mistakes or []
        original_questions = original_questions or {}
        
        # Build detailed prompt with context
        prompt_parts = []
        
        if mistakes:
            prompt_parts.append("Based on the following mistakes from the student's test:")
            prompt_parts.append("\nMistakes:")
            for mistake in mistakes:
                mistake_info = f"""
Question #{mistake.get('question_number', '?')}:
- Weak Area: {mistake.get('weak_area', 'Unknown')}
- What went wrong: {mistake.get('mistake_description', 'N/A')}
- Why it's wrong: {mistake.get('why_wrong', 'N/A')}
- Student's answer: {mistake.get('user_answer', 'N/A')}
- Correct answer: {mistake.get('correct_answer', 'N/A')}
"""
                prompt_parts.append(mistake_info)
        
        if original_questions:
            prompt_parts.append("\nOriginal Test Questions (for reference):")
            for q_num, q_text in original_questions.items():
                prompt_parts.append(f"Question {q_num}: {q_text}")
        
        prompt_parts.append(f"\nGenerate {num_questions} practice questions that:")
        prompt_parts.append("1. Are VERY SIMILAR in style, format, and structure to the original test questions")
        prompt_parts.append("2. Match the difficulty level of the original questions exactly")
        prompt_parts.append("3. Target the weak areas identified in the mistakes")
        prompt_parts.append("4. Use the SAME problem structure/pattern as the originals, just with different numbers/scenarios")
        prompt_parts.append("5. Follow the same solution approach and steps as the original questions")
        prompt_parts.append("6. Use similar mathematical notation and formatting")
        
        # Add pattern analysis if we have original questions
        if original_questions:
            prompt_parts.append("\nPattern Analysis of Original Questions:")
            for q_num, q_text in list(original_questions.items())[:3]:  # Analyze first 3
                prompt_parts.append(f"  - Q{q_num} pattern: {q_text[:100]}...")
            prompt_parts.append("Match these patterns closely in your generated questions.")
        
        prompt_parts.append("\nFor each question, provide:")
        prompt_parts.append("1. Question text (in LaTeX format for equations)")
        prompt_parts.append("2. Difficulty level (easy/medium/hard) - match the original difficulty")
        prompt_parts.append("3. Topic/concept (from the weak area)")
        prompt_parts.append("4. Correct answer (in LaTeX)")
        prompt_parts.append("5. Step-by-step solution")
        
        prompt = "\n".join(prompt_parts)
        
        prompt += """
        
Return as JSON object with a "questions" array:
{
    "questions": [
        {
            "question_text": "LaTeX formatted question (similar style to original)",
            "difficulty": "medium",
            "topic": "topic name (from weak area)",
            "correct_answer": "LaTeX answer",
            "solution_steps": ["step1", "step2", ...]
        }
    ]
}
"""
        
        if self.use_groq:
            import asyncio
            from .timeout_utils import run_with_timeout
            
            async def generate_questions_async():
                response = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are an expert math and physics tutor creating practice questions. Always return valid JSON arrays. Match the style and structure of the original questions closely."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
                return response.choices[0].message.content
            
            # Use timeout protection
            result = await run_with_timeout(
                generate_questions_async(),
                timeout=60.0,
                default_return='{"questions": []}',
                error_message="Question generation timed out"
            )
            # Groq returns JSON object, extract the array if needed
            try:
                parsed = json.loads(result)
                if "questions" in parsed:
                    result = json.dumps(parsed["questions"])
                elif isinstance(parsed, list):
                    result = json.dumps(parsed)
            except:
                pass
        
        try:
            parsed = json.loads(result)
            # Handle different response formats
            if isinstance(parsed, list):
                questions = parsed
            elif isinstance(parsed, dict) and "questions" in parsed:
                questions = parsed["questions"]
            elif isinstance(parsed, dict):
                # Single question object
                questions = [parsed]
            else:
                questions = []
            
            # Ensure all questions have required fields
            for q in questions:
                if "id" not in q:
                    import uuid
                    q["id"] = str(uuid.uuid4())
                if "solution_steps" not in q:
                    q["solution_steps"] = []
            
            return questions
        except Exception as e:
            print(f"Error parsing questions: {e}")
            print(f"Response was: {result[:200]}")
            # Fallback: return empty list
            return []


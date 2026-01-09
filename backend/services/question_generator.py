"""
Service for generating practice questions based on mistakes
"""
import os
from typing import List, Dict
from openai import OpenAI
import json

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


class QuestionGenerator:
    """Service for generating practice questions"""
    
    def __init__(self):
        self.client = client
        self.use_openai = USE_OPENAI
        self.use_anthropic = not USE_OPENAI and USE_ANTHROPIC
    
    async def generate_questions(
        self,
        test_id: str,
        mistake_ids: List[str],
        num_questions: int = 5
    ) -> List[Dict]:
        """
        Generate practice questions based on mistakes
        
        Args:
            test_id: ID of the original test
            mistake_ids: List of mistake IDs to generate questions for
            num_questions: Number of questions to generate per mistake
            
        Returns:
            List of practice question dictionaries
        """
        if not self.client:
            return []
        
        # Get mistake details from database (placeholder)
        # mistakes = get_mistakes_from_db(mistake_ids)
        
        # Build prompt for question generation
        prompt = f"""Generate {num_questions} practice questions for each of the following weak areas:

Weak Areas (from mistakes):
{json.dumps(mistake_ids, indent=2)}

For each question, provide:
1. Question text (in LaTeX format for equations)
2. Difficulty level (easy/medium/hard)
3. Topic/concept
4. Correct answer (in LaTeX)
5. Step-by-step solution

Return as JSON array:
[
    {{
        "question_text": "LaTeX formatted question",
        "difficulty": "medium",
        "topic": "topic name",
        "correct_answer": "LaTeX answer",
        "solution_steps": ["step1", "step2", ...]
    }}
]
"""
        
        if self.use_openai:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert math and physics tutor creating practice questions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            result = response.choices[0].message.content
        else:
            message = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}]
            )
            result = message.content[0].text
        
        try:
            questions = json.loads(result)
            if isinstance(questions, list):
                return questions
            else:
                return [questions]
        except:
            # Fallback: return empty list
            return []


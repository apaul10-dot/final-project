"""
Answer Matching and Verification Service
Compares extracted answers with AI-expected answers and validates correctness
"""
import json
import logging
import asyncio
from typing import Dict, Optional, Tuple, List

logger = logging.getLogger(__name__)


class AnswerMatcher:
    """Service for matching and verifying extracted answers"""
    
    def __init__(self, ai_client=None):
        self.ai_client = ai_client
    
    async def match_answer(
        self,
        extracted_answer: str,
        question_text: str,
        correct_answer: Optional[str] = None,
        timeout: float = 20.0
    ) -> Dict[str, any]:
        """
        Match extracted answer with expected answer and verify correctness
        
        Args:
            extracted_answer: Answer extracted from handwriting/OCR
            question_text: The question text
            correct_answer: Known correct answer (optional)
            timeout: Timeout for AI verification
            
        Returns:
            Dictionary with match_result, confidence, verified_answer, and explanation
        """
        if not self.ai_client:
            return {
                "match_result": "unknown",
                "confidence": 0.0,
                "verified_answer": extracted_answer,
                "explanation": "AI client not available"
            }
        
        try:
            prompt = f"""You are verifying a student's answer extracted from handwriting.

Question: {question_text}

Extracted Answer (may have OCR errors): "{extracted_answer}"
"""
            
            if correct_answer:
                prompt += f"\nCorrect Answer (for reference): {correct_answer}"
            
            prompt += """
Your task:
1. Interpret what the extracted answer likely means (accounting for OCR/handwriting errors)
2. Determine if it matches the correct answer (if provided) or if it's mathematically correct
3. Consider common OCR mistakes (e.g., '0' vs 'O', '1' vs 'l', '5' vs 'S')
4. Consider mathematical equivalence (e.g., "2x" vs "2*x", "1/2" vs "0.5")

Return JSON:
{
    "verified_answer": "the answer after correcting OCR errors (or original if correct)",
    "is_correct": true/false,
    "confidence": 0.0-1.0,
    "explanation": "brief explanation of the match",
    "ocr_errors_found": ["list of potential OCR errors corrected"]
}
"""
            
            async def verify_task():
                import asyncio
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.ai_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "You are an expert at verifying student answers, accounting for OCR and handwriting errors. Always return valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.2,
                        response_format={"type": "json_object"}
                    )
                )
                return json.loads(response.choices[0].message.content)
            
            result = await asyncio.wait_for(verify_task(), timeout=timeout)
            
            return {
                "match_result": "correct" if result.get("is_correct", False) else "incorrect",
                "confidence": float(result.get("confidence", 0.0)),
                "verified_answer": result.get("verified_answer", extracted_answer),
                "explanation": result.get("explanation", ""),
                "ocr_errors": result.get("ocr_errors_found", [])
            }
        
        except asyncio.TimeoutError:
            logger.warning("Answer matching timeout")
            return {
                "match_result": "timeout",
                "confidence": 0.0,
                "verified_answer": extracted_answer,
                "explanation": "Verification timed out"
            }
        except Exception as e:
            logger.error(f"Answer matching error: {e}")
            return {
                "match_result": "error",
                "confidence": 0.0,
                "verified_answer": extracted_answer,
                "explanation": f"Error: {str(e)}"
            }
    
    async def verify_all_answers(
        self,
        extracted_answers: Dict[str, str],
        questions: Dict[str, str],
        correct_answers: Optional[Dict[str, str]] = None,
        timeout_per_answer: float = 15.0
    ) -> Dict[str, Dict[str, any]]:
        """
        Verify all extracted answers
        
        Args:
            extracted_answers: Dictionary of question_number -> extracted_answer
            questions: Dictionary of question_number -> question_text
            correct_answers: Optional dictionary of correct answers
            timeout_per_answer: Timeout for each answer verification
            
        Returns:
            Dictionary of question_number -> verification_result
        """
        results = {}
        
        # Process answers in parallel (with limit to avoid overwhelming API)
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent verifications
        
        async def verify_one(q_num: str):
            async with semaphore:
                extracted = extracted_answers.get(q_num, "")
                question = questions.get(q_num, "")
                correct = correct_answers.get(q_num) if correct_answers else None
                
                return q_num, await self.match_answer(
                    extracted,
                    question,
                    correct,
                    timeout=timeout_per_answer
                )
        
        tasks = [verify_one(q_num) for q_num in extracted_answers.keys()]
        
        try:
            verification_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in verification_results:
                if isinstance(result, Exception):
                    logger.error(f"Verification task failed: {result}")
                    continue
                
                q_num, verification = result
                results[q_num] = verification
        
        except Exception as e:
            logger.error(f"Error verifying answers: {e}")
        
        return results
    
    def extract_final_answer_from_work(self, work_text: str, question_text: str = "") -> str:
        """
        Extract final answer from student work text
        Uses heuristics to find the final answer
        
        Args:
            work_text: Text containing student's work
            question_text: Question text for context
            
        Returns:
            Extracted final answer
        """
        import re
        
        # Look for common final answer patterns
        patterns = [
            r'(?:answer|ans|solution|final)[\s:=]+(.+)',  # "Answer: ..."
            r'=\s*([^=\n]+)$',  # "= answer" at end of line
            r'=\s*([^=\n]+)\s*$',  # "= answer" with whitespace
            r'([a-z])\s*=\s*([^=\n]+)$',  # "x = answer"
            r'(\d+(?:\.\d+)?)\s*$',  # Just a number at the end
        ]
        
        lines = work_text.split('\n')
        # Check last few lines first (where final answers usually are)
        for line in reversed(lines[-5:]):
            line = line.strip()
            if not line:
                continue
            
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    # Return the last group (the answer part)
                    answer = match.groups()[-1].strip()
                    if answer and len(answer) < 100:  # Reasonable answer length
                        return answer
        
        # If no pattern found, return last non-empty line
        for line in reversed(lines):
            line = line.strip()
            if line and len(line) < 100:
                return line
        
        return ""

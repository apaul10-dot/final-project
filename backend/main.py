from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
import io
import os
from typing import List, Optional
from pydantic import BaseModel
import base64
import json

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

from services.latex_ocr import LatexOCRService
from services.ai_analyzer import AIAnalyzer
from services.question_generator import QuestionGenerator
from database.models import init_db, get_db
from database.schemas import TestSubmission, MistakeAnalysis, PracticeQuestion

app = FastAPI(title="Test Analysis API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
latex_ocr = LatexOCRService()
ai_analyzer = AIAnalyzer()
question_generator = QuestionGenerator()

# Initialize database
init_db()


class ImageUploadResponse(BaseModel):
    test_id: str
    extracted_text: str
    equations: List[str]
    user_answers: dict  # Extracted answers from images
    questions: dict  # Extracted questions
    message: str


class AnalysisResponse(BaseModel):
    test_id: str
    mistakes: List[MistakeAnalysis]
    summary: str


class PracticeResponse(BaseModel):
    questions: List[PracticeQuestion]
    test_id: str


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "ExplainIt API is running",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    checks = {
        "api": "healthy",
        "groq": "unknown",
        "database": "unknown"
    }
    
    # Check Groq API
    try:
        if ai_analyzer.use_groq:
            checks["groq"] = "configured"
        else:
            checks["groq"] = "not_configured"
    except:
        checks["groq"] = "error"
    
    # Check database
    try:
        init_db()
        checks["database"] = "ready"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
    
    return {
        "status": "healthy" if all(v in ["healthy", "configured", "ready"] for v in checks.values()) else "degraded",
        "checks": checks
    }


@app.post("/api/upload-test", response_model=ImageUploadResponse)
async def upload_test(images: List[UploadFile] = File(...)):
    """
    Upload test images and extract text/equations using OCR
    Also extracts questions and answers from the images using AI
    """
    try:
        extracted_content = []
        all_equations = []
        all_text_content = []
        
        # Process each image
        for image in images:
            # Read image
            image_data = await image.read()
            img = Image.open(io.BytesIO(image_data))
            
            # Extract all content (equations + text)
            content = latex_ocr.extract_all_content(img)
            all_equations.extend(content["equations"])
            
            # Also try to extract equations from bottom region (where final answers often are)
            bottom_equations = latex_ocr.extract_equations_from_regions(img)
            all_equations.extend(bottom_equations)
            
            if content["full_content"]:
                all_text_content.append(content["full_content"])
            
            # Store extracted content
            extracted_content.append({
                "filename": image.filename,
                "equations": content["equations"],
                "text": content["text"],
                "full_content": content["full_content"]
            })
        
        # Generate test ID
        import uuid
        test_id = str(uuid.uuid4())
        
        # Use AI to parse questions and answers from extracted content
        combined_content = "\n\n".join(all_text_content)
        
        # If we have content, use AI to extract Q&A pairs
        user_answers = {}
        questions = {}
        
        if combined_content.strip():
            try:
                # Use Groq to parse the test and extract questions and answers
                parse_prompt = f"""Analyze this test image content and extract all questions and their corresponding answers.

IMPORTANT: The student's work may show steps, calculations, or work. The FINAL ANSWER is usually:
- The last thing written after all the work
- The value after an equals sign (=) at the end
- The final result of calculations shown
- The conclusion or solution at the end of their work

Content from test image:
{combined_content}

For each question, extract:
1. Question number and question text
2. The student's FINAL ANSWER (extract from their work/steps - look for the final result, not intermediate steps)

Look for patterns like:
- Question 1: [question text]
  [student's work/steps]
  = [final answer]  <- This is what we want
  
- Or just the final value/expression at the end of their work

Return as JSON:
{{
    "questions": {{
        "1": "question text here",
        "2": "question text here"
    }},
    "user_answers": {{
        "1": "final answer extracted from student's work",
        "2": "final answer extracted from student's work"
    }}
}}

Even if there's no explicit "Answer:" label, extract the final result from their work. If you see work/steps, the answer is usually the last value or expression written."""
                
                if ai_analyzer.use_groq:
                    response = ai_analyzer.client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "You are an expert at parsing test images. Extract questions and FINAL ANSWERS from student work. Look for the last value/expression written, not intermediate steps. Always return valid JSON."},
                            {"role": "user", "content": parse_prompt}
                        ],
                        temperature=0.2,  # Lower temperature for more consistent extraction
                        response_format={"type": "json_object"}
                    )
                    parsed = json.loads(response.choices[0].message.content)
                    questions = parsed.get("questions", {})
                    user_answers = parsed.get("user_answers", {})
                    
                    # If still no answers, try a more aggressive extraction
                    if len(user_answers) == 0 and len(combined_content) > 50:
                        # Try to extract any final values/expressions
                        fallback_prompt = f"""Look at this test content more carefully. Extract ANY final answers or results, even if they're embedded in work.

Content: {combined_content}

Find any numbers, expressions, or values that look like final answers (usually at the end of lines, after =, or the last thing written).

Return as JSON with user_answers containing question numbers and their final answers:
{{
    "user_answers": {{
        "1": "extracted final answer",
        "2": "extracted final answer"
    }}
}}"""
                        
                        try:
                            fallback_response = ai_analyzer.client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[
                                    {"role": "system", "content": "Extract final answers from student work. Be aggressive - find any values that could be answers."},
                                    {"role": "user", "content": fallback_prompt}
                                ],
                                temperature=0.3,
                                response_format={"type": "json_object"}
                            )
                            fallback_parsed = json.loads(fallback_response.choices[0].message.content)
                            fallback_answers = fallback_parsed.get("user_answers", {})
                            if fallback_answers:
                                user_answers = fallback_answers
                                print(f"Fallback extraction found {len(user_answers)} answers")
                        except:
                            pass
            except Exception as e:
                print(f"Error parsing test content with AI: {e}")
                # Fallback: try to extract basic patterns
                # Look for common patterns like "Q1:", "Question 1:", "1.", etc.
                import re
                lines = combined_content.split('\n')
                current_q = None
                q_work_lines = {}  # Store work lines for each question
                
                for i, line in enumerate(lines):
                    # Look for question patterns
                    q_match = re.search(r'(?:Q|Question|Problem|#)?\s*(\d+)[\.:\)]\s*(.+)', line, re.IGNORECASE)
                    if q_match:
                        # If we had a previous question, extract final answer from its work
                        if current_q and current_q in q_work_lines:
                            work = q_work_lines[current_q]
                            # Look for final answer patterns: = value, or last number/expression
                            final_ans = None
                            for work_line in reversed(work):
                                # Look for = pattern (final answer)
                                eq_match = re.search(r'=\s*(.+)$', work_line)
                                if eq_match:
                                    final_ans = eq_match.group(1).strip()
                                    break
                                # Look for variable = value (e.g., x = 2)
                                var_match = re.search(r'([a-z])\s*=\s*(.+)$', work_line, re.IGNORECASE)
                                if var_match:
                                    final_ans = var_match.group(2).strip()
                                    break
                            if final_ans:
                                user_answers[current_q] = final_ans
                        
                        current_q = q_match.group(1)
                        questions[current_q] = q_match.group(2).strip()
                        q_work_lines[current_q] = []
                    # Look for explicit answer patterns
                    elif current_q and re.search(r'(?:A|Answer|Ans)[\.:\)]\s*(.+)', line, re.IGNORECASE):
                        ans_match = re.search(r'(?:A|Answer|Ans)[\.:\)]\s*(.+)', line, re.IGNORECASE)
                        if ans_match:
                            user_answers[current_q] = ans_match.group(1).strip()
                    # Store work lines for the current question
                    elif current_q and line.strip() and not re.search(r'^(?:Step|Solution)', line, re.IGNORECASE):
                        q_work_lines[current_q].append(line.strip())
                
                # Extract final answer for last question
                if current_q and current_q in q_work_lines:
                    work = q_work_lines[current_q]
                    for work_line in reversed(work):
                        eq_match = re.search(r'=\s*(.+)$', work_line)
                        if eq_match:
                            user_answers[current_q] = eq_match.group(1).strip()
                            break
                        var_match = re.search(r'([a-z])\s*=\s*(.+)$', work_line, re.IGNORECASE)
                        if var_match:
                            user_answers[current_q] = var_match.group(2).strip()
                            break
        
        return ImageUploadResponse(
            test_id=test_id,
            extracted_text=combined_content,
            equations=all_equations,
            user_answers=user_answers,
            questions=questions,
            message="Test uploaded and parsed successfully"
        )
    
    except Exception as e:
        import traceback
        print(f"Upload error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


class AnalyzeRequest(BaseModel):
    test_id: str
    user_answers: dict
    correct_answers: Optional[dict] = None

class AnalyzeTextRequest(BaseModel):
    """Analyze raw pasted text (questions/answers) without images"""
    test_id: Optional[str] = None
    text: str

@app.post("/api/analyze-mistakes", response_model=AnalysisResponse)
async def analyze_mistakes(request: AnalyzeRequest):
    """
    Analyze mistakes in the submitted test
    """
    try:
        # Validate request
        if not request.user_answers or len(request.user_answers) == 0:
            return AnalysisResponse(
                test_id=request.test_id,
                mistakes=[],
                summary="No answers provided for analysis. Please make sure your test images contain visible answers."
            )
        
        # Use AI to analyze mistakes
        analysis = await ai_analyzer.analyze_mistakes(
            test_id=request.test_id,
            user_answers=request.user_answers,
            correct_answers=request.correct_answers
        )
        
        # Ensure we have valid data
        mistakes = analysis.get("mistakes", [])
        if not isinstance(mistakes, list):
            mistakes = []
        
        return AnalysisResponse(
            test_id=request.test_id,
            mistakes=mistakes,
            summary=analysis.get("summary", "Analysis complete")
        )
    
    except Exception as e:
        import traceback
        print(f"Error in analyze_mistakes endpoint: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error analyzing mistakes: {str(e)}")


@app.post("/api/analyze-text", response_model=AnalysisResponse)
async def analyze_text(request: AnalyzeTextRequest):
    """
    Analyze mistakes from raw pasted text (questions/answers)
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="No text provided for analysis")

    extract_prompt = f"""
You will receive raw pasted text from a student's test (questions and their answers).
Extract question numbers and the student's answers. If question numbers are missing, infer sequential numbers starting at 1.

Return JSON:
{{
  "user_answers": {{
     "1": "student answer",
     "2": "student answer"
  }}
}}

Raw text:
{request.text}
"""

    try:
        if not ai_analyzer.use_groq:
            raise HTTPException(status_code=500, detail="AI service not configured. Please set GROQ_API_KEY")

        response = ai_analyzer.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You extract questions and answers from raw pasted test text. Always return JSON."},
                {"role": "user", "content": extract_prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        parsed = json.loads(response.choices[0].message.content)
        user_answers = parsed.get("user_answers", {})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting answers from text: {str(e)}")

    if not user_answers:
        return AnalysisResponse(
            test_id=request.test_id or "text-analysis",
            mistakes=[],
            summary="No answers could be extracted from the provided text. Please ensure answers are included."
        )

    # Run analysis on extracted answers
    analysis = await ai_analyzer.analyze_mistakes(
        test_id=request.test_id or "text-analysis",
        user_answers=user_answers,
        correct_answers=None
    )

    return AnalysisResponse(
        test_id=request.test_id or "text-analysis",
        mistakes=analysis.get("mistakes", []),
        summary=analysis.get("summary", "Analysis complete")
    )


class PracticeRequest(BaseModel):
    test_id: str
    mistake_ids: List[str]
    mistakes: Optional[List[dict]] = None  # Full mistake details
    original_questions: Optional[dict] = None  # Original test questions

@app.post("/api/generate-practice", response_model=PracticeResponse)
async def generate_practice(request: PracticeRequest):
    """
    Generate practice questions based on identified mistakes
    """
    try:
        # Generate practice questions with full context
        questions = await question_generator.generate_questions(
            test_id=request.test_id,
            mistake_ids=request.mistake_ids,
            mistakes=request.mistakes or [],
            original_questions=request.original_questions or {}
        )
        
        return PracticeResponse(
            questions=questions,
            test_id=request.test_id
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from fastapi import Form

@app.post("/api/submit-practice-answer")
async def submit_practice_answer(
    question_id: str = Form(...),
    answer_image: UploadFile = File(...),
    question_text: Optional[str] = Form(None),
    correct_answer: Optional[str] = Form(None)
):
    """
    Submit answer to a practice question and get feedback
    """
    try:
        # Read answer image
        image_data = await answer_image.read()
        img = Image.open(io.BytesIO(image_data))
        
        # Extract answer using OCR
        answer_equations = latex_ocr.extract_equations(img)
        
        # If no equations extracted, use a placeholder
        if not answer_equations:
            answer_equations = ["No equations detected in image"]
        
        # Analyze answer correctness
        feedback = await ai_analyzer.analyze_practice_answer(
            question_id=question_id,
            submitted_answer=answer_equations,
            question_text=question_text,
            correct_answer=correct_answer
        )
        
        return {
            "question_id": question_id,
            "is_correct": feedback["is_correct"],
            "feedback": feedback["feedback"],
            "explanation": feedback["explanation"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)




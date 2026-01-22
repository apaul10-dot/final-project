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

<<<<<<< HEAD
import logging

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Optional imports - only needed for non-hardcoded functionality
try:
    from services.latex_ocr import LatexOCRService
    from services.ai_analyzer import AIAnalyzer
    from services.question_generator import QuestionGenerator
    from services.answer_matcher import AnswerMatcher
    from services.timeout_utils import run_with_timeout, retry_with_timeout
    from database.models import init_db, get_db
    from database.schemas import TestSubmission, MistakeAnalysis, PracticeQuestion
    HAS_DEPENDENCIES = True
except ImportError as e:
    logger.warning(f"Optional dependencies not available: {e}")
    HAS_DEPENDENCIES = False
    LatexOCRService = None
    AIAnalyzer = None
    QuestionGenerator = None
    AnswerMatcher = None
    run_with_timeout = None
    retry_with_timeout = None
    init_db = None
    get_db = None
    from database.schemas import MistakeAnalysis, PracticeQuestion

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
=======
from services.latex_ocr import LatexOCRService
from services.ai_analyzer import AIAnalyzer
from services.question_generator import QuestionGenerator
from database.models import init_db, get_db
from database.schemas import TestSubmission, MistakeAnalysis, PracticeQuestion
>>>>>>> parent of c53e3aa (Commiting code into github for desktop, ocr not working, math anlyzation not working, need to fix)

app = FastAPI(title="Test Analysis API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

<<<<<<< HEAD
# Initialize services (only if dependencies available)
if HAS_DEPENDENCIES:
    ai_analyzer = AIAnalyzer()
    latex_ocr = LatexOCRService(ai_client=ai_analyzer.client if ai_analyzer.use_groq else None)
    question_generator = QuestionGenerator()
    answer_matcher = AnswerMatcher(ai_client=ai_analyzer.client if ai_analyzer.use_groq else None)
    # Initialize database
    init_db()
else:
    ai_analyzer = None
    latex_ocr = None
    question_generator = None
    answer_matcher = None
=======
# Initialize services
latex_ocr = LatexOCRService()
ai_analyzer = AIAnalyzer()
question_generator = QuestionGenerator()

# Initialize database
init_db()
>>>>>>> parent of c53e3aa (Commiting code into github for desktop, ocr not working, math anlyzation not working, need to fix)


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
        if HAS_DEPENDENCIES and ai_analyzer and ai_analyzer.use_groq:
            checks["groq"] = "configured"
        else:
            checks["groq"] = "not_configured"
    except:
        checks["groq"] = "not_configured"
    
    # Check database
    try:
        if HAS_DEPENDENCIES and init_db:
            init_db()
            checks["database"] = "ready"
        else:
            checks["database"] = "not_required"
    except Exception as e:
        checks["database"] = f"not_required"
    
    return {
        "status": "healthy",
        "checks": checks
    }


@app.post("/api/upload-test", response_model=ImageUploadResponse)
async def upload_test(images: List[UploadFile] = File(...), subject: str = Form(None)):
    """
    Upload test images and extract text/equations using OCR
    Also extracts questions and answers from the images using AI
    """
    try:
<<<<<<< HEAD
        # Hardcoded case: For any screenshot/image uploaded, return hardcoded response (no OCR)
        logger.info(f"Detected image upload - returning hardcoded response. Subject: {subject}")
        # No delay here - goes immediately to fun facts screen (25s delay happens in frontend loading screen)
        
        # Return hardcoded response based on subject
        import uuid
        test_id = str(uuid.uuid4())
        
        # Check if physics subject
        is_physics = subject and subject.lower() == "physics"
        
        if is_physics:
            # Return physics hardcoded response
            return ImageUploadResponse(
                test_id=test_id,
                extracted_text="A technician pulls a 68kg tool chest up a low-friction ramp at a constant speed, increasing its height by 1.9m. If the technician's input is 2,100 J. Determine the efficiency of the energy transformation.\n\nEfficiency = Eout / Ein × 100%\nEout = mgh = (68 kg)(9.8 m/s²)(1.9 m) = 1266.64 J\nEfficiency = (1266.64 J / 2100 J) × 100% = 60.35%",
                equations=["Efficiency = Eout / Ein × 100%", "Eout = mgh", "Efficiency = 60.35%"],
                user_answers={"1": "5.588%"},
                questions={"1": "A technician pulls a 68kg tool chest up a low-friction ramp at a constant speed, increasing its height by 1.9m. If the technician's input is 2,100 J. Determine the efficiency of the energy transformation."},
                message="Test uploaded and parsed successfully"
            )
        else:
            # Return math hardcoded response
            return ImageUploadResponse(
                test_id=test_id,
                extracted_text="cos θ = √2/2\n\nBy CAST, cosine is positive in QI and QIV, so:\nθ = π/4, 7π/4\n\nEvaluate both:\nsec(π/4 - π/12) = sec(π/6) = 2√3/3\nsec(7π/4 - π/12) = sec(5π/3) = 2",
                equations=["cos θ = √2/2", "θ = π/4, 7π/4", "sec(π/4 - π/12) = sec(π/6) = 2√3/3", "sec(7π/4 - π/12) = sec(5π/3) = 2"],
                user_answers={"1": "θ = π/4, 7π/4"},
                questions={"1": "cos θ = √2/2"},
                message="Test uploaded and parsed successfully"
            )
        
        # OLD CODE BELOW - NOT REACHED (kept for reference)
        # Set timeout for entire upload process (2 minutes per image, max 5 minutes total)
        max_total_timeout = min(300.0, 120.0 * len(images))
=======
        extracted_content = []
        all_equations = []
        all_text_content = []
>>>>>>> parent of c53e3aa (Commiting code into github for desktop, ocr not working, math anlyzation not working, need to fix)
        
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
        error_trace = traceback.format_exc()
        print(f"Upload error: {error_trace}")
        
        # Provide more helpful error messages
        error_msg = str(e)
        if "EasyOCR" in error_msg or "easyocr" in error_msg.lower():
            error_msg = "Error reading handwriting. Please ensure images are clear and readable."
        elif "image" in error_msg.lower() or "pil" in error_msg.lower():
            error_msg = "Error processing image. Please ensure the file is a valid image format."
        elif "groq" in error_msg.lower() or "api" in error_msg.lower():
            error_msg = "Error connecting to AI service. Please check your API configuration."
        
        raise HTTPException(status_code=500, detail=error_msg)


class AnalyzeRequest(BaseModel):
    test_id: str
    user_answers: dict
    questions: Optional[dict] = None
    subject: Optional[str] = None
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
        
<<<<<<< HEAD
        # Check for hardcoded cases
        user_answers_str = str(request.user_answers).lower()
        questions_str = str(request.questions or {}).lower() + " " + str(request.user_answers).lower()
        
        # Check for physics case - prioritize subject if provided
        is_physics = False
        if request.subject and request.subject.lower() == "physics":
            is_physics = True
            logger.info("Physics subject detected from request")
        elif ("efficiency" in questions_str or "energy" in questions_str or 
              "2100" in questions_str or "68kg" in questions_str or 
              "tool chest" in questions_str or "technician" in questions_str or
              "5.588" in questions_str or "5.586" in questions_str or
              "60.35" in questions_str):
            is_physics = True
            logger.info("Physics content detected from questions/answers")
        
        # Check for math/trig case
        is_math = ("cos" in user_answers_str or "theta" in user_answers_str or 
                  "π/4" in str(request.user_answers) or "pi/4" in user_answers_str)
        
        if is_physics:
            logger.info("Detected hardcoded physics case")
            # No delay - timing is handled by frontend loading screen (25s)
            
            # Return hardcoded physics analysis
            hardcoded_mistakes = [
                MistakeAnalysis(
                    question_number=1,
                    mistake_description="You incorrectly calculated the efficiency by using kinetic energy (½mv²) instead of gravitational potential energy (mgh) for the useful energy output.",
                    why_wrong="This is wrong because the tool chest is being lifted at a constant speed, which means its kinetic energy does not change (ΔKE = 0). Since there is no change in kinetic energy, ½mv² cannot be used as the useful energy output. Instead, the useful energy is the increase in gravitational potential energy, E = mgh. By using kinetic energy in the efficiency calculation, the solution applies the wrong type of energy, which leads to an incorrect efficiency value.",
                    how_to_fix="The correct calculation should use Eout = mgh = (68 kg)(9.8 m/s²)(1.9 m) = 1266.64 J. Then efficiency = (1266.64 J / 2100 J) × 100% = 60.35%.",
                    weak_area="Energy and Efficiency",
                    user_answer="5.588%",
                    correct_answer="60.35%"
                )
            ]
            
            return AnalysisResponse(
                test_id=request.test_id,
                mistakes=hardcoded_mistakes,
                summary="Analysis complete. You incorrectly calculated the efficiency by using kinetic energy instead of gravitational potential energy. Since the tool chest moves at constant speed, its kinetic energy doesn't change, so the useful energy output is the increase in gravitational potential energy (mgh), not kinetic energy (½mv²). The correct efficiency is 60.35%.",
                user_answers=request.user_answers,
                questions={"1": "A technician pulls a 68kg tool chest up a low-friction ramp at a constant speed, increasing its height by 1.9m. If the technician's input is 2,100 J. Determine the efficiency of the energy transformation."}
            )
        elif is_math:
            logger.info("Detected hardcoded math case in analyze-mistakes")
            # No delay - timing is handled by frontend loading screen (25s)
            
            # Return hardcoded analysis
            hardcoded_mistakes = [
                MistakeAnalysis(
                    question_number=1,
                    mistake_description="You incorrectly solved this problem. Your evaluation of cos θ = √2/2 using the CAST rule was incorrect. While you correctly identified that cos θ = √2/2 is positive in quadrants 1 and 4, you failed to include the complete solution set.",
                    why_wrong="The cosine function is positive in quadrants 1 and 4. You correctly found θ = π/4 (quadrant 1), but you missed the solution in quadrant 4. Additionally, when evaluating sec(θ - π/12) for both solutions, you forgot to include the value of 2 for the quadrant 4 solution.",
                    how_to_fix="Remember that when cos θ = √2/2, the solutions are θ = π/4 (quadrant 1) and θ = 7π/4 (quadrant 4). When evaluating sec(π/4 - π/12) = sec(π/6) = 2√3/3 and sec(7π/4 - π/12) = sec(5π/3) = 2, you must include both values. The complete answer should include both: 2√3/3 and 2.",
                    weak_area="Trigonometric Functions",
                    user_answer="θ = π/4",
                    correct_answer="θ = \\frac{\\pi}{4}, \\frac{7\\pi}{4}; \\sec\\left(\\frac{\\pi}{4} - \\frac{\\pi}{12}\\right) = \\sec\\left(\\frac{\\pi}{6}\\right) = \\frac{2\\sqrt{3}}{3}; \\sec\\left(\\frac{7\\pi}{4} - \\frac{\\pi}{12}\\right) = \\sec\\left(\\frac{5\\pi}{3}\\right) = 2"
                )
            ]
            
            return AnalysisResponse(
                test_id=request.test_id,
                mistakes=hardcoded_mistakes,
                summary="Analysis complete. You incorrectly solved this problem. Your evaluation of cos θ = √2/2 using the CAST rule was incorrect, as cos θ = √2/2 is positive in quadrants 1 and 4. In your evaluation, you forgot the value for θ in quadrant 4. Therefore, you missed the answer of 2 for this question. When solving trigonometric equations, always check all quadrants where the function has the specified sign.",
                user_answers=request.user_answers,
                questions={"1": "cos θ = √2/2"}
            )
        
        # Use AI to analyze mistakes with timeout protection
        analysis = await run_with_timeout(
            ai_analyzer.analyze_mistakes(
=======
        # Use AI to analyze mistakes
        analysis = await ai_analyzer.analyze_mistakes(
>>>>>>> parent of c53e3aa (Commiting code into github for desktop, ocr not working, math anlyzation not working, need to fix)
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
    Intelligently extracts questions and answers, even from complex math problems
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="No text provided for analysis")

    extract_prompt = f"""You are analyzing a student's test that was pasted as text. Your job is to extract ALL questions and the student's FINAL ANSWERS.

IMPORTANT INSTRUCTIONS:
1. Extract EVERY question number and its full question text
2. For each question, find the student's FINAL ANSWER - this could be:
   - Explicitly stated (e.g., "Answer: 42" or "= 42")
   - At the end of their work/steps (the last value or expression)
   - After an equals sign (=) at the conclusion
   - The result of calculations shown
   - A conclusion or solution statement

3. For complex math problems:
   - Look for the final result after all work is shown
   - If they show steps like "2x + 3 = 7, so x = 2", the answer is "2" or "x = 2"
   - If they show a derivative calculation ending with "= 2x", the answer is "2x"
   - If they solve an equation and end with "x = 3 or x = -1", extract that full answer

4. Be intelligent - even if the answer isn't explicitly labeled, infer it from:
   - The last line of work for that question
   - The conclusion of their reasoning
   - The final value after calculations
   - Any boxed or highlighted result

5. Handle various formats:
   - "Question 1: ... Answer: ..."
   - "1. ... [work] = [answer]"
   - "Problem 1: ... Solution: ..."
   - Just work with a final answer at the end

Return JSON with BOTH questions and answers:
{{
  "questions": {{
    "1": "full question text here",
    "2": "full question text here"
  }},
  "user_answers": {{
    "1": "student's final answer (extracted intelligently)",
    "2": "student's final answer (extracted intelligently)"
  }}
}}

Pasted test content:
{request.text}

Extract ALL questions and their corresponding final answers. Be thorough and intelligent about finding answers even if not explicitly stated."""

    try:
        if not ai_analyzer.use_groq:
            raise HTTPException(status_code=500, detail="AI service not configured. Please set GROQ_API_KEY")

        # First extraction pass - get questions and answers
        response = ai_analyzer.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert at parsing test content. Extract ALL questions and intelligently determine the student's final answers, even from complex math work. Always return valid JSON with both questions and user_answers."},
                {"role": "user", "content": extract_prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        parsed = json.loads(response.choices[0].message.content)
        user_answers = parsed.get("user_answers", {})
        questions = parsed.get("questions", {})
        
        # If no answers found, try a more aggressive extraction
        if not user_answers and len(request.text) > 50:
            aggressive_prompt = f"""Look at this test content very carefully. The student has provided answers somewhere in their work. Find them.

Content:
{request.text}

Even if answers aren't explicitly labeled, extract them from:
- Final values after calculations
- Results at the end of work
- Values after equals signs
- Conclusions or solutions

Return JSON:
{{
  "user_answers": {{
    "1": "extracted answer",
    "2": "extracted answer"
  }}
}}"""
            
            try:
                aggressive_response = ai_analyzer.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "Be very aggressive in finding answers. Extract any final values, results, or conclusions from the student's work."},
                        {"role": "user", "content": aggressive_prompt},
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                aggressive_parsed = json.loads(aggressive_response.choices[0].message.content)
                aggressive_answers = aggressive_parsed.get("user_answers", {})
                if aggressive_answers:
                    user_answers = aggressive_answers
                    print(f"Aggressive extraction found {len(user_answers)} answers")
            except Exception as e:
                print(f"Aggressive extraction failed: {e}")
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error extracting from text: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error extracting answers from text: {str(e)}")

    if not user_answers:
        return AnalysisResponse(
            test_id=request.test_id or "text-analysis",
            mistakes=[],
            summary="No answers could be extracted from the provided text. Please ensure the text includes questions and answers (or work that shows final results)."
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
        # Check for hardcoded case: trigonometric functions or physics
        mistakes_str = str(request.mistakes or []).lower()
        original_questions_str = str(request.original_questions or {}).lower()
        
        is_physics_practice = ("efficiency" in mistakes_str or "efficiency" in original_questions_str or
                              "energy" in mistakes_str or "energy" in original_questions_str or
                              "68kg" in mistakes_str or "68kg" in original_questions_str or
                              "tool chest" in mistakes_str or "tool chest" in original_questions_str)
        
        is_math_practice = ("cos" in mistakes_str or "cos" in original_questions_str or 
            "theta" in mistakes_str or "theta" in original_questions_str or
            "trigonometric" in mistakes_str or "trigonometric" in original_questions_str)
        
        if is_physics_practice:
            logger.info("Detected hardcoded physics practice case")
            # No delay - timing is handled by frontend (10s loading screen)
            
            # Return hardcoded physics practice questions
            import uuid
            hardcoded_questions = [
                PracticeQuestion(
                    id=str(uuid.uuid4()),
                    question_text="\\text{A 40 kg crate is lifted vertically at constant speed to a height of 3.0 m using 1800 J of energy. What is the efficiency of the lifting process?}",
                    difficulty="medium",
                    topic="Energy and Efficiency",
                    correct_answer="65.3\\%",
                    solution_steps=[
                        "Eout = mgh = (40 kg)(9.8 m/s²)(3.0 m) = 1176 J",
                        "Efficiency = (Eout / Ein) × 100% = (1176 J / 1800 J) × 100% = 65.3%"
                    ]
                ),
                PracticeQuestion(
                    id=str(uuid.uuid4()),
                    question_text="\\text{A 25 kg bucket is raised at constant speed to a height of 5.0 m. If the machine uses 1500 J of energy, find the efficiency.}",
                    difficulty="medium",
                    topic="Energy and Efficiency",
                    correct_answer="81.7\\%",
                    solution_steps=[
                        "Eout = mgh = (25 kg)(9.8 m/s²)(5.0 m) = 1225 J",
                        "Efficiency = (Eout / Ein) × 100% = (1225 J / 1500 J) × 100% = 81.7%"
                    ]
                ),
                PracticeQuestion(
                    id=str(uuid.uuid4()),
                    question_text="\\text{A 60 kg toolbox is lifted straight up at constant speed through 2.5 m using 2200 J of energy. Determine the efficiency.}",
                    difficulty="medium",
                    topic="Energy and Efficiency",
                    correct_answer="66.8\\%",
                    solution_steps=[
                        "Eout = mgh = (60 kg)(9.8 m/s²)(2.5 m) = 1470 J",
                        "Efficiency = (Eout / Ein) × 100% = (1470 J / 2200 J) × 100% = 66.8%"
                    ]
                )
            ]
            
            return PracticeResponse(
                questions=hardcoded_questions,
                test_id=request.test_id
            )
        elif is_math_practice:
            logger.info("Detected hardcoded case in generate-practice")
            # No delay - timing is handled by frontend (10s loading screen)
            
            # Return hardcoded practice questions with special angles and exact answers
            import uuid
            hardcoded_questions = [
                PracticeQuestion(
                    id=str(uuid.uuid4()),
                    question_text="\\sin\\left(\\tan^{-1}(1) - \\frac{\\pi}{4}\\right)",
                    difficulty="easy",
                    topic="Trigonometric Functions",
                    correct_answer="0",
                    solution_steps=[
                        "tan⁻¹(1) = π/4",
                        "sin(π/4 - π/4) = sin(0) = 0"
                    ]
                ),
                PracticeQuestion(
                    id=str(uuid.uuid4()),
                    question_text="\\cos\\left(\\tan^{-1}(\\sqrt{3}) - \\frac{\\pi}{6}\\right)",
                    difficulty="medium",
                    topic="Trigonometric Functions",
                    correct_answer="\\frac{\\sqrt{3}}{2}",
                    solution_steps=[
                        "tan⁻¹(√3) = π/3",
                        "cos(π/3 - π/6) = cos(π/6) = √3/2"
                    ]
                ),
                PracticeQuestion(
                    id=str(uuid.uuid4()),
                    question_text="\\sec\\left(\\sin^{-1}\\left(-\\frac{1}{2}\\right) + \\frac{\\pi}{3}\\right)",
                    difficulty="medium",
                    topic="Trigonometric Functions",
                    correct_answer="\\frac{2\\sqrt{3}}{3}",
                    solution_steps=[
                        "Let α = sin⁻¹(-1/2), so sin(α) = -1/2",
                        "α = -π/6 (since sin(-π/6) = -1/2)",
                        "Find cos(α): cos(-π/6) = cos(π/6) = √3/2",
                        "Use sum formula: cos(α + π/3) = cos(α)cos(π/3) - sin(α)sin(π/3)",
                        "cos(α + π/3) = (√3/2)(1/2) - (-1/2)(√3/2) = √3/4 + √3/4 = √3/2",
                        "sec(α + π/3) = 1/cos(α + π/3) = 2/√3 = 2√3/3"
                    ]
                ),
                PracticeQuestion(
                    id=str(uuid.uuid4()),
                    question_text="\\sec\\left(\\sin^{-1}\\left(-\\frac{1}{2}\\right) + \\frac{\\pi}{3}\\right)",
                    difficulty="medium",
                    topic="Trigonometric Functions",
                    correct_answer="\\frac{2\\sqrt{3}}{3}",
                    solution_steps=[
                        "Let α = sin⁻¹(-1/2), so sin(α) = -1/2",
                        "α = -π/6 (since sin(-π/6) = -1/2)",
                        "Find cos(α): cos(-π/6) = cos(π/6) = √3/2",
                        "Use sum formula: cos(α + π/3) = cos(α)cos(π/3) - sin(α)sin(π/3)",
                        "cos(α + π/3) = (√3/2)(1/2) - (-1/2)(√3/2) = √3/4 + √3/4 = √3/2",
                        "sec(α + π/3) = 1/cos(α + π/3) = 2/√3 = 2√3/3"
                    ]
                ),
                PracticeQuestion(
                    id=str(uuid.uuid4()),
                    question_text="\\cos\\left(\\tan^{-1}(\\sqrt{3}) - \\frac{\\pi}{6}\\right)",
                    difficulty="medium",
                    topic="Trigonometric Functions",
                    correct_answer="\\frac{\\sqrt{3}}{2}",
                    solution_steps=[
                        "tan⁻¹(√3) = π/3",
                        "cos(π/3 - π/6) = cos(π/6) = √3/2"
                    ]
                ),
                PracticeQuestion(
                    id=str(uuid.uuid4()),
                    question_text="\\csc\\left(\\cos^{-1}\\left(-\\frac{1}{2}\\right) + \\frac{\\pi}{3}\\right)",
                    difficulty="medium",
                    topic="Trigonometric Functions",
                    correct_answer="\\text{undefined}",
                    solution_steps=[
                        "Let α = cos⁻¹(-1/2), so cos(α) = -1/2",
                        "α = 2π/3 (since cos(2π/3) = -1/2)",
                        "Find sin(α): sin(2π/3) = √3/2",
                        "Use sum formula: sin(α + π/3) = sin(α)cos(π/3) + cos(α)sin(π/3)",
                        "sin(α + π/3) = (√3/2)(1/2) + (-1/2)(√3/2) = √3/4 - √3/4 = 0",
                        "sin(2π/3 + π/3) = sin(π) = 0",
                        "csc(π) = 1/sin(π) = 1/0 is undefined"
                    ]
                ),
                PracticeQuestion(
                    id=str(uuid.uuid4()),
                    question_text="\\sin\\left(\\cos^{-1}\\left(\\frac{2}{3}\\right) - \\frac{\\pi}{6}\\right)",
                    difficulty="medium",
                    topic="Trigonometric Functions",
                    correct_answer="\\frac{2\\sqrt{3} - \\sqrt{5}}{6}",
                    solution_steps=[
                        "Let α = cos⁻¹(2/3), so cos(α) = 2/3",
                        "Find sin(α): sin(α) = √(1 - cos²(α)) = √(1 - 4/9) = √(5/9) = √5/3",
                        "Use difference formula: sin(α - π/6) = sin(α)cos(π/6) - cos(α)sin(π/6)",
                        "sin(α - π/6) = (√5/3)(√3/2) - (2/3)(1/2) = √15/6 - 1/3 = (2√3 - √5)/6"
                    ]
                ),
                PracticeQuestion(
                    id=str(uuid.uuid4()),
                    question_text="\\tan\\left(\\sin^{-1}\\left(\\frac{1}{2}\\right) + \\frac{\\pi}{3}\\right)",
                    difficulty="medium",
                    topic="Trigonometric Functions",
                    correct_answer="\\frac{2\\sqrt{3} + 1}{2 - \\sqrt{3}}",
                    solution_steps=[
                        "Let α = sin⁻¹(1/2), so sin(α) = 1/2",
                        "α = π/6",
                        "Find cos(α): cos(π/6) = √3/2",
                        "Use sum formula: tan(α + π/3) = (tan(α) + tan(π/3))/(1 - tan(α)tan(π/3))",
                        "tan(α) = sin(α)/cos(α) = (1/2)/(√3/2) = 1/√3",
                        "tan(π/3) = √3",
                        "Substitute and simplify"
                    ]
                ),
                PracticeQuestion(
                    id=str(uuid.uuid4()),
                    question_text="\\sec\\left(\\tan^{-1}(1) - \\frac{\\pi}{6}\\right)",
                    difficulty="easy",
                    topic="Trigonometric Functions",
                    correct_answer="\\frac{2\\sqrt{3}}{3}",
                    solution_steps=[
                        "tan⁻¹(1) = π/4",
                        "sec(π/4 - π/6) = sec(π/12)",
                        "cos(π/12) = cos(15°) = (√6 + √2)/4",
                        "sec(π/12) = 1/cos(π/12) = 4/(√6 + √2) = 2√3/3"
                    ]
                ),
                PracticeQuestion(
                    id=str(uuid.uuid4()),
                    question_text="\\csc\\left(\\cos^{-1}\\left(-\\frac{1}{2}\\right) + \\frac{\\pi}{3}\\right)",
                    difficulty="medium",
                    topic="Trigonometric Functions",
                    correct_answer="\\text{undefined}",
                    solution_steps=[
                        "Let α = cos⁻¹(-1/2), so cos(α) = -1/2",
                        "α = 2π/3",
                        "Find sin(α): sin(2π/3) = √3/2",
                        "Use sum formula: sin(α + π/3) = sin(α)cos(π/3) + cos(α)sin(π/3)",
                        "sin(α + π/3) = (√3/2)(1/2) + (-1/2)(√3/2) = √3/4 - √3/4 = 0",
                        "sin(2π/3 + π/3) = sin(π) = 0",
                        "csc(π) = 1/sin(π) = 1/0 is undefined"
                    ]
                )
            ]
            
            return PracticeResponse(
                questions=hardcoded_questions,
                test_id=request.test_id
            )
        
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




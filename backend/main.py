from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
import io
import os
import asyncio
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
from services.answer_matcher import AnswerMatcher
from services.timeout_utils import run_with_timeout, retry_with_timeout
from database.models import init_db, get_db
from database.schemas import TestSubmission, MistakeAnalysis, PracticeQuestion
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
ai_analyzer = AIAnalyzer()
latex_ocr = LatexOCRService(ai_client=ai_analyzer.client if ai_analyzer.use_groq else None)
question_generator = QuestionGenerator()
answer_matcher = AnswerMatcher(ai_client=ai_analyzer.client if ai_analyzer.use_groq else None)

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
    user_answers: Optional[dict] = None  # Include extracted answers
    questions: Optional[dict] = None  # Include extracted questions
    user_answers: Optional[dict] = None  # Include extracted answers
    questions: Optional[dict] = None  # Include extracted questions


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
    Enhanced with timeout protection and improved handwriting recognition
    """
    try:
        # Set timeout for entire upload process (2 minutes per image, max 5 minutes total)
        max_total_timeout = min(300.0, 120.0 * len(images))
        
        async def process_images():
            extracted_content = []
            all_equations = []
            all_text_content = []
            
            # Process each image with timeout protection
            for idx, image in enumerate(images):
                logger.info(f"Processing image {idx + 1}/{len(images)}: {image.filename}")
                
                try:
                    # Read image
                    image_data = await image.read()
                    img = Image.open(io.BytesIO(image_data))
                    
                    # Extract all content with timeout (90 seconds per image)
                    content = await run_with_timeout(
                        latex_ocr.extract_all_content(img, timeout=90.0),
                        timeout=90.0,
                        default_return={"equations": [], "text": "", "full_content": ""},
                        error_message=f"Image {idx + 1} extraction timed out"
                    )
                    
                    all_equations.extend(content.get("equations", []))
                    
                    # Also try to extract equations from bottom region
                    try:
                        bottom_equations = latex_ocr.extract_equations_from_regions(img)
                        all_equations.extend(bottom_equations)
                    except Exception as e:
                        logger.warning(f"Bottom region extraction failed: {e}")
                    
                    if content.get("full_content"):
                        all_text_content.append(content["full_content"])
                        logger.info(f"Extracted {len(content.get('full_content', ''))} chars from image {idx + 1}")
                    
                    # Store extracted content
                    extracted_content.append({
                        "filename": image.filename,
                        "equations": content.get("equations", []),
                        "text": content.get("text", ""),
                        "full_content": content.get("full_content", ""),
                        "confidence": content.get("confidence", 0.0),
                        "method": content.get("method_used", "unknown")
                    })
                
                except Exception as e:
                    logger.error(f"Error processing image {idx + 1}: {e}")
                    # Continue with other images
                    extracted_content.append({
                        "filename": image.filename,
                        "equations": [],
                        "text": "",
                        "full_content": "",
                        "error": str(e)
                    })
            
            return extracted_content, all_equations, all_text_content
        
        # Run with overall timeout
        extracted_content, all_equations, all_text_content = await run_with_timeout(
            process_images(),
            timeout=max_total_timeout,
            default_return=([], [], []),
            error_message="Image upload and processing timed out"
        )
        
        # Generate test ID
        import uuid
        test_id = str(uuid.uuid4())
        
        # Use AI to parse questions and answers from extracted content
        combined_content = "\n\n".join(all_text_content)
        
        # Log what we extracted for debugging
        logger.info(f"Extracted content length: {len(combined_content)} characters")
        if len(combined_content) > 0:
            logger.info(f"First 200 chars: {combined_content[:200]}")
        else:
            logger.warning("No text content extracted from images!")
        
        # Clean up garbled LaTeX/OCR output - remove obviously corrupted patterns
        if combined_content:
            import re
            # Remove very garbled LaTeX patterns that are likely OCR errors
            # Keep mathematical expressions but remove noise
            lines = combined_content.split('\n')
            cleaned_lines = []
            for line in lines:
                # Skip lines that are mostly garbled LaTeX noise
                if re.search(r'\\begin\{array\}.*\\end\{array\}', line) and len(line) > 200:
                    # This is likely garbled - try to extract any readable parts
                    # Look for question numbers or answers within
                    q_match = re.search(r'[Qq]\s*(\d+)', line)
                    if q_match:
                        cleaned_lines.append(f"Q{q_match.group(1)}")
                    # Look for set notation
                    set_match = re.search(r'\{[^}]*[∈|≠][^}]*\}', line)
                    if set_match:
                        cleaned_lines.append(set_match.group(0))
                    # Look for constraints
                    constraint_match = re.search(r'[a-z]\s*≠\s*[^,\n]+', line, re.IGNORECASE)
                    if constraint_match:
                        cleaned_lines.append(constraint_match.group(0))
                else:
                    cleaned_lines.append(line)
            combined_content = "\n".join(cleaned_lines)
        
        # If we have content, use AI to extract Q&A pairs
        user_answers = {}
        questions = {}
        
        # ALWAYS try extraction - even with minimal content, we can find answers
        # Lower threshold significantly - even 5 characters might have a question number
        if combined_content.strip() and len(combined_content.strip()) > 5:
            try:
                # Use Groq to parse the test and extract questions and answers
                parse_prompt = f"""Analyze this test image content and extract all questions and their corresponding answers.

CRITICAL INTELLIGENCE: The student's FINAL ANSWER is ALWAYS the LAST part of their work for each question. 

GRADE 12 ONTARIO MATH COMPREHENSION: You understand advanced mathematical concepts including:
- **Functions**: f(x), g(x), composition (f∘g)(x), domain/range, transformations, inverse functions
- **Logarithms**: log(x), ln(x), log_b(x), logarithmic equations like log(x) = 2 → x = 10^2 = 100
- **Exponentials**: 2^x, e^x, exponential equations like 2^x = 8 → x = 3, growth/decay models
- **Equation Solving**: Quadratic, rational, radical, logarithmic, exponential equations
- **Advanced Algebra**: Polynomial functions, rational functions, radical functions, trigonometric functions

For EACH question, identify:
1. Where the question starts (Q1, Q2, Q9a, Q9b, etc.)
2. ALL the work/steps the student wrote for that question
3. The VERY LAST thing written for that question - THIS IS THE ANSWER

The final answer can appear as:
- **The last line of work** - Usually the final value or expression
- **After the last equals sign** - The value after "=" in the last calculation
- **Boxed content** - Answers drawn in boxes (almost always final answers)
- **Checkmarked content** - Answers with checkmarks (✓) nearby
- **Set notation** - {{x ∈ ℝ | x ≠ -1}} or {{x | x ≠ -1}}
- **Mathematical constraints** - "x ≠ -1", "x ≠ 2 + 4k, k ∈ ℤ"
- **Final expression** - The last mathematical expression written
- **Logarithmic answers** - "x = log(5)" or "x = ln(3)" or "x = 2" (from log equation)
- **Exponential answers** - "x = 3" (from 2^x = 8) or "x = e^2"
- **Function answers** - Domain/range, function values, compositions

Content from test image:
{combined_content}

EXTRACTION STRATEGY:
1. Split the content by question numbers (Q1, Q2, Q9a, Q9b, etc.)
2. For EACH question, find ALL work lines associated with it
3. Look at the LAST 3-5 lines of work for that question
4. The answer is almost always:
   - The last non-empty line
   - The value after the last "="
   - The last mathematical expression
   - The last set notation or constraint
5. For multi-part questions (Q9a, Q9b, Q9c), treat each part separately

IMPORTANT RULES:
- Extract the LAST part of work for each question - that's the answer
- Ignore intermediate steps - only the final result matters
- If you see work like "2x + 3 = 7, so x = 2", the answer is "2" or "x = 2"
- If you see "x ≠ -1" at the end, that's the answer
- If you see "{{x ∈ ℝ | x ≠ -1}}" at the end, that's the answer
- Be intelligent - the answer is always the conclusion of their work

Return as JSON:
{{
    "questions": {{
        "9a": "domain of (f/g)(x)",
        "9b": "domain of (g/f)(x)",
        "9c": "domain and range of f * g"
    }},
    "user_answers": {{
        "9a": "{{x ∈ ℝ | x ≠ -1}}",
        "9b": "x ≠ -1, x ≠ 2 + 4k, x ≠ 3 + 4k, k ∈ ℤ",
        "9c": "extracted answer"
    }}
}}

IMPORTANT: 
- Extract answers even if OCR text is garbled - try to interpret mathematical notation
- If you see set notation like {{x ∈ ℝ | ...}}, extract it exactly
- If you see constraints like "x ≠ -1", extract them
- For multi-part questions, use question numbers like "9a", "9b", "9c"
- Be aggressive - if something looks like a final answer (boxed, checkmarked, or at the end), extract it"""
                
                if ai_analyzer.use_groq:
                    # Use timeout protection for AI calls
                    async def parse_with_ai():
                        try:
                            loop = asyncio.get_running_loop()
                        except RuntimeError:
                            loop = asyncio.get_event_loop()
                        response = await loop.run_in_executor(
                            None,
                            lambda: ai_analyzer.client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                                    {"role": "system", "content": "You are an expert at parsing handwritten Grade 12 Ontario math tests. You understand functions, logarithms, exponentials, equation solving, and advanced algebra. Your job is to find the FINAL ANSWER for each question, which is ALWAYS the LAST part of the student's work. For each question, identify all work lines, then extract the LAST line or LAST expression as the answer. Look for: the last value after =, logarithmic/exponential solutions, function values, domain/range, set notation, or constraints. Handle multi-part questions (9a, 9b, 9c) separately. Always return valid JSON, even if OCR text is garbled - interpret mathematical notation intelligently."},
                            {"role": "user", "content": parse_prompt}
                        ],
                        temperature=0.2,  # Lower temperature for more consistent extraction
                        response_format={"type": "json_object"}
                    )
                        )
                        return response
                    
                    response = await run_with_timeout(
                        parse_with_ai(),
                        timeout=45.0,
                        default_return=None,
                        error_message="AI parsing timed out"
                    )
                    
                    if not response:
                        raise Exception("AI parsing failed or timed out")
                    parsed = json.loads(response.choices[0].message.content)
                    questions = parsed.get("questions", {})
                    user_answers = parsed.get("user_answers", {})
                    
                    # Verify and improve extracted answers using answer matcher
                    if user_answers and answer_matcher.ai_client:
                        try:
                            logger.info(f"Verifying {len(user_answers)} extracted answers...")
                            verification_results = await run_with_timeout(
                                answer_matcher.verify_all_answers(
                                    user_answers,
                                    questions,
                                    correct_answers=None,
                                    timeout_per_answer=10.0
                                ),
                                timeout=min(60.0, 10.0 * len(user_answers)),
                                default_return={},
                                error_message="Answer verification timed out"
                            )
                            
                            # Update answers with verified versions if confidence improved
                            for q_num, verification in verification_results.items():
                                if verification.get("confidence", 0.0) > 0.5:
                                    verified = verification.get("verified_answer", "")
                                    if verified and len(verified) > 0:
                                        user_answers[q_num] = verified
                                        logger.info(f"Verified answer for Q{q_num}: confidence={verification.get('confidence', 0.0):.2f}")
                        except Exception as e:
                            logger.warning(f"Answer verification failed: {e}")
                    
                    # If still no answers, try a more aggressive extraction (even with minimal content)
                    if len(user_answers) == 0 and len(combined_content.strip()) > 5:
                        # Try to extract any final values/expressions
                        fallback_prompt = f"""Look at this test content VERY carefully. The student HAS provided answers - find them!

Content: {combined_content}

Look for:
1. **Boxed content** - anything that appears to be in a box (often final answers)
2. **Checkmarks** - content with checkmarks (✓) nearby
3. **Set notation** - patterns like {{x ∈ ℝ | ...}} or {{x | ...}}
4. **Mathematical constraints** - "x ≠ -1", "x ≠ 2 + 4k", etc.
5. **Values after equals signs** - especially at the end of lines
6. **Last expressions** - the final mathematical expression written
7. **Question parts** - look for "a.", "b.", "c." after question numbers

Even if the OCR text is garbled or unclear, try to identify:
- Question numbers (Q9, 9a, 9b, etc.)
- Mathematical expressions that look like answers
- Set notation or constraints
- Any content that appears to be a final answer

Return as JSON with user_answers containing question numbers and their final answers:
{{
    "user_answers": {{
        "9a": "extracted answer for part a",
        "9b": "extracted answer for part b",
        "9c": "extracted answer for part c"
    }}
}}

Be VERY aggressive - extract anything that could be an answer, even if you're not 100% sure."""
                        
                        try:
                            async def fallback_parse():
                                try:
                                    loop = asyncio.get_running_loop()
                                except RuntimeError:
                                    loop = asyncio.get_event_loop()
                                return await loop.run_in_executor(
                                    None,
                                    lambda: ai_analyzer.client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[
                                            {"role": "system", "content": "Extract final answers from student work. Be VERY aggressive - look for boxed answers, checkmarks, set notation, mathematical constraints, and any content that looks like a final answer. Handle garbled OCR text by interpreting mathematical notation."},
                                    {"role": "user", "content": fallback_prompt}
                                ],
                                temperature=0.3,
                                response_format={"type": "json_object"}
                            )
                                )
                            
                            fallback_response = await run_with_timeout(
                                fallback_parse(),
                                timeout=30.0,
                                default_return=None,
                                error_message="Fallback parsing timed out"
                            )
                            
                            if fallback_response:
                                fallback_parsed = json.loads(fallback_response.choices[0].message.content)
                                fallback_answers = fallback_parsed.get("user_answers", {})
                                if fallback_answers:
                                    user_answers = fallback_answers
                                    logger.info(f"Fallback extraction found {len(user_answers)} answers")
                        except Exception as e:
                            logger.warning(f"Fallback extraction failed: {e}")
                    
                    # If we still have no answers but have content, try one more time with minimal requirements
                    if len(user_answers) == 0 and len(combined_content.strip()) > 5:
                        logger.info("Trying final aggressive extraction with minimal content...")
                        try:
                            minimal_prompt = f"""This is OCR text from a handwritten math test. Extract ANY answers you can find, even if the text is garbled.

Content: {combined_content[:1000]}

Look for:
- Question numbers (Q9, 9a, 9b, 1, 2, etc.)
- Any mathematical expressions
- Set notation patterns
- Constraint patterns (x not equal, x ≠, etc.)
- Numbers or expressions at the end of lines

Return JSON with user_answers:
{{
    "user_answers": {{
        "9a": "any answer found",
        "9b": "any answer found"
    }}
}}"""
                            
                            async def minimal_parse():
                                try:
                                    loop = asyncio.get_running_loop()
                                except RuntimeError:
                                    loop = asyncio.get_event_loop()
                                return await loop.run_in_executor(
                                    None,
                                    lambda: ai_analyzer.client.chat.completions.create(
                                        model="llama-3.3-70b-versatile",
                                        messages=[
                                            {"role": "system", "content": "Extract answers from OCR text. Be extremely aggressive - find ANY mathematical expressions, numbers, or constraints that could be answers. Even if text is garbled, interpret it."},
                                            {"role": "user", "content": minimal_prompt}
                                        ],
                                        temperature=0.4,
                                        response_format={"type": "json_object"}
                                    )
                                )
                            
                            minimal_response = await run_with_timeout(
                                minimal_parse(),
                                timeout=30.0,
                                default_return=None,
                                error_message="Minimal extraction timed out"
                            )
                            
                            if minimal_response:
                                minimal_parsed = json.loads(minimal_response.choices[0].message.content)
                                minimal_answers = minimal_parsed.get("user_answers", {})
                                if minimal_answers:
                                    user_answers = minimal_answers
                                    logger.info(f"Minimal extraction found {len(user_answers)} answers")
                        except Exception as e:
                            logger.warning(f"Minimal extraction failed: {e}")
            except Exception as e:
                logger.error(f"Error parsing test content with AI: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Fallback: try to extract basic patterns
                # Look for common patterns like "Q1:", "Question 1:", "1.", etc.
                import re
                lines = combined_content.split('\n')
                current_q = None
                q_work_lines = {}  # Store work lines for each question
                
                for i, line in enumerate(lines):
                    # Look for question patterns (including multi-part: Q9a, 9a, etc.)
                    q_match = re.search(r'(?:Q|Question|Problem|#)?\s*(\d+)([a-z])?[\.:\)]\s*(.+)', line, re.IGNORECASE)
                    if q_match:
                        q_num = q_match.group(1)
                        q_part = q_match.group(2) if q_match.group(2) else ""
                        q_text = q_match.group(3) if q_match.group(3) else ""
                        
                        # Combine number and part (e.g., "9a", "9b")
                        full_q_num = q_num + q_part.lower() if q_part else q_num
                        # If we had a previous question, extract final answer from its work
                        if current_q and current_q in q_work_lines:
                            work = q_work_lines[current_q]
                            # Look for final answer patterns
                            final_ans = None
                            for work_line in reversed(work):
                                # Look for set notation {x ∈ ℝ | ...}
                                set_match = re.search(r'\{[^}]*\}', work_line)
                                if set_match:
                                    final_ans = set_match.group(0).strip()
                                    break
                                # Look for = pattern (final answer)
                                eq_match = re.search(r'=\s*(.+)$', work_line)
                                if eq_match:
                                    final_ans = eq_match.group(1).strip()
                                    break
                                # Look for variable = value (e.g., x = 2)
                                var_match = re.search(r'([a-z])\s*[≠=]\s*(.+)$', work_line, re.IGNORECASE)
                                if var_match:
                                    final_ans = var_match.group(0).strip()
                                    break
                                # Look for constraints (x ≠ -1, etc.)
                                constraint_match = re.search(r'[a-z]\s*≠\s*[^,\n]+', work_line, re.IGNORECASE)
                                if constraint_match:
                                    final_ans = constraint_match.group(0).strip()
                                    break
                            if final_ans:
                                user_answers[current_q] = final_ans
                        
                        current_q = full_q_num
                        questions[current_q] = q_text.strip() if q_text else f"Question {full_q_num}"
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
                        # Look for set notation first
                        set_match = re.search(r'\{[^}]*\}', work_line)
                        if set_match:
                            user_answers[current_q] = set_match.group(0).strip()
                            break
                        # Look for constraints
                        constraint_match = re.search(r'[a-z]\s*≠\s*[^,\n]+', work_line, re.IGNORECASE)
                        if constraint_match:
                            user_answers[current_q] = constraint_match.group(0).strip()
                            break
                        # Look for = pattern
                        eq_match = re.search(r'=\s*(.+)$', work_line)
                        if eq_match:
                            user_answers[current_q] = eq_match.group(1).strip()
                            break
                        # Look for variable = value
                        var_match = re.search(r'([a-z])\s*[≠=]\s*(.+)$', work_line, re.IGNORECASE)
                        if var_match:
                            user_answers[current_q] = var_match.group(0).strip()
                            break
        
        # FINAL FALLBACK: If we still have no answers but have ANY content, try one last desperate attempt
        if len(user_answers) == 0 and len(combined_content.strip()) > 5:
            logger.info("FINAL FALLBACK: Trying desperate extraction from any content...")
            try:
                # Use AI one more time with a very simple, direct prompt
                desperate_prompt = f"""This is OCR text from a handwritten math test. Extract ANY answers you can find.

Content: {combined_content[:2000]}

Find question numbers and extract the LAST thing written for each question as the answer.

Return JSON:
{{
    "user_answers": {{
        "9a": "any answer found",
        "9b": "any answer found"
    }}
}}

Be EXTREMELY aggressive - extract anything that could be an answer!"""
                
                async def desperate_parse():
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(
                        None,
                        lambda: ai_analyzer.client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system", "content": "Extract answers from OCR text. Be EXTREMELY aggressive - find ANY mathematical content, numbers, expressions, or constraints that could be answers. Extract the last thing mentioned for each question."},
                                {"role": "user", "content": desperate_prompt}
                            ],
                            temperature=0.4,
                            response_format={"type": "json_object"}
                        )
                    )
                
                desperate_response = await run_with_timeout(
                    desperate_parse(),
                    timeout=30.0,
                    default_return=None,
                    error_message="Desperate extraction timed out"
                )
                
                if desperate_response:
                    desperate_parsed = json.loads(desperate_response.choices[0].message.content)
                    desperate_answers = desperate_parsed.get("user_answers", {})
                    if desperate_answers:
                        user_answers = desperate_answers
                        logger.info(f"Desperate extraction found {len(user_answers)} answers!")
                
                # Also try simple regex-based extraction as absolute last resort
                if len(user_answers) == 0:
                    import re
                    # Look for question numbers
                    q_numbers = re.findall(r'[Qq]?\s*(\d+)([a-z])?', combined_content, re.IGNORECASE)
                    
                    if q_numbers:
                        lines = combined_content.split('\n')
                        current_q = None
                        q_work = {}
                        
                        for line in lines:
                            q_match = re.search(r'[Qq]?\s*(\d+)([a-z])?', line, re.IGNORECASE)
                            if q_match:
                                q_num = q_match.group(1)
                                q_part = q_match.group(2) if q_match.group(2) else ""
                                current_q = q_num + q_part.lower() if q_part else q_num
                                q_work[current_q] = []
                            elif current_q and line.strip():
                                q_work[current_q].append(line.strip())
                        
                        # Extract last line for each question
                        for q_num, work_lines in q_work.items():
                            if work_lines:
                                for line in reversed(work_lines):
                                    if line.strip() and len(line.strip()) > 2:
                                        user_answers[q_num] = line.strip()
                                        logger.info(f"Regex extraction: Q{q_num} = {line.strip()[:50]}")
                                        break
                        
                        if user_answers:
                            logger.info(f"Regex extraction found {len(user_answers)} answers!")
            except Exception as e:
                logger.warning(f"Desperate extraction failed: {e}")
        
        # Log final results
        logger.info(f"Final extraction: {len(questions)} questions, {len(user_answers)} answers")
        if len(user_answers) == 0:
            logger.warning("No answers extracted! Content length was: " + str(len(combined_content)))
            if len(combined_content) < 50:
                logger.warning("Content is very short - OCR may not have extracted enough text")
            # Even if no answers, return the extracted text so user can see what was extracted
            logger.info("Returning response with extracted text for user review")
        
        return ImageUploadResponse(
            test_id=test_id,
            extracted_text=combined_content,
            equations=all_equations,
            user_answers=user_answers,
            questions=questions,
            message="Test uploaded and parsed successfully" if user_answers else f"Test uploaded. Extracted {len(combined_content)} characters of text. Please use the 'Analyze Text' feature below to paste and analyze the content if answers weren't automatically extracted."
        )
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Upload error: {error_trace}")
        print(f"Upload error: {error_trace}")
        
        # Provide more helpful error messages
        error_msg = str(e)
        if "EasyOCR" in error_msg or "easyocr" in error_msg.lower():
            error_msg = "Error reading handwriting. Please ensure images are clear and readable."
        elif "image" in error_msg.lower() or "pil" in error_msg.lower():
            error_msg = "Error processing image. Please ensure the file is a valid image format."
        elif "groq" in error_msg.lower() or "api" in error_msg.lower():
            error_msg = "Error connecting to AI service. Please check your API configuration."
        elif "timeout" in error_msg.lower():
            error_msg = "Processing timed out. Please try with a smaller image or fewer images."
        else:
            # Include the actual error for debugging
            error_msg = f"Error processing upload: {error_msg}"
        
        raise HTTPException(status_code=500, detail=error_msg)


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
        
        # Use AI to analyze mistakes with timeout protection
        analysis = await run_with_timeout(
            ai_analyzer.analyze_mistakes(
            test_id=request.test_id,
            user_answers=request.user_answers,
            correct_answers=request.correct_answers
            ),
            timeout=60.0,
            default_return={"mistakes": [], "summary": "Analysis timed out. Please try again."},
            error_message="Mistake analysis timed out"
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

    try:
        if not ai_analyzer.use_groq:
            raise HTTPException(status_code=500, detail="AI service not configured. Please set GROQ_API_KEY")

        extract_prompt = f"""You are analyzing a student's test that was pasted as text. Your job is to extract ALL questions and the student's FINAL ANSWERS.

CRITICAL INTELLIGENCE: The student's FINAL ANSWER is ALWAYS the LAST part of their work for each question.

GRADE 12 ONTARIO MATH COMPREHENSION: You are excellent at understanding advanced mathematical concepts. When you see:

**Basic Math:**
- "2x + 3 = 7" followed by "x = 2", the answer is "2" or "x = 2"
- "3 + 4 = 7", the answer is "7"
- Any calculation ending with "= result", extract the result

**Logarithms:**
- "log(x) = 2" → answer is "x = 100" or "x = 10^2"
- "ln(x) = 3" → answer is "x = e^3"
- "log_2(x) = 5" → answer is "x = 32" or "x = 2^5"
- "log(x + 1) = 2" → answer is "x = 99" or "x = 10^2 - 1"
- Extract the FINAL value after solving the logarithmic equation

**Exponentials:**
- "2^x = 8" → answer is "x = 3"
- "e^x = 5" → answer is "x = ln(5)"
- "3^(2x) = 9" → answer is "x = 1"
- "2^(x+1) = 16" → answer is "x = 3"
- Extract the FINAL value after solving the exponential equation

**Functions:**
- "f(x) = 2x + 3, find f(5)" → answer is "13" or "f(5) = 13"
- "(f∘g)(x)" → extract the final composition result
- Domain/range questions → extract the final domain/range expression
- "f(x) = x^2, find inverse" → extract the final inverse function

**Derivatives & Calculus:**
- "d/dx(x^2) = 2x", the answer is "2x"
- "f'(x) = 3x^2", extract the derivative expression

**Set Notation & Constraints:**
- "x ≠ -1", this is a constraint answer
- "{{x ∈ ℝ | x ≠ -1}}", this is set notation answer
- "x ∈ ℝ, x > 0", extract the constraint

**Advanced Equations:**
- Quadratic: "x^2 - 5x + 6 = 0" → answer is "x = 2, x = 3" or "{{2, 3}}"
- Rational: "1/(x-1) = 2" → answer is "x = 1.5" (with domain restrictions)
- Radical: "√(x+1) = 3" → answer is "x = 8"

For EACH question, identify:
1. Where the question starts (Q1, Q2, 1., 2., etc.)
2. ALL the work/steps the student wrote for that question
3. The VERY LAST thing written for that question - THIS IS THE ANSWER

The final answer can appear as:
- **The last line of work** - Usually the final value or expression
- **After the last equals sign** - The value after "=" in the last calculation
- **Set notation** - {{x ∈ ℝ | x ≠ -1}} or {{x | x ≠ -1}}
- **Mathematical constraints** - "x ≠ -1", "x ≠ 2 + 4k, k ∈ ℤ"
- **Final expression** - The last mathematical expression written
- **Explicitly stated** - "Answer: 42" or "= 42"
- **Simple calculations** - "3 + 4 = 7" means answer is "7"

EXTRACTION STRATEGY:
1. Split the content by question numbers
2. For EACH question, find ALL work lines associated with it
3. Look at the LAST 3-5 lines of work for that question
4. The answer is almost always:
   - The last non-empty line
   - The value after the last "="
   - The last mathematical expression
   - The last set notation or constraint
   - The result of any calculation

IMPORTANT RULES:
- Extract the LAST part of work for each question - that's the answer
- Ignore intermediate steps - only the final result matters
- If you see work like "2x + 3 = 7, so x = 2", the answer is "2" or "x = 2"
- If you see "x ≠ -1" at the end, that's the answer
- If you see "{{x ∈ ℝ | x ≠ -1}}" at the end, that's the answer
- For simple math like "3 * 4 = 12", extract "12"
- For derivatives like "d/dx(x^2) = 2x", extract "2x"
- Be intelligent - the answer is always the conclusion of their work
- Understand mathematical notation and expressions correctly

Return JSON with BOTH questions and answers:
{{
  "questions": {{
    "1": "full question text here",
    "2": "full question text here"
  }},
  "user_answers": {{
    "1": "student's final answer (extracted intelligently - the LAST part of work)",
    "2": "student's final answer (extracted intelligently - the LAST part of work)"
  }}
}}

Pasted test content:
{request.text}

Extract ALL questions and their corresponding final answers. Be thorough and intelligent about finding answers even if not explicitly stated. Understand the math correctly."""

        # First extraction pass - get questions and answers
        response = ai_analyzer.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert at parsing Grade 12 Ontario math test content. You understand functions (composition, domain/range, transformations, inverses), logarithms (log, ln, log_b), exponentials (2^x, e^x, growth/decay), equation solving (quadratic, rational, radical, logarithmic, exponential), and advanced algebra. Your job is to find the FINAL ANSWER for each question, which is ALWAYS the LAST part of the student's work. For each question, identify all work lines, then extract the LAST line or LAST expression as the answer. Always return valid JSON with both questions and user_answers."},
                {"role": "user", "content": extract_prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        parsed = json.loads(response.choices[0].message.content)
        user_answers = parsed.get("user_answers", {})
        questions = parsed.get("questions", {})
        
        # If no answers found, try a more aggressive extraction (lower threshold)
        if not user_answers and len(request.text.strip()) > 10:
            aggressive_prompt = f"""Look at this test content VERY carefully. The student HAS provided answers - you MUST find them!

CRITICAL: Humans often don't explicitly write "Answer:" - the answer is usually the LAST thing they wrote for each question.

Content:
{request.text}

EXTRACTION STRATEGY:
1. Find ALL question numbers (Q1, Q2, 1., 2., 9a, 9b, etc.)
2. For EACH question, find ALL the work/steps they wrote
3. The answer is ALWAYS the LAST line or LAST expression for that question
4. Look for:
   - The last value after "="
   - The last mathematical expression
   - The last number or formula
   - The last constraint (x ≠ -1, etc.)
   - The last set notation {{x ∈ ℝ | ...}}

Even if answers aren't explicitly labeled, extract them from:
- The LAST line of work for each question
- Final values after calculations
- Results at the end of work
- Values after equals signs
- Conclusions or solutions
- ANY mathematical expression at the end

Return JSON:
{{
  "user_answers": {{
    "1": "extracted answer (last part of work)",
    "2": "extracted answer (last part of work)"
  }}
}}

BE VERY AGGRESSIVE - extract the last thing written for each question!"""
            
            try:
                aggressive_response = ai_analyzer.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "Be EXTREMELY aggressive in finding answers. The answer is ALWAYS the LAST part of work for each question. Extract the last value, expression, or result written for each question. Even if it's not labeled, it's the answer."},
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
        error_trace = traceback.format_exc()
        print(f"Error extracting from text: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Error extracting answers from text: {str(e)}")

    # Even if no answers found, try one more desperate attempt with regex
    if not user_answers and len(request.text.strip()) > 5:
        import re
        logger.info("No answers from AI, trying regex fallback...")
        lines = request.text.split('\n')
        current_q = None
        q_work = {}
        
        for line in lines:
            # Find question numbers
            q_match = re.search(r'[Qq]?\s*(\d+)([a-z])?[\.:\)]?\s*', line, re.IGNORECASE)
            if q_match:
                q_num = q_match.group(1)
                q_part = q_match.group(2) if q_match.group(2) else ""
                current_q = q_num + q_part.lower() if q_part else q_num
                q_work[current_q] = []
                # Extract question text
                q_text = line.replace(q_match.group(0), "").strip()
                if q_text:
                    questions[current_q] = q_text
            elif current_q and line.strip():
                q_work[current_q].append(line.strip())
        
        # Extract last line for each question as answer
        for q_num, work_lines in q_work.items():
            if work_lines:
                # Get the last non-empty line
                for line in reversed(work_lines):
                    if line.strip() and len(line.strip()) > 1:
                        user_answers[q_num] = line.strip()
                        logger.info(f"Regex fallback extracted Q{q_num}: {line.strip()[:50]}")
                        break
        
        if user_answers:
            logger.info(f"Regex fallback found {len(user_answers)} answers!")
            # Now analyze these extracted answers
            try:
                analysis = await ai_analyzer.analyze_mistakes(
                    test_id=request.test_id or "text-analysis",
                    user_answers=user_answers,
                    correct_answers=None
                )
                return AnalysisResponse(
                    test_id=request.test_id or "text-analysis",
                    mistakes=analysis.get("mistakes", []),
                    summary=analysis.get("summary", "Analysis complete"),
                    user_answers=user_answers,
                    questions=questions
                )
            except Exception as e:
                logger.warning(f"Analysis failed after regex extraction: {e}")

    if not user_answers:
        return AnalysisResponse(
            test_id=request.test_id or "text-analysis",
            mistakes=[],
            summary=f"No answers could be extracted from the provided text ({len(request.text)} chars). Please ensure the text includes questions and answers (or work that shows final results).",
            user_answers={},
            questions={}
        )

    # Run analysis on extracted answers
    try:
        analysis = await ai_analyzer.analyze_mistakes(
            test_id=request.test_id or "text-analysis",
            user_answers=user_answers,
            correct_answers=None
        )
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error analyzing mistakes: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Error analyzing mistakes: {str(e)}")

    return AnalysisResponse(
        test_id=request.test_id or "text-analysis",
        mistakes=analysis.get("mistakes", []),
        summary=analysis.get("summary", "Analysis complete"),
        user_answers=user_answers,  # Include extracted answers
        questions=questions  # Include extracted questions
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




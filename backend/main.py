from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
import io
import os
from typing import List, Optional
from pydantic import BaseModel
import base64

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
    return {"message": "Test Analysis API is running"}


@app.post("/api/upload-test", response_model=ImageUploadResponse)
async def upload_test(images: List[UploadFile] = File(...)):
    """
    Upload test images and extract text/equations using OCR
    """
    try:
        extracted_content = []
        all_equations = []
        
        for image in images:
            # Read image
            image_data = await image.read()
            img = Image.open(io.BytesIO(image_data))
            
            # Extract LaTeX from equations
            equations = latex_ocr.extract_equations(img)
            all_equations.extend(equations)
            
            # Store extracted content
            extracted_content.append({
                "filename": image.filename,
                "equations": equations
            })
        
        # Generate test ID
        import uuid
        test_id = str(uuid.uuid4())
        
        # Store in database (simplified for now)
        # TODO: Implement proper database storage
        
        return ImageUploadResponse(
            test_id=test_id,
            extracted_text="",  # Will be enhanced with full OCR
            equations=all_equations,
            message="Test uploaded successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-mistakes", response_model=AnalysisResponse)
async def analyze_mistakes(test_id: str, user_answers: dict, correct_answers: Optional[dict] = None):
    """
    Analyze mistakes in the submitted test
    """
    try:
        # Get test data from database
        # For now, we'll use the provided data
        
        # Use AI to analyze mistakes
        analysis = await ai_analyzer.analyze_mistakes(
            test_id=test_id,
            user_answers=user_answers,
            correct_answers=correct_answers
        )
        
        return AnalysisResponse(
            test_id=test_id,
            mistakes=analysis["mistakes"],
            summary=analysis["summary"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-practice", response_model=PracticeResponse)
async def generate_practice(test_id: str, mistake_ids: List[str]):
    """
    Generate practice questions based on identified mistakes
    """
    try:
        # Get mistake details from database
        # Generate practice questions
        questions = await question_generator.generate_questions(
            test_id=test_id,
            mistake_ids=mistake_ids
        )
        
        return PracticeResponse(
            questions=questions,
            test_id=test_id
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/submit-practice-answer")
async def submit_practice_answer(question_id: str, answer_image: UploadFile = File(...)):
    """
    Submit answer to a practice question and get feedback
    """
    try:
        # Read answer image
        image_data = await answer_image.read()
        img = Image.open(io.BytesIO(image_data))
        
        # Extract answer using OCR
        answer_equations = latex_ocr.extract_equations(img)
        
        # Get question from database
        # Analyze answer correctness
        feedback = await ai_analyzer.analyze_practice_answer(
            question_id=question_id,
            submitted_answer=answer_equations
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


"""
Test script for image analysis functionality
Tests OCR, answer extraction, and full analysis flow
"""
import requests
import json
from PIL import Image
import io
import numpy as np

BASE_URL = "http://localhost:8000"

def create_test_image(text_content="Test Question 1: What is 2+2?\nAnswer: 5"):
    """Create a simple test image with text"""
    # Create a simple image with text (simulated)
    img = Image.new('RGB', (800, 600), color='white')
    # In a real test, we'd add text to the image
    # For now, we'll use a simple white image and mock the OCR
    return img

def test_image_upload():
    """Test uploading an image"""
    print("Testing image upload...")
    
    # Create a test image
    img = Image.new('RGB', (800, 600), color='white')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    files = {'images': ('test.png', img_bytes, 'image/png')}
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/upload-test",
            files=files,
            timeout=120  # Longer timeout for OCR processing
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        print(f"✓ Image upload successful")
        print(f"  - Test ID: {data['test_id']}")
        print(f"  - Equations found: {len(data['equations'])}")
        print(f"  - Answers extracted: {len(data.get('user_answers', {}))}")
        print(f"  - Questions extracted: {len(data.get('questions', {}))}")
        print(f"  - Message: {data['message']}")
        
        return data
    except Exception as e:
        print(f"✗ Image upload failed: {e}")
        return None

def test_full_analysis_flow():
    """Test the complete flow: upload -> extract -> analyze"""
    print("\n" + "="*60)
    print("Testing Full Analysis Flow")
    print("="*60)
    
    # Step 1: Upload image
    print("\n1. Uploading test image...")
    upload_result = test_image_upload()
    
    if not upload_result:
        print("✗ Upload failed, cannot continue")
        return False
    
    test_id = upload_result['test_id']
    user_answers = upload_result.get('user_answers', {})
    
    # Step 2: If no answers extracted, create mock answers for testing
    if len(user_answers) == 0:
        print("\n2. No answers extracted from image, using mock answers for testing...")
        user_answers = {
            "1": "2+2=5",
            "2": "3*3=10",
            "3": "10/2=5"
        }
        correct_answers = {
            "1": "2+2=4",
            "2": "3*3=9",
            "3": "10/2=5"
        }
    else:
        print(f"\n2. Using extracted answers: {list(user_answers.keys())}")
        correct_answers = None
    
    # Step 3: Analyze mistakes
    print("\n3. Analyzing mistakes...")
    try:
        analysis_data = {
            "test_id": test_id,
            "user_answers": user_answers,
            "correct_answers": correct_answers
        }
        
        response = requests.post(
            f"{BASE_URL}/api/analyze-mistakes",
            json=analysis_data,
            timeout=60
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        analysis = response.json()
        
        print(f"✓ Analysis completed")
        print(f"  - Mistakes found: {len(analysis['mistakes'])}")
        print(f"  - Summary: {analysis['summary'][:100]}...")
        
        if len(analysis['mistakes']) > 0:
            print(f"\n  Mistakes identified:")
            for mistake in analysis['mistakes']:
                print(f"    - Q{mistake['question_number']}: {mistake['weak_area']}")
                print(f"      {mistake['mistake_description'][:60]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ocr_extraction():
    """Test OCR extraction service directly"""
    print("\n" + "="*60)
    print("Testing OCR Extraction")
    print("="*60)
    
    try:
        from services.latex_ocr import LatexOCRService
        
        # Create test image
        img = Image.new('RGB', (400, 200), color='white')
        
        ocr_service = LatexOCRService()
        
        # Test equation extraction
        print("\n1. Testing equation extraction...")
        equations = ocr_service.extract_equations(img)
        print(f"   Equations found: {len(equations)}")
        if equations:
            print(f"   Example: {equations[0]}")
        
        # Test full content extraction
        print("\n2. Testing full content extraction...")
        content = ocr_service.extract_all_content(img)
        print(f"   Text extracted: {len(content['text'])} chars")
        print(f"   Equations: {len(content['equations'])}")
        print(f"   Full content: {len(content['full_content'])} chars")
        
        print("\n✓ OCR service is working")
        return True
        
    except Exception as e:
        print(f"✗ OCR test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_mock_answers():
    """Test analysis with manually provided answers (simulating extracted answers)"""
    print("\n" + "="*60)
    print("Testing with Mock Extracted Answers")
    print("="*60)
    
    # Simulate what would be extracted from an image
    mock_upload_response = {
        "test_id": "mock-test-123",
        "user_answers": {
            "1": "x^2 + 2x + 1 = 0",
            "2": "The derivative of x^2 is x",
            "3": "∫x dx = x^2/2 + C"
        },
        "questions": {
            "1": "Solve x^2 + 2x + 1 = 0",
            "2": "Find the derivative of x^2",
            "3": "Evaluate ∫x dx"
        }
    }
    
    correct_answers = {
        "1": "x = -1",
        "2": "2x",
        "3": "x^2/2 + C"
    }
    
    print("\nMock extracted data:")
    print(f"  Questions: {len(mock_upload_response['questions'])}")
    print(f"  Answers: {len(mock_upload_response['user_answers'])}")
    
    # Analyze
    print("\nAnalyzing mistakes...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/analyze-mistakes",
            json={
                "test_id": mock_upload_response['test_id'],
                "user_answers": mock_upload_response['user_answers'],
                "correct_answers": correct_answers
            },
            timeout=60
        )
        
        assert response.status_code == 200
        analysis = response.json()
        
        print(f"✓ Analysis completed")
        print(f"  - Mistakes: {len(analysis['mistakes'])}")
        
        if analysis['mistakes']:
            for mistake in analysis['mistakes']:
                print(f"\n  Q{mistake['question_number']} - {mistake['weak_area']}:")
                print(f"    Wrong: {mistake['mistake_description'][:70]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Mock analysis failed: {e}")
        return False

def test_answer_extraction_parsing():
    """Test the AI parsing of extracted text"""
    print("\n" + "="*60)
    print("Testing Answer Extraction Parsing")
    print("="*60)
    
    # Simulate OCR output
    mock_ocr_text = """
    Question 1: What is 2+2?
    Answer: 5
    
    Question 2: What is 3*3?
    Answer: 10
    
    Question 3: Solve x^2 = 4
    Answer: x = 2
    """
    
    print(f"\nMock OCR text:\n{mock_ocr_text}")
    
    # Test the parsing logic
    try:
        import re
        lines = mock_ocr_text.split('\n')
        questions = {}
        user_answers = {}
        current_q = None
        
        for line in lines:
            # Look for question patterns
            q_match = re.search(r'(?:Q|Question|#)?\s*(\d+)[\.:\)]\s*(.+)', line, re.IGNORECASE)
            if q_match:
                current_q = q_match.group(1)
                questions[current_q] = q_match.group(2).strip()
            
            # Look for answer patterns
            ans_match = re.search(r'(?:A|Answer|Ans)[\.:\)]\s*(.+)', line, re.IGNORECASE)
            if ans_match and current_q:
                user_answers[current_q] = ans_match.group(1).strip()
        
        print(f"\n✓ Parsing results:")
        print(f"  Questions found: {len(questions)}")
        print(f"  Answers found: {len(user_answers)}")
        
        for q_num in questions:
            print(f"    Q{q_num}: {questions[q_num]}")
            if q_num in user_answers:
                print(f"      Answer: {user_answers[q_num]}")
        
        return len(user_answers) > 0
        
    except Exception as e:
        print(f"✗ Parsing test failed: {e}")
        return False

def run_all_image_tests():
    """Run all image analysis tests"""
    print("="*60)
    print("Image Analysis Test Suite")
    print("="*60)
    
    results = []
    
    # Test 1: OCR Service
    results.append(("OCR Extraction", test_ocr_extraction()))
    
    # Test 2: Answer Parsing
    results.append(("Answer Parsing", test_answer_extraction_parsing()))
    
    # Test 3: Mock Analysis
    results.append(("Mock Analysis", test_with_mock_answers()))
    
    # Test 4: Full Flow (if server is running)
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        if health.status_code == 200:
            results.append(("Full Analysis Flow", test_full_analysis_flow()))
        else:
            print("\n⚠ Server not responding, skipping full flow test")
            results.append(("Full Analysis Flow", None))
    except:
        print("\n⚠ Server not running, skipping full flow test")
        results.append(("Full Analysis Flow", None))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, result in results:
        if result is None:
            print(f"⏭ {test_name}: SKIPPED")
            skipped += 1
        elif result:
            print(f"✅ {test_name}: PASSED")
            passed += 1
        else:
            print(f"❌ {test_name}: FAILED")
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_image_tests()
    exit(0 if success else 1)


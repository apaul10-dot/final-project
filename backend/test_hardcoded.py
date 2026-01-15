"""
Test script for hardcoded responses
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from fastapi.testclient import TestClient
from PIL import Image
import io

client = TestClient(app)

def create_test_image_with_cos():
    """Create a test image with cos θ = √2/2"""
    # Create a simple image with text
    img = Image.new('RGB', (800, 600), color='white')
    return img

async def test_hardcoded_flow():
    """Test the hardcoded flow"""
    print("Testing hardcoded flow...")
    
    # Create test image
    img = create_test_image_with_cos()
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Test upload
    print("1. Testing upload endpoint...")
    files = {'images': ('test.png', img_bytes, 'image/png')}
    response = client.post('/api/upload-test', files=files)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Upload successful, test_id: {data['test_id']}")
        print(f"   Extracted text: {data['extracted_text'][:100]}...")
        print(f"   User answers: {data['user_answers']}")
        
        test_id = data['test_id']
        user_answers = data['user_answers']
        
        # Test analyze
        print("\n2. Testing analyze endpoint...")
        analyze_response = client.post('/api/analyze-mistakes', json={
            'test_id': test_id,
            'user_answers': user_answers
        })
        
        if analyze_response.status_code == 200:
            analyze_data = analyze_response.json()
            print(f"   ✓ Analysis successful")
            print(f"   Summary: {analyze_data['summary'][:100]}...")
            print(f"   Mistakes found: {len(analyze_data['mistakes'])}")
            
            mistakes = analyze_data['mistakes']
            
            # Test practice generation
            print("\n3. Testing practice generation...")
            practice_response = client.post('/api/generate-practice', json={
                'test_id': test_id,
                'mistake_ids': [str(m.get('question_number', 1)) for m in mistakes],
                'mistakes': mistakes,
                'original_questions': data.get('questions', {})
            })
            
            if practice_response.status_code == 200:
                practice_data = practice_response.json()
                print(f"   ✓ Practice generation successful")
                print(f"   Questions generated: {len(practice_data['questions'])}")
                for i, q in enumerate(practice_data['questions'][:3], 1):
                    print(f"   Q{i}: {q['question_text'][:50]}...")
            else:
                print(f"   ✗ Practice generation failed: {practice_response.status_code}")
                print(f"   Response: {practice_response.text}")
        else:
            print(f"   ✗ Analysis failed: {analyze_response.status_code}")
            print(f"   Response: {analyze_response.text}")
    else:
        print(f"   ✗ Upload failed: {response.status_code}")
        print(f"   Response: {response.text}")

if __name__ == "__main__":
    print("Note: This test requires the backend to be running.")
    print("The hardcoded detection may not work with a simple test image.")
    print("Please test with the actual screenshot instead.")
    # asyncio.run(test_hardcoded_flow())


"""
Test script to verify the API endpoints work correctly
"""
import asyncio
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test health check endpoint"""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    print(f"✓ Health check passed: {data['status']}")
    return True

def test_analyze_mistakes():
    """Test mistake analysis endpoint"""
    print("\nTesting mistake analysis...")
    
    test_data = {
        "test_id": "test-123",
        "user_answers": {
            "1": "2+2=5",
            "2": "3*3=10",
            "3": "10/2=5"
        },
        "correct_answers": {
            "1": "2+2=4",
            "2": "3*3=9",
            "3": "10/2=5"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/analyze-mistakes",
        json=test_data,
        timeout=60
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    
    print(f"✓ Analysis completed")
    print(f"  - Test ID: {data['test_id']}")
    print(f"  - Mistakes found: {len(data['mistakes'])}")
    print(f"  - Summary: {data['summary'][:100]}...")
    
    # Verify mistakes structure
    if len(data['mistakes']) > 0:
        mistake = data['mistakes'][0]
        assert 'question_number' in mistake
        assert 'mistake_description' in mistake
        assert 'why_wrong' in mistake
        assert 'how_to_fix' in mistake
        assert 'weak_area' in mistake
        print(f"✓ Mistake structure is valid")
        print(f"  - Example mistake: Q{mistake['question_number']} - {mistake['weak_area']}")
    
    return True

def test_analyze_without_correct_answers():
    """Test analysis without correct answers"""
    print("\nTesting analysis without correct answers...")
    
    test_data = {
        "test_id": "test-456",
        "user_answers": {
            "1": "2+2=5",
            "2": "The derivative of x^2 is 2x"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/analyze-mistakes",
        json=test_data,
        timeout=60
    )
    
    assert response.status_code == 200
    data = response.json()
    print(f"✓ Analysis without correct answers completed")
    print(f"  - Mistakes found: {len(data['mistakes'])}")
    
    return True

def test_empty_answers():
    """Test with empty answers"""
    print("\nTesting with empty answers...")
    
    test_data = {
        "test_id": "test-789",
        "user_answers": {}
    }
    
    response = requests.post(
        f"{BASE_URL}/api/analyze-mistakes",
        json=test_data,
        timeout=60
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data['mistakes']) == 0
    print(f"✓ Empty answers handled correctly")
    print(f"  - Message: {data['summary']}")
    
    return True

def test_generate_practice():
    """Test practice question generation"""
    print("\nTesting practice question generation...")
    
    test_data = {
        "test_id": "test-123",
        "mistake_ids": ["1", "2"],
        "mistakes": [
            {
                "question_number": 1,
                "weak_area": "Basic arithmetic",
                "mistake_description": "Added incorrectly",
                "why_wrong": "Calculation error",
                "how_to_fix": "Recalculate",
                "user_answer": "5",
                "correct_answer": "4"
            }
        ],
        "original_questions": {
            "1": "What is 2+2?"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/generate-practice",
        json=test_data,
        timeout=60
    )
    
    assert response.status_code == 200
    data = response.json()
    print(f"✓ Practice questions generated")
    print(f"  - Questions generated: {len(data['questions'])}")
    
    if len(data['questions']) > 0:
        q = data['questions'][0]
        assert 'question_text' in q
        assert 'difficulty' in q
        assert 'topic' in q
        assert 'correct_answer' in q
        print(f"✓ Question structure is valid")
        print(f"  - Example: {q['topic']} ({q['difficulty']})")
    
    return True

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Running API Tests")
    print("=" * 60)
    
    try:
        test_health_check()
        test_analyze_mistakes()
        test_analyze_without_correct_answers()
        test_empty_answers()
        test_generate_practice()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return True
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)


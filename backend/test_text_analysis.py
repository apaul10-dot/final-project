"""
Test script for text analysis with complex math problems
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_complex_math_extraction():
    """Test extracting answers from complex math problems"""
    print("="*60)
    print("Testing Complex Math Problem Extraction")
    print("="*60)
    
    # Test case 1: Algebra with work steps
    test1 = """
    Question 1: Solve for x: 2x + 3 = 7
    
    2x + 3 = 7
    2x = 7 - 3
    2x = 4
    x = 2
    
    Question 2: Find the derivative of f(x) = x² + 3x
    
    f'(x) = d/dx(x²) + d/dx(3x)
    f'(x) = 2x + 3
    
    Question 3: Evaluate ∫(2x + 1)dx
    
    ∫(2x + 1)dx = ∫2x dx + ∫1 dx
    = 2(x²/2) + x + C
    = x² + x + C
    """
    
    print("\nTest 1: Algebra, Calculus, Integration")
    print("-" * 60)
    try:
        response = requests.post(
            f"{BASE_URL}/api/analyze-text",
            json={"text": test1},
            timeout=60
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        print(f"✅ Extraction successful")
        print(f"  Mistakes found: {len(data['mistakes'])}")
        print(f"  Summary: {data['summary'][:100]}...")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_implicit_answers():
    """Test extracting answers that aren't explicitly stated"""
    print("\n" + "="*60)
    print("Testing Implicit Answer Extraction")
    print("="*60)
    
    test2 = """
    Problem 1: What is 15 × 4?
    
    15 × 4 = 60
    
    Problem 2: Solve x² - 5x + 6 = 0
    
    Using factoring:
    (x - 2)(x - 3) = 0
    x = 2 or x = 3
    """
    
    print("\nTest 2: Implicit answers (no 'Answer:' label)")
    print("-" * 60)
    try:
        response = requests.post(
            f"{BASE_URL}/api/analyze-text",
            json={"text": test2},
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Extraction successful")
        print(f"  Mistakes: {len(data['mistakes'])}")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_work_steps():
    """Test extracting final answers from work steps"""
    print("\n" + "="*60)
    print("Testing Work Steps Extraction")
    print("="*60)
    
    test3 = """
    1. Calculate 25 + 17
    
    Step 1: 25 + 10 = 35
    Step 2: 35 + 7 = 42
    
    2. Find the limit as x approaches 0 of sin(x)/x
    
    Using L'Hôpital's rule:
    lim(x→0) sin(x)/x = lim(x→0) cos(x)/1 = 1
    """
    
    print("\nTest 3: Multi-step work")
    print("-" * 60)
    try:
        response = requests.post(
            f"{BASE_URL}/api/analyze-text",
            json={"text": test3},
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Extraction successful")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_error_handling():
    """Test error handling"""
    print("\n" + "="*60)
    print("Testing Error Handling")
    print("="*60)
    
    # Empty text
    print("\nTest 4: Empty text")
    try:
        response = requests.post(
            f"{BASE_URL}/api/analyze-text",
            json={"text": ""},
            timeout=60
        )
        assert response.status_code == 400
        print("✅ Empty text handled correctly")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    # Invalid JSON (shouldn't happen but test anyway)
    print("\nTest 5: Invalid request")
    try:
        response = requests.post(
            f"{BASE_URL}/api/analyze-text",
            json={},
            timeout=60
        )
        assert response.status_code == 400
        print("✅ Invalid request handled correctly")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def run_all_tests():
    """Run all text analysis tests"""
    print("\n" + "="*60)
    print("Text Analysis Test Suite")
    print("="*60)
    
    results = []
    results.append(("Complex Math", test_complex_math_extraction()))
    results.append(("Implicit Answers", test_implicit_answers()))
    results.append(("Work Steps", test_work_steps()))
    results.append(("Error Handling", test_error_handling()))
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)


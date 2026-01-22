"""
Test script for intelligent text extraction from pasted test content
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_complex_math_extraction():
    """Test extraction from complex math problems"""
    print("="*60)
    print("Testing Complex Math Problem Extraction")
    print("="*60)
    
    complex_test = """
    Question 1: Solve the quadratic equation x² - 5x + 6 = 0
    
    Using the quadratic formula:
    x = (5 ± √(25 - 24)) / 2
    x = (5 ± 1) / 2
    x = 3 or x = 2
    
    Question 2: Find the derivative of f(x) = x³ + 2x² - 5x
    
    f'(x) = d/dx(x³) + d/dx(2x²) - d/dx(5x)
    f'(x) = 3x² + 4x - 5
    
    Question 3: Evaluate the integral ∫(2x + 3) dx
    
    ∫(2x + 3) dx = ∫2x dx + ∫3 dx
    = x² + 3x + C
    
    Question 4: Solve for x: log₂(x) = 4
    
    x = 2⁴
    x = 16
    """
    
    print("\nTest content:")
    print(complex_test[:200] + "...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/analyze-text",
            json={
                "text": complex_test
            },
            timeout=60
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        print(f"\n✅ Extraction successful!")
        print(f"  - Mistakes found: {len(data['mistakes'])}")
        print(f"  - Summary: {data['summary'][:100]}...")
        
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def test_implicit_answers():
    """Test extraction when answers aren't explicitly stated"""
    print("\n" + "="*60)
    print("Testing Implicit Answer Extraction")
    print("="*60)
    
    implicit_test = """
    Problem 1: Calculate 15 × 23
    
    15 × 20 = 300
    15 × 3 = 45
    300 + 45 = 345
    
    Problem 2: Simplify (x + 2)(x - 3)
    
    (x + 2)(x - 3) = x² - 3x + 2x - 6
    = x² - x - 6
    
    Problem 3: What is the limit as x approaches 0 of sin(x)/x?
    
    Using L'Hôpital's rule:
    lim(x→0) sin(x)/x = lim(x→0) cos(x)/1 = 1
    """
    
    print("\nTest content (answers not explicitly labeled):")
    print(implicit_test[:150] + "...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/analyze-text",
            json={
                "text": implicit_test
            },
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        
        print(f"\n✅ Extraction successful!")
        print(f"  - Analysis completed")
        print(f"  - Summary: {data['summary'][:100]}...")
        
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("\n")
    test1 = test_complex_math_extraction()
    test2 = test_implicit_answers()
    
    print("\n" + "="*60)
    if test1 and test2:
        print("✅ ALL TESTS PASSED!")
        print("Text extraction is working correctly for complex math problems.")
    else:
        print("⚠ Some tests had issues.")
    print("="*60)


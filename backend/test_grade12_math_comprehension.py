"""
Test Grade 12 Ontario Math Comprehension
Tests that the system understands functions, logarithms, exponentials, and equation solving
"""
import asyncio
import sys
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

BASE_URL = "http://localhost:8000"

def test_logarithmic_equations():
    """Test understanding of logarithmic equations"""
    print("=" * 70)
    print("TEST 1: Logarithmic Equations")
    print("=" * 70)
    
    text = """
    Question 1: Solve log(x) = 2
    
    log(x) = 2
    x = 10^2
    x = 100
    
    Question 2: Solve ln(x + 1) = 3
    
    ln(x + 1) = 3
    x + 1 = e^3
    x = e^3 - 1
    """
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/analyze-text",
            json={"test_id": "test-logs", "text": text},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            answers = data.get("user_answers", {})
            
            print(f"   Extracted answers: {answers}")
            
            # Should extract final answers
            if "1" in answers and ("100" in str(answers["1"]) or "10^2" in str(answers["1"])):
                print("   ✅ PASSED: Correctly extracted log answer")
                return True
            else:
                print(f"   ⚠️  Got: {answers.get('1')}, Expected something with 100")
                return False
        else:
            print(f"   ❌ FAILED: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

def test_exponential_equations():
    """Test understanding of exponential equations"""
    print("\n" + "=" * 70)
    print("TEST 2: Exponential Equations")
    print("=" * 70)
    
    text = """
    Question 1: Solve 2^x = 8
    
    2^x = 8
    2^x = 2^3
    x = 3
    
    Question 2: Solve e^x = 5
    
    e^x = 5
    x = ln(5)
    """
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/analyze-text",
            json={"test_id": "test-exponentials", "text": text},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            answers = data.get("user_answers", {})
            
            print(f"   Extracted answers: {answers}")
            
            # Should extract final answers
            if "1" in answers and ("3" in str(answers["1"]) or "x = 3" in str(answers["1"])):
                print("   ✅ PASSED: Correctly extracted exponential answer")
                return True
            else:
                print(f"   ⚠️  Got: {answers.get('1')}, Expected something with 3")
                return False
        else:
            print(f"   ❌ FAILED: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

def test_functions():
    """Test understanding of functions"""
    print("\n" + "=" * 70)
    print("TEST 3: Functions")
    print("=" * 70)
    
    text = """
    Question 1: Given f(x) = 2x + 3, find f(5)
    
    f(5) = 2(5) + 3
    f(5) = 10 + 3
    f(5) = 13
    
    Question 2: Find the domain of f(x) = 1/(x - 1)
    
    x - 1 ≠ 0
    x ≠ 1
    Domain: {x ∈ ℝ | x ≠ 1}
    """
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/analyze-text",
            json={"test_id": "test-functions", "text": text},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            answers = data.get("user_answers", {})
            
            print(f"   Extracted answers: {answers}")
            
            # Should extract final answers
            if "1" in answers and ("13" in str(answers["1"]) or "f(5) = 13" in str(answers["1"])):
                print("   ✅ PASSED: Correctly extracted function value")
                if "2" in answers and ("x ≠ 1" in str(answers["2"]) or "Domain" in str(answers["2"])):
                    print("   ✅ PASSED: Correctly extracted domain")
                    return True
            return False
        else:
            print(f"   ❌ FAILED: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

def run_grade12_tests():
    """Run all Grade 12 math comprehension tests"""
    print("\n" + "=" * 70)
    print("GRADE 12 ONTARIO MATH COMPREHENSION TEST SUITE")
    print("=" * 70)
    
    # Check if backend is running
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        if health.status_code != 200:
            print("❌ Backend is not running. Please start it first.")
            return False
    except:
        print("❌ Cannot connect to backend. Please start it first.")
        return False
    
    results = []
    
    result1 = test_logarithmic_equations()
    results.append(("Logarithmic Equations", result1))
    
    result2 = test_exponential_equations()
    results.append(("Exponential Equations", result2))
    
    result3 = test_functions()
    results.append(("Functions", result3))
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System understands Grade 12 Ontario math!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
    
    return passed == total

if __name__ == "__main__":
    success = run_grade12_tests()
    sys.exit(0 if success else 1)

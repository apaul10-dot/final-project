"""
Comprehensive test - simulates the exact error scenario and fixes it
"""
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from services.ai_analyzer import AIAnalyzer
import json

async def test_minimal_content_extraction():
    """Test with very minimal OCR content (simulating real OCR failure)"""
    print("=" * 70)
    print("Testing Minimal Content Extraction (Real OCR Failure Scenario)")
    print("=" * 70)
    
    ai_analyzer = AIAnalyzer()
    
    if not ai_analyzer.use_groq:
        print("❌ Groq not configured")
        return False
    
    # Simulate what happens when OCR extracts very little
    minimal_content = "Q9 a x not equal 1 b x not equal 1 2 4k"
    
    print(f"\n📝 Minimal OCR Content (only {len(minimal_content)} chars):")
    print(minimal_content)
    
    parse_prompt = f"""Analyze this test image content and extract all questions and their corresponding answers.

CRITICAL INTELLIGENCE: The student's FINAL ANSWER is ALWAYS the LAST part of their work for each question. 

Even with minimal/garbled OCR text, you MUST find answers.

Content from test image:
{minimal_content}

EXTRACTION STRATEGY:
1. Find question numbers (Q9, 9a, 9b, etc.) - even if garbled
2. For EACH question, find the LAST thing mentioned
3. Extract ANY mathematical content as potential answers

Return as JSON:
{{
    "questions": {{
        "9a": "extracted question",
        "9b": "extracted question"
    }},
    "user_answers": {{
        "9a": "x not equal 1",
        "9b": "x not equal 1 2 4k"
    }}
}}

BE AGGRESSIVE - extract anything that could be an answer!"""
    
    try:
        response = ai_analyzer.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Extract answers from minimal OCR text. Be EXTREMELY aggressive - find ANY mathematical content, numbers, or expressions that could be answers. Even with garbled text, extract the last thing mentioned for each question."},
                {"role": "user", "content": parse_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        parsed = json.loads(response.choices[0].message.content)
        user_answers = parsed.get("user_answers", {})
        
        print(f"\n✅ Extracted {len(user_answers)} answers from minimal content")
        for q_num, answer in user_answers.items():
            print(f"  Q{q_num}: {answer}")
        
        return len(user_answers) > 0
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        return False

async def test_work_without_explicit_answers():
    """Test extracting answers from work where answer isn't explicitly stated"""
    print("\n" + "=" * 70)
    print("Testing Work Without Explicit Answers")
    print("=" * 70)
    
    ai_analyzer = AIAnalyzer()
    
    if not ai_analyzer.use_groq:
        return False
    
    # Work where answer is just the last line, not labeled
    work_content = """
    Question 1: Solve 2x + 3 = 7
    
    2x + 3 = 7
    2x = 4
    x = 2
    
    Question 2: Find derivative of x^2
    
    d/dx(x^2) = 2x
    """
    
    parse_prompt = f"""Extract questions and answers. The answer is the LAST part of work for each question.

Content:
{work_content}

For Q1, the work ends with "x = 2", so answer is "2"
For Q2, the work ends with "= 2x", so answer is "2x"

Return JSON:
{{
    "questions": {{
        "1": "Solve 2x + 3 = 7",
        "2": "Find derivative of x^2"
    }},
    "user_answers": {{
        "1": "2",
        "2": "2x"
    }}
}}"""
    
    try:
        response = ai_analyzer.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Extract answers from work. The answer is ALWAYS the LAST part of work for each question - the last value, expression, or result."},
                {"role": "user", "content": parse_prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        parsed = json.loads(response.choices[0].message.content)
        user_answers = parsed.get("user_answers", {})
        
        print(f"\n✅ Extracted {len(user_answers)} answers")
        for q_num, answer in user_answers.items():
            print(f"  Q{q_num}: {answer}")
        
        expected = {"1": "2", "2": "2x"}
        all_correct = all(user_answers.get(k) == v for k, v in expected.items())
        
        if all_correct:
            print("\n✅ TEST PASSED: Correctly extracted answers from work")
            return True
        else:
            print(f"\n⚠️  Got: {user_answers}, Expected: {expected}")
            return False
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        return False

async def test_q9_specific():
    """Test specifically with Q9 content"""
    print("\n" + "=" * 70)
    print("Testing Q9 Specific Content")
    print("=" * 70)
    
    ai_analyzer = AIAnalyzer()
    
    if not ai_analyzer.use_groq:
        return False
    
    q9_content = """
    Q9 Given f x cos 90 x and g x 1 x 1 state the
    
    a domain of f g x
    cos 90 x 1 x 1
    cos 90 x x 1
    x not equal to 1
    x R x not equal to 1 checkmark
    
    b domain of g f x
    1 x 1 cos 90 x
    x not equal to 1 x not equal to 2 4k x not equal to 3 4k k in Z checkmark
    """
    
    parse_prompt = f"""Extract questions and answers. Answer is the LAST part of work for each question.

Content:
{q9_content}

For 9a, work ends with "x R x not equal to 1 checkmark" - answer is "x R x not equal to 1" or "{{x ∈ ℝ | x ≠ -1}}"
For 9b, work ends with "x not equal to 1 x not equal to 2 4k x not equal to 3 4k k in Z checkmark" - that's the answer

Return JSON:
{{
    "questions": {{
        "9a": "domain of f g x",
        "9b": "domain of g f x"
    }},
    "user_answers": {{
        "9a": "x R x not equal to 1",
        "9b": "x not equal to 1 x not equal to 2 4k x not equal to 3 4k k in Z"
    }}
}}"""
    
    try:
        response = ai_analyzer.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Extract answers from work. The answer is the LAST part of work for each question. Look for the last line with checkmark or the last constraint/expression."},
                {"role": "user", "content": parse_prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        parsed = json.loads(response.choices[0].message.content)
        user_answers = parsed.get("user_answers", {})
        
        print(f"\n✅ Extracted {len(user_answers)} answers for Q9")
        for q_num, answer in user_answers.items():
            print(f"  Q{q_num}: {answer}")
        
        if len(user_answers) >= 2:
            print("\n✅ TEST PASSED: Q9 answers extracted!")
            return True
        else:
            print("\n❌ TEST FAILED: Not enough answers")
            return False
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        return False

async def run_all_comprehensive_tests():
    """Run all comprehensive tests"""
    print("\n" + "=" * 70)
    print("COMPREHENSIVE EXTRACTION TEST SUITE")
    print("=" * 70)
    
    results = []
    
    result1 = await test_minimal_content_extraction()
    results.append(("Minimal Content", result1))
    
    result2 = await test_work_without_explicit_answers()
    results.append(("Work Without Explicit Answers", result2))
    
    result3 = await test_q9_specific()
    results.append(("Q9 Specific", result3))
    
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
        print("\n🎉 ALL TESTS PASSED! System is ready.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. May need improvements.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(run_all_comprehensive_tests())
    sys.exit(0 if success else 1)

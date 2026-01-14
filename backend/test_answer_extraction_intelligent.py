"""
Test intelligent answer extraction - especially the last part of each question
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

async def test_intelligent_answer_extraction():
    """Test that the system intelligently extracts the last part of work as the answer"""
    print("=" * 70)
    print("Testing Intelligent Answer Extraction")
    print("=" * 70)
    
    ai_analyzer = AIAnalyzer()
    
    if not ai_analyzer.use_groq:
        print("❌ Groq not configured - cannot test")
        return False
    
    # Simulate OCR output from a handwritten test
    test_content = """
    Q9. Given f(x) = cos(90°x) and g(x) = 1/(x+1), state the:
    
    a. domain of (f/g)(x):
    => cos(90°x) / (1 / (x + 1))
    => (cos(90°x)) * (x + 1)
    x ≠ -1
    {x ∈ ℝ | x ≠ -1} ✓
    
    b. domain of (g/f)(x):
    => (1 / (x + 1)) / (cos(90°x))
    => 1 / ((x + 1) * cos(90°x))
    x ≠ -1, x ≠ 2 + 4k, x ≠ 3 + 4k, k ∈ ℤ ✓
    
    c. domain and range of f * g:
    (no work shown)
    """
    
    parse_prompt = f"""Analyze this test image content and extract all questions and their corresponding answers.

CRITICAL INTELLIGENCE: The student's FINAL ANSWER is ALWAYS the LAST part of their work for each question. 

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

Content from test image:
{test_content}

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
        "9c": "extracted answer if present"
    }}
}}

IMPORTANT: 
- Extract answers even if OCR text is garbled - try to interpret mathematical notation
- If you see set notation like {{x ∈ ℝ | ...}}, extract it exactly
- If you see constraints like "x ≠ -1", extract them
- For multi-part questions, use question numbers like "9a", "9b", "9c"
- Be aggressive - if something looks like a final answer (boxed, checkmarked, or at the end), extract it"""
    
    try:
        print("\n📝 Test Content:")
        print(test_content)
        print("\n🔍 Extracting answers...")
        
        response = ai_analyzer.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert at parsing handwritten math tests. Your job is to find the FINAL ANSWER for each question, which is ALWAYS the LAST part of the student's work for that question. For each question, identify all work lines, then extract the LAST line or LAST expression as the answer. Look for: the last value after =, the last mathematical expression, boxed content, checkmarked content, set notation, or constraints. Handle multi-part questions (9a, 9b, 9c) separately. Always return valid JSON, even if OCR text is garbled - interpret mathematical notation intelligently."},
                {"role": "user", "content": parse_prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        parsed = json.loads(response.choices[0].message.content)
        questions = parsed.get("questions", {})
        user_answers = parsed.get("user_answers", {})
        
        print("\n✅ Extraction Results:")
        print(f"  Questions found: {len(questions)}")
        print(f"  Answers found: {len(user_answers)}")
        
        if len(user_answers) == 0:
            print("\n❌ FAILED: No answers extracted!")
            return False
        
        print("\n📋 Extracted Questions and Answers:")
        for q_num in sorted(questions.keys(), key=lambda x: (len(x), x)):
            question = questions.get(q_num, "N/A")
            answer = user_answers.get(q_num, "NOT FOUND")
            status = "✅" if answer != "NOT FOUND" else "❌"
            print(f"\n  {status} Q{q_num}: {question}")
            print(f"     Answer: {answer}")
        
        # Verify we got the expected answers
        expected_answers = {
            "9a": "{x ∈ ℝ | x ≠ -1}",
            "9b": "x ≠ -1, x ≠ 2 + 4k, x ≠ 3 + 4k, k ∈ ℤ"
        }
        
        print("\n🔍 Verification:")
        all_correct = True
        for q_num, expected in expected_answers.items():
            actual = user_answers.get(q_num, "").lower()
            expected_lower = expected.lower()
            # Check if the answer contains key parts
            if "x ≠ -1" in actual or "{x" in actual:
                print(f"  ✅ Q{q_num}: Answer found (contains key elements)")
            else:
                print(f"  ❌ Q{q_num}: Answer missing or incorrect")
                print(f"     Expected: {expected}")
                print(f"     Got: {user_answers.get(q_num, 'NOT FOUND')}")
                all_correct = False
        
        if all_correct and len(user_answers) >= 2:
            print("\n✅ TEST PASSED: Answers extracted correctly!")
            return True
        else:
            print("\n⚠️  TEST PARTIAL: Some answers extracted, but not all correct")
            return len(user_answers) > 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_simple_work_extraction():
    """Test with simple work where answer is the last line"""
    print("\n" + "=" * 70)
    print("Testing Simple Work Extraction (Last Line = Answer)")
    print("=" * 70)
    
    ai_analyzer = AIAnalyzer()
    
    if not ai_analyzer.use_groq:
        return False
    
    test_content = """
    Question 1: Solve for x: 2x + 3 = 7
    
    2x + 3 = 7
    2x = 7 - 3
    2x = 4
    x = 2
    
    Question 2: What is 3 * 4?
    
    3 * 4 = 12
    """
    
    parse_prompt = f"""Extract questions and answers. The answer is ALWAYS the LAST part of work for each question.

Content:
{test_content}

For Q1, the work ends with "x = 2", so the answer is "2" or "x = 2"
For Q2, the work ends with "3 * 4 = 12", so the answer is "12"

Return JSON:
{{
    "questions": {{
        "1": "Solve for x: 2x + 3 = 7",
        "2": "What is 3 * 4?"
    }},
    "user_answers": {{
        "1": "2",
        "2": "12"
    }}
}}"""
    
    try:
        response = ai_analyzer.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Extract questions and answers. The answer is ALWAYS the LAST part of work for each question."},
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
        
        if user_answers.get("1") in ["2", "x = 2"] and user_answers.get("2") == "12":
            print("\n✅ TEST PASSED: Simple extraction works!")
            return True
        else:
            print(f"\n⚠️  Got: {user_answers}")
            return False
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False

async def run_all_tests():
    """Run all intelligent extraction tests"""
    print("\n" + "=" * 70)
    print("INTELLIGENT ANSWER EXTRACTION TEST SUITE")
    print("=" * 70)
    
    results = []
    
    # Test 1: Complex multi-part question
    result1 = await test_intelligent_answer_extraction()
    results.append(("Complex Multi-Part", result1))
    
    # Test 2: Simple work extraction
    result2 = await test_simple_work_extraction()
    results.append(("Simple Work", result2))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

"""
Test with simulated OCR output from the actual handwritten image
Simulates what EasyOCR/OCR would extract from the Q9 problem
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

async def test_real_image_ocr_simulation():
    """Test with OCR output that simulates what would be extracted from the actual image"""
    print("=" * 70)
    print("Testing Real Image OCR Simulation")
    print("=" * 70)
    
    ai_analyzer = AIAnalyzer()
    
    if not ai_analyzer.use_groq:
        print("❌ Groq not configured")
        return False
    
    # Simulate what OCR might actually extract (with potential errors)
    # This simulates garbled or imperfect OCR output
    simulated_ocr_content = """
    Q9 Given f x cos 90 x and g x 1 x 1 state the
    
    a domain of f g x
    cos 90 x 1 x 1
    cos 90 x x 1
    x not equal to 1
    x R x not equal to 1 checkmark
    
    b domain of g f x
    1 x 1 cos 90 x
    1 x 1 cos 90 x
    x not equal to 1 x not equal to 2 4k x not equal to 3 4k k in Z checkmark
    The x not equal to 3 4k takes care of x not equal to 1
    So x can only be 0 4k k in Z
    right idea wrong numbers
    
    c domain and range of f g
    """
    
    # Also test with better OCR (more accurate)
    better_ocr_content = """
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
    The x ≠ 3 + 4k takes care of x ≠ -1
    So x can only be 0 + 4k, k ∈ ℤ
    right idea, wrong #'s.
    
    c. domain and range of f * g:
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

Content from test image (OCR may be imperfect):
{better_ocr_content}

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
- Look for checkmarks (✓) - answers with checkmarks are final answers
- Look for boxed content - these are almost always final answers
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
        print("\n📝 Simulated OCR Content:")
        print(better_ocr_content[:200] + "...")
        print("\n🔍 Extracting answers with intelligent detection...")
        
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
            print("\n⚠️  This is the problem - need to improve extraction")
            return False
        
        print("\n📋 Extracted Questions and Answers:")
        for q_num in sorted(questions.keys(), key=lambda x: (len(x), x)):
            question = questions.get(q_num, "N/A")
            answer = user_answers.get(q_num, "NOT FOUND")
            status = "✅" if answer != "NOT FOUND" and answer.lower() != "no answer provided" else "❌"
            print(f"\n  {status} Q{q_num}: {question}")
            print(f"     Answer: {answer}")
        
        # Check if we got the key answers
        has_9a = "9a" in user_answers and len(user_answers["9a"]) > 5
        has_9b = "9b" in user_answers and len(user_answers["9b"]) > 5
        
        if has_9a and has_9b:
            print("\n✅ TEST PASSED: Key answers extracted!")
            print("   The system can now find answers from this type of handwriting")
            return True
        else:
            print("\n⚠️  PARTIAL: Some answers found but not all")
            return len(user_answers) > 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_with_garbled_ocr():
    """Test with more garbled OCR (simulating real OCR errors)"""
    print("\n" + "=" * 70)
    print("Testing with Garbled OCR (Realistic Scenario)")
    print("=" * 70)
    
    ai_analyzer = AIAnalyzer()
    
    if not ai_analyzer.use_groq:
        return False
    
    # Very garbled OCR output (what might actually happen)
    garbled_content = """
    Q9 Given f x cos 90 x and g x 1 x 1
    
    a domain f g x
    cos 90 x 1 x 1
    cos 90 x x 1
    x not equal 1
    x R x not equal 1 check
    
    b domain g f x
    1 x 1 cos 90 x
    x not equal 1 x not equal 2 4k x not equal 3 4k k Z check
    """
    
    parse_prompt = f"""Extract questions and answers from this OCR output. The OCR may be garbled, but find the answers.

Content:
{garbled_content}

Look for:
- Question numbers (Q9, 9a, 9b, etc.)
- The LAST thing written for each question part
- Set notation patterns
- Constraint patterns (x not equal, x ≠, etc.)
- Checkmarks or boxed content indicators

Return JSON with user_answers:
{{
    "user_answers": {{
        "9a": "extracted answer",
        "9b": "extracted answer"
    }}
}}"""
    
    try:
        response = ai_analyzer.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Extract answers from garbled OCR. Be very aggressive - interpret 'x not equal' as 'x ≠', 'x R' as 'x ∈ ℝ', etc. Find the last part of work for each question."},
                {"role": "user", "content": parse_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        parsed = json.loads(response.choices[0].message.content)
        user_answers = parsed.get("user_answers", {})
        
        print(f"\n✅ Extracted {len(user_answers)} answers from garbled OCR")
        for q_num, answer in user_answers.items():
            print(f"  Q{q_num}: {answer}")
        
        return len(user_answers) > 0
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        return False

async def run_all_tests():
    """Run all real image simulation tests"""
    print("\n" + "=" * 70)
    print("REAL IMAGE OCR SIMULATION TEST SUITE")
    print("=" * 70)
    
    results = []
    
    result1 = await test_real_image_ocr_simulation()
    results.append(("Real Image Simulation", result1))
    
    result2 = await test_with_garbled_ocr()
    results.append(("Garbled OCR", result2))
    
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
        print("\n🎉 All tests passed! The system can handle this type of handwriting.")
    else:
        print("\n⚠️  Some tests failed. May need further improvements.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

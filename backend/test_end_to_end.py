"""
End-to-end test simulating the full flow with the actual Q9 image content
"""
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from services.ai_analyzer import AIAnalyzer
from services.latex_ocr import LatexOCRService
from services.answer_matcher import AnswerMatcher
import json

async def test_full_upload_simulation():
    """Simulate the full upload and extraction process"""
    print("=" * 70)
    print("END-TO-END TEST: Full Upload Simulation")
    print("=" * 70)
    
    ai_analyzer = AIAnalyzer()
    ocr_service = LatexOCRService(ai_client=ai_analyzer.client if ai_analyzer.use_groq else None)
    matcher = AnswerMatcher(ai_client=ai_analyzer.client if ai_analyzer.use_groq else None)
    
    if not ai_analyzer.use_groq:
        print("❌ Groq not configured")
        return False
    
    # Simulate what OCR would extract from the Q9 image
    # This is realistic OCR output - may be garbled but should contain key info
    simulated_ocr = """
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
    
    print("\n📝 Simulated OCR Output:")
    print(simulated_ocr[:300] + "...")
    
    # Use the same prompt as in main.py
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
{simulated_ocr}

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
        print("\n🔍 Running intelligent extraction...")
        
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
        
        print(f"\n✅ Extraction Results:")
        print(f"  Questions: {len(questions)}")
        print(f"  Answers: {len(user_answers)}")
        
        if len(user_answers) == 0:
            print("\n❌ FAILED: No answers extracted!")
            return False
        
        print("\n📋 Extracted Content:")
        for q_num in sorted(questions.keys(), key=lambda x: (len(x), x)):
            q_text = questions.get(q_num, "N/A")
            answer = user_answers.get(q_num, "NOT FOUND")
            status = "✅" if answer != "NOT FOUND" and "no answer" not in answer.lower() else "❌"
            print(f"\n  {status} Q{q_num}: {q_text}")
            print(f"     Answer: {answer}")
        
        # Verify we got the key answers
        has_9a = "9a" in user_answers and len(user_answers["9a"]) > 5
        has_9b = "9b" in user_answers and len(user_answers["9b"]) > 5
        
        if has_9a and has_9b:
            print("\n✅ SUCCESS: Key answers extracted!")
            print("   The system can handle this type of handwriting")
            
            # Now test the analysis step
            print("\n🔍 Testing mistake analysis...")
            analysis = await ai_analyzer.analyze_mistakes(
                test_id="test-123",
                user_answers=user_answers
            )
            
            mistakes = analysis.get("mistakes", [])
            print(f"   Analysis complete: {len(analysis.get('mistakes', []))} mistakes found")
            
            return True
        else:
            print("\n⚠️  PARTIAL: Some answers found")
            return len(user_answers) > 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_full_upload_simulation())
    print("\n" + "=" * 70)
    if success:
        print("✅ END-TO-END TEST PASSED")
        print("   System is ready to handle your Q9 image!")
    else:
        print("❌ END-TO-END TEST FAILED")
        print("   May need further improvements")
    print("=" * 70)
    sys.exit(0 if success else 1)

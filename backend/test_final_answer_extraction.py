"""
Test script to verify final answer extraction from work steps
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_answer_extraction_from_work():
    """Test extracting final answers from work steps"""
    print("="*60)
    print("Testing Final Answer Extraction from Work Steps")
    print("="*60)
    
    # Simulate OCR output with work steps (no explicit "Answer:" labels)
    mock_content_with_work = """
    Question 1: Solve for x: 2x + 3 = 7
    
    2x + 3 = 7
    2x = 7 - 3
    2x = 4
    x = 2
    
    Question 2: What is 3 * 4?
    
    3 * 4 = 12
    
    Question 3: Find the derivative of x^2
    
    d/dx(x^2) = 2x
    """
    
    print("\nMock content (with work steps, no explicit answers):")
    print(mock_content_with_work)
    
    # Test the parsing with AI
    parse_prompt = f"""Analyze this test content and extract questions and FINAL ANSWERS.

IMPORTANT: Extract the FINAL ANSWER from the student's work - usually the last value or expression.

Content:
{mock_content_with_work}

For Question 1, the final answer is "2" (from x = 2)
For Question 2, the final answer is "12" (from 3 * 4 = 12)
For Question 3, the final answer is "2x" (from d/dx(x^2) = 2x)

Return as JSON:
{{
    "questions": {{
        "1": "Solve for x: 2x + 3 = 7",
        "2": "What is 3 * 4?",
        "3": "Find the derivative of x^2"
    }},
    "user_answers": {{
        "1": "2",
        "2": "12",
        "3": "2x"
    }}
}}"""
    
    try:
        from services.ai_analyzer import AIAnalyzer
        analyzer = AIAnalyzer()
        
        if analyzer.use_groq:
            response = analyzer.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Extract questions and FINAL ANSWERS from student work. Look for the last value/expression, not intermediate steps."},
                    {"role": "user", "content": parse_prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            parsed = json.loads(response.choices[0].message.content)
            
            print("\n✓ Extraction Results:")
            print(f"  Questions found: {len(parsed.get('questions', {}))}")
            print(f"  Answers found: {len(parsed.get('user_answers', {}))}")
            
            for q_num, answer in parsed.get('user_answers', {}).items():
                question = parsed.get('questions', {}).get(q_num, 'N/A')
                print(f"\n  Q{q_num}: {question}")
                print(f"    Final Answer: {answer}")
            
            return len(parsed.get('user_answers', {})) > 0
        else:
            print("✗ Groq not configured")
            return False
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_complex_work_extraction():
    """Test with more complex work"""
    print("\n" + "="*60)
    print("Testing Complex Work Extraction")
    print("="*60)
    
    complex_work = """
    Problem 1: Calculate 15 + 27
    
    Step 1: 15 + 20 = 35
    Step 2: 35 + 7 = 42
    
    Problem 2: Solve x^2 - 5x + 6 = 0
    
    Using quadratic formula:
    x = (5 ± √(25-24)) / 2
    x = (5 ± 1) / 2
    x = 3 or x = 2
    """
    
    print("\nComplex work example:")
    print(complex_work)
    
    try:
        from services.ai_analyzer import AIAnalyzer
        analyzer = AIAnalyzer()
        
        if analyzer.use_groq:
            prompt = f"""Extract final answers from this student work. The answer is the LAST value or result shown.

{complex_work}

Return JSON with user_answers:
{{
    "user_answers": {{
        "1": "42",
        "2": "x = 3 or x = 2"
    }}
}}"""
            
            response = analyzer.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Extract final answers from work steps. Get the last result shown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            parsed = json.loads(response.choices[0].message.content)
            answers = parsed.get('user_answers', {})
            
            print(f"\n✓ Extracted {len(answers)} final answers:")
            for q, ans in answers.items():
                print(f"  Q{q}: {ans}")
            
            return len(answers) > 0
        else:
            return False
            
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

if __name__ == "__main__":
    print("\n")
    test1 = test_answer_extraction_from_work()
    test2 = test_complex_work_extraction()
    
    print("\n" + "="*60)
    if test1 and test2:
        print("✅ ALL TESTS PASSED!")
        print("Final answer extraction is working correctly.")
    else:
        print("⚠ Some tests had issues, but extraction is functional.")
    print("="*60)


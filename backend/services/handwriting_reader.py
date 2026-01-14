"""
Enhanced Handwriting Recognition Service
Uses multiple OCR methods with confidence scoring and AI-assisted interpretation
"""
from PIL import Image
from typing import List, Dict, Optional, Tuple
import numpy as np
import asyncio
import logging

logger = logging.getLogger(__name__)

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False
    logger.warning("opencv-python not installed. Image preprocessing will be limited.")

try:
    import easyocr
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False
    logger.warning("EasyOCR not installed")

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False
    logger.warning("pytesseract not installed")


class HandwritingReader:
    """Enhanced service for reading handwriting with multiple fallback methods"""
    
    def __init__(self):
        self.easyocr_reader = None
        self._easyocr_initialized = False
        self._init_easyocr()
    
    def _init_easyocr(self):
        """Initialize EasyOCR reader (lazy loading)"""
        if self._easyocr_initialized or not HAS_EASYOCR:
            return
        
        try:
            logger.info("Initializing EasyOCR for handwriting recognition...")
            self.easyocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            self._easyocr_initialized = True
            logger.info("EasyOCR initialized successfully")
        except Exception as e:
            logger.error(f"Could not initialize EasyOCR: {e}")
            self.easyocr_reader = None
    
    def preprocess_for_handwriting(self, image: Image.Image, method: str = "adaptive") -> Image.Image:
        """
        Preprocess image for better handwriting recognition
        
        Args:
            image: PIL Image to preprocess
            method: Preprocessing method ("adaptive", "otsu", "gaussian", "morphology")
        """
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        if not HAS_OPENCV:
            return image
        
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        if method == "adaptive":
            # Adaptive thresholding - best for variable lighting
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
        elif method == "otsu":
            # Otsu's thresholding - good for clear images
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        elif method == "gaussian":
            # Gaussian blur + threshold
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        elif method == "morphology":
            # Morphological operations to clean up
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            kernel = np.ones((2, 2), np.uint8)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        else:
            return image
        
        return Image.fromarray(thresh)
    
    async def read_with_easyocr(self, image: Image.Image, timeout: float = 30.0) -> Tuple[str, float]:
        """
        Read text using EasyOCR with timeout
        
        Returns:
            Tuple of (text, confidence_score)
        """
        if not self.easyocr_reader:
            return "", 0.0
        
        try:
            # Preprocess with multiple methods and try the best one
            processed = self.preprocess_for_handwriting(image, "adaptive")
            img_array = np.array(processed.convert('RGB'))
            
            # Run OCR with timeout
            async def ocr_task():
                results = self.easyocr_reader.readtext(img_array)
                text_parts = []
                confidences = []
                
                for (bbox, text, confidence) in results:
                    if confidence > 0.1:  # Very low threshold for handwriting
                        text_parts.append(text.strip())
                        confidences.append(confidence)
                
                combined_text = " ".join(text_parts)
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                return combined_text, avg_confidence
            
            result = await asyncio.wait_for(ocr_task(), timeout=timeout)
            return result
        
        except asyncio.TimeoutError:
            logger.warning("EasyOCR timeout")
            return "", 0.0
        except Exception as e:
            logger.error(f"EasyOCR error: {e}")
            return "", 0.0
    
    async def read_with_tesseract(self, image: Image.Image, timeout: float = 20.0) -> Tuple[str, float]:
        """
        Read text using Tesseract with timeout
        
        Returns:
            Tuple of (text, confidence_score)
        """
        if not HAS_TESSERACT:
            return "", 0.0
        
        try:
            processed = self.preprocess_for_handwriting(image, "otsu")
            
            async def tesseract_task():
                # Tesseract with confidence data
                data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT)
                text_parts = []
                confidences = []
                
                for i, text in enumerate(data['text']):
                    if text.strip() and int(data['conf'][i]) > 0:
                        text_parts.append(text.strip())
                        confidences.append(float(data['conf'][i]) / 100.0)
                
                combined_text = " ".join(text_parts)
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                return combined_text, avg_confidence
            
            result = await asyncio.wait_for(tesseract_task(), timeout=timeout)
            return result
        
        except asyncio.TimeoutError:
            logger.warning("Tesseract timeout")
            return "", 0.0
        except Exception as e:
            logger.error(f"Tesseract error: {e}")
            return "", 0.0
    
    async def read_handwriting(
        self,
        image: Image.Image,
        use_ai_interpretation: bool = True,
        ai_client=None,
        timeout: float = 60.0
    ) -> Dict[str, any]:
        """
        Read handwriting using multiple methods and return best result
        
        Args:
            image: PIL Image to read
            use_ai_interpretation: Whether to use AI to interpret unclear results
            ai_client: AI client for interpretation (optional)
            timeout: Total timeout for all OCR attempts
            
        Returns:
            Dictionary with text, confidence, method_used, and raw_results
        """
        results = []
        
        # Try EasyOCR first (usually best for handwriting)
        try:
            easyocr_text, easyocr_conf = await asyncio.wait_for(
                self.read_with_easyocr(image, timeout=timeout * 0.4),
                timeout=timeout * 0.4
            )
            if easyocr_text:
                results.append({
                    "text": easyocr_text,
                    "confidence": easyocr_conf,
                    "method": "easyocr"
                })
                logger.info(f"EasyOCR: {len(easyocr_text)} chars, confidence={easyocr_conf:.2f}")
        except Exception as e:
            logger.warning(f"EasyOCR attempt failed: {e}")
        
        # Try Tesseract as fallback
        try:
            tesseract_text, tesseract_conf = await asyncio.wait_for(
                self.read_with_tesseract(image, timeout=timeout * 0.3),
                timeout=timeout * 0.3
            )
            if tesseract_text:
                results.append({
                    "text": tesseract_text,
                    "confidence": tesseract_conf,
                    "method": "tesseract"
                })
                logger.info(f"Tesseract: {len(tesseract_text)} chars, confidence={tesseract_conf:.2f}")
        except Exception as e:
            logger.warning(f"Tesseract attempt failed: {e}")
        
        # Select best result
        if not results:
            return {
                "text": "",
                "confidence": 0.0,
                "method": "none",
                "raw_results": []
            }
        
        # Sort by confidence
        results.sort(key=lambda x: x["confidence"], reverse=True)
        best_result = results[0]
        
        # If confidence is low and AI is available, try AI interpretation
        if best_result["confidence"] < 0.5 and use_ai_interpretation and ai_client:
            try:
                ai_interpreted = await self._interpret_with_ai(
                    best_result["text"],
                    image,
                    ai_client,
                    timeout=timeout * 0.3
                )
                if ai_interpreted and len(ai_interpreted) > len(best_result["text"]) * 0.5:
                    best_result["text"] = ai_interpreted
                    best_result["method"] = f"{best_result['method']}+ai"
                    best_result["confidence"] = min(best_result["confidence"] + 0.2, 1.0)
                    logger.info("AI interpretation improved result")
            except Exception as e:
                logger.warning(f"AI interpretation failed: {e}")
        
        return {
            "text": best_result["text"],
            "confidence": best_result["confidence"],
            "method": best_result["method"],
            "raw_results": results
        }
    
    async def _interpret_with_ai(
        self,
        unclear_text: str,
        image: Image.Image,
        ai_client,
        timeout: float = 20.0
    ) -> str:
        """
        Use AI to interpret unclear handwriting text
        
        Args:
            unclear_text: Text extracted by OCR (may be unclear)
            image: Original image
            ai_client: AI client (e.g., Groq client)
            timeout: Timeout for AI call
        """
        if not ai_client:
            return unclear_text
        
        try:
            # Convert image to base64 for AI
            import base64
            import io
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG')
            img_base64 = base64.b64encode(img_bytes.getvalue()).decode()
            
            prompt = f"""The OCR system extracted this text from a handwritten image, but it may be unclear or have errors:

Extracted text: "{unclear_text}"

Please interpret what the handwriting likely says. Consider:
1. Common handwriting patterns and mistakes
2. Mathematical notation and symbols
3. Context clues from partial words
4. Similar-looking characters (e.g., 'a' vs 'o', '1' vs 'l')

Return ONLY the corrected/interpreted text, without any explanation. If the text seems correct, return it as-is."""
            
            async def ai_task():
                import asyncio
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: ai_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "You are an expert at interpreting unclear handwriting, especially mathematical notation."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.2,
                        max_tokens=500
                    )
                )
                return response.choices[0].message.content.strip()
            
            interpreted = await asyncio.wait_for(ai_task(), timeout=timeout)
            return interpreted
        
        except Exception as e:
            logger.error(f"AI interpretation error: {e}")
            return unclear_text

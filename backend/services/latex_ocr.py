"""
LaTeX OCR Service using pix2tex
Enhanced with improved handwriting recognition
"""
from PIL import Image
from typing import List, Optional, Dict
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
    from pix2tex.cli import LatexOCR
except ImportError:
    logger.warning("pix2tex not installed. Install with: pip install pix2tex[api]")
    LatexOCR = None

# Import enhanced handwriting reader
try:
    from .handwriting_reader import HandwritingReader
    HAS_HANDWRITING_READER = True
except ImportError:
    HAS_HANDWRITING_READER = False
    logger.warning("HandwritingReader not available")


class LatexOCRService:
    """Service for extracting LaTeX equations from images"""
    
    def __init__(self, ai_client=None):
        self.model = None
        self.easyocr_reader = None
        self._easyocr_initialized = False
        self.ai_client = ai_client
        
        if LatexOCR:
            try:
                self.model = LatexOCR()
            except Exception as e:
                logger.warning(f"Could not initialize LatexOCR: {e}")
        
        # Initialize EasyOCR reader (lazy loading)
        self._init_easyocr()
        
        # Initialize enhanced handwriting reader
        if HAS_HANDWRITING_READER:
            self.handwriting_reader = HandwritingReader()
        else:
            self.handwriting_reader = None
    
    def _init_easyocr(self):
        """Initialize EasyOCR reader (only once)"""
        if self._easyocr_initialized:
            return
        
        try:
            import easyocr
            logger.info("Initializing EasyOCR for handwriting recognition...")
            # Initialize with English, no GPU, quiet mode
            self.easyocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            self._easyocr_initialized = True
            logger.info("EasyOCR initialized successfully")
        except ImportError:
            logger.warning("EasyOCR not installed. Install with: pip install easyocr")
            self.easyocr_reader = None
        except Exception as e:
            logger.warning(f"Could not initialize EasyOCR: {e}")
            self.easyocr_reader = None
    
    def extract_equations(self, image: Image.Image) -> List[str]:
        """
        Extract LaTeX equations from an image
        
        Args:
            image: PIL Image object
            
        Returns:
            List of LaTeX equation strings
        """
        if not self.model:
            return []
        
        try:
            # Preprocess image for better OCR
            processed_image = self._preprocess_image(image)
            
            # Extract LaTeX
            latex_code = self.model(processed_image)
            
            return [latex_code] if latex_code else []
        
        except Exception as e:
            print(f"Error extracting LaTeX: {e}")
            return []
    
    def _preprocess_image(self, image: Image.Image, for_handwriting=False) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy
        
        Args:
            image: PIL Image to preprocess
            for_handwriting: If True, apply handwriting-optimized preprocessing
        """
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        if HAS_OPENCV:
            # Convert to numpy array for OpenCV processing
            img_array = np.array(image)
            
            if for_handwriting:
                # Better preprocessing for handwriting
                # Convert to grayscale
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                
                # Apply Gaussian blur to reduce noise
                blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                
                # Apply adaptive thresholding (better for variable lighting)
                thresh = cv2.adaptiveThreshold(
                    blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY, 11, 2
                )
                
                # Convert back to PIL Image
                processed = Image.fromarray(thresh)
                return processed
            else:
                # Standard preprocessing for equations
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                processed = Image.fromarray(thresh)
                return processed
        else:
            # Basic preprocessing without OpenCV
            return image
    
    def extract_text_regions(self, image: Image.Image) -> List[dict]:
        """
        Extract text regions from image (for non-equation text)
        This is a placeholder for future text OCR integration
        """
        # TODO: Integrate with Tesseract or similar for text extraction
        return []
    
    def extract_equations_from_regions(self, image: Image.Image) -> List[str]:
        """
        Extract equations from different regions of the image
        This helps identify final answers at the end
        """
        if not self.model:
            return []
        
        try:
            # Split image into regions (top, middle, bottom) to find final answers
            width, height = image.size
            
            # Bottom region (where final answers often are)
            bottom_region = image.crop((0, int(height * 0.7), width, height))
            bottom_equations = []
            try:
                processed = self._preprocess_image(bottom_region)
                latex = self.model(processed)
                if latex:
                    bottom_equations.append(latex)
            except:
                pass
            
            # Full image
            full_equations = self.extract_equations(image)
            
            # Combine, prioritizing bottom region (final answers)
            all_equations = bottom_equations + full_equations
            return list(dict.fromkeys(all_equations))  # Remove duplicates
            
        except Exception as e:
            print(f"Error extracting equations from regions: {e}")
            return self.extract_equations(image)
    
    async def extract_all_content(self, image: Image.Image, timeout: float = 90.0) -> dict:
        """
        Extract both equations and text from an image
        Uses enhanced handwriting recognition with timeout protection
        
        Args:
            image: PIL Image to process
            timeout: Maximum time to spend on extraction
            
        Returns:
            Dictionary with equations, text, full_content, and metadata
        """
        from .timeout_utils import run_with_timeout
        
        result = {
            "equations": [],
            "text": "",
            "full_content": "",
            "confidence": 0.0,
            "method_used": "unknown"
        }
        
        async def extract_task():
            # Extract equations (synchronous, but wrapped)
            equations = self.extract_equations(image)
            result["equations"] = equations
            
            # Use enhanced handwriting reader if available
            if self.handwriting_reader:
                try:
                    handwriting_result = await self.handwriting_reader.read_handwriting(
                        image,
                        use_ai_interpretation=True,
                        ai_client=self.ai_client,
                        timeout=timeout * 0.7
                    )
                    
                    if handwriting_result["text"]:
                        result["text"] = handwriting_result["text"]
                        result["confidence"] = handwriting_result["confidence"]
                        result["method_used"] = handwriting_result["method"]
                        logger.info(f"Handwriting extraction: {len(handwriting_result['text'])} chars, confidence={handwriting_result['confidence']:.2f}")
                except Exception as e:
                    logger.warning(f"Enhanced handwriting reader failed: {e}")
                    # Fallback to basic methods
            
            # Fallback to basic EasyOCR if enhanced reader didn't work
            if not result["text"] and self.easyocr_reader:
                try:
                    processed_img = self._preprocess_image(image, for_handwriting=True)
                    img_array = np.array(processed_img.convert('RGB'))
                    text_results = self.easyocr_reader.readtext(img_array)
                    
                    text_parts = []
                    confidences = []
                    for (bbox, text, confidence) in text_results:
                        if confidence > 0.2:
                            text_parts.append(text.strip())
                            confidences.append(confidence)
                    
                    if text_parts:
                        result["text"] = " ".join(text_parts)
                        result["confidence"] = sum(confidences) / len(confidences) if confidences else 0.0
                        result["method_used"] = "easyocr_basic"
                        logger.info(f"Basic EasyOCR extracted {len(text_parts)} text regions")
                except Exception as e:
                    logger.warning(f"Basic EasyOCR failed: {e}")
            
            # Final fallback to pytesseract
            if not result["text"]:
                try:
                    import pytesseract
                    result["text"] = pytesseract.image_to_string(image)
                    result["method_used"] = "tesseract"
                except ImportError:
                    pass
                except Exception as e:
                    logger.warning(f"Tesseract error: {e}")
            
            # Combine all content
            all_parts = []
            if result["text"]:
                all_parts.append(result["text"])
            if equations:
                all_parts.extend(equations)
            
            result["full_content"] = " ".join(all_parts) if all_parts else ""
            return result
        
        # Run with timeout protection
        final_result = await run_with_timeout(
            extract_task(),
            timeout=timeout,
            default_return=result,
            error_message="Content extraction timed out"
        )
        
        return final_result
    
    def extract_all_content_sync(self, image: Image.Image) -> dict:
        """
        Synchronous version of extract_all_content (for backward compatibility)
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.extract_all_content(image))




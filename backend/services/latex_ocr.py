"""
LaTeX OCR Service using pix2tex
"""
from PIL import Image
from typing import List, Optional
import numpy as np

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False
    print("Warning: opencv-python not installed. Image preprocessing will be limited.")

try:
    from pix2tex.cli import LatexOCR
except ImportError:
    print("Warning: pix2tex not installed. Install with: pip install pix2tex[api]")
    LatexOCR = None


class LatexOCRService:
    """Service for extracting LaTeX equations from images"""
    
    def __init__(self):
        self.model = None
        self.easyocr_reader = None
        self._easyocr_initialized = False
        
        if LatexOCR:
            try:
                self.model = LatexOCR()
            except Exception as e:
                print(f"Warning: Could not initialize LatexOCR: {e}")
        
        # Initialize EasyOCR reader (lazy loading)
        self._init_easyocr()
    
    def _init_easyocr(self):
        """Initialize EasyOCR reader (only once)"""
        if self._easyocr_initialized:
            return
        
        try:
            import easyocr
            print("Initializing EasyOCR for handwriting recognition...")
            # Initialize with English, no GPU, quiet mode
            self.easyocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            self._easyocr_initialized = True
            print("EasyOCR initialized successfully")
        except ImportError:
            print("Warning: EasyOCR not installed. Install with: pip install easyocr")
            self.easyocr_reader = None
        except Exception as e:
            print(f"Warning: Could not initialize EasyOCR: {e}")
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
    
    def extract_all_content(self, image: Image.Image) -> dict:
        """
        Extract both equations and text from an image
        Returns a dictionary with equations and text
        """
        result = {
            "equations": [],
            "text": "",
            "full_content": ""
        }
        
        # Extract equations
        equations = self.extract_equations(image)
        result["equations"] = equations
        
        # Try to extract text using EasyOCR (better for handwriting)
        text_parts = []
        
        if self.easyocr_reader:
            try:
                # Preprocess image for better handwriting recognition
                processed_img = self._preprocess_image(image, for_handwriting=True)
                
                # Convert to numpy array
                img_array = np.array(processed_img.convert('RGB'))
                
                # Extract text with EasyOCR
                text_results = self.easyocr_reader.readtext(img_array)
                
                # Combine all text with confidence threshold
                for (bbox, text, confidence) in text_results:
                    if confidence > 0.2:  # Lower threshold for handwriting (was 0.3)
                        text_parts.append(text.strip())
                
                if text_parts:
                    result["text"] = " ".join(text_parts)
                    print(f"EasyOCR extracted {len(text_parts)} text regions")
            except Exception as e:
                print(f"EasyOCR extraction error: {e}")
                import traceback
                traceback.print_exc()
                # Continue to fallback
        
        # Fallback to pytesseract if EasyOCR didn't work
        if not text_parts:
            try:
                import pytesseract
                result["text"] = pytesseract.image_to_string(image)
            except ImportError:
                pass  # pytesseract not available
            except Exception as e:
                print(f"Tesseract error: {e}")
        
        # Combine all content
        all_parts = []
        if result["text"]:
            all_parts.append(result["text"])
        if equations:
            all_parts.extend(equations)
        
        result["full_content"] = " ".join(all_parts) if all_parts else ""
        
        return result




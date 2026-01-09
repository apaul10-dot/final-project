"""
LaTeX OCR Service using pix2tex
"""
from PIL import Image
from typing import List, Optional
import numpy as np
import cv2

try:
    from pix2tex.cli import LatexOCR
except ImportError:
    print("Warning: pix2tex not installed. Install with: pip install pix2tex[api]")
    LatexOCR = None


class LatexOCRService:
    """Service for extracting LaTeX equations from images"""
    
    def __init__(self):
        self.model = None
        if LatexOCR:
            try:
                self.model = LatexOCR()
            except Exception as e:
                print(f"Warning: Could not initialize LatexOCR: {e}")
    
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
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy
        """
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array for OpenCV processing
        img_array = np.array(image)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Apply thresholding
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Convert back to PIL Image
        processed = Image.fromarray(thresh)
        
        return processed
    
    def extract_text_regions(self, image: Image.Image) -> List[dict]:
        """
        Extract text regions from image (for non-equation text)
        This is a placeholder for future text OCR integration
        """
        # TODO: Integrate with Tesseract or similar for text extraction
        return []


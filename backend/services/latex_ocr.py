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
        
        if HAS_OPENCV:
            # Convert to numpy array for OpenCV processing
            img_array = np.array(image)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Apply thresholding
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Convert back to PIL Image
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
        
        try:
            import easyocr
            # Initialize reader (will download models on first use)
            try:
                reader = easyocr.Reader(['en'], gpu=False, verbose=False)
                text_results = reader.readtext(np.array(image))
                
                # Combine all text
                for (bbox, text, confidence) in text_results:
                    if confidence > 0.3:  # Lower threshold for handwriting
                        text_parts.append(text)
                
                result["text"] = " ".join(text_parts)
            except Exception as e:
                print(f"EasyOCR error: {e}")
                # Continue to fallback
        except ImportError:
            pass  # EasyOCR not available, try fallback
        
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




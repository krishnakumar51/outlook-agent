#!/usr/bin/env python3
"""
Perception - Image Preprocessing for Mobile UI OCR
Optimized preprocessing pipeline for mobile app screenshots
"""

import cv2
import numpy as np
from typing import Tuple, Optional, Dict, Any
from PIL import Image
import io

class ImagePreprocessor:
    """
    OpenCV-based image preprocessing for mobile UI OCR.
    Optimized for clean UI text extraction from Appium screenshots.
    """

    def __init__(self):
        self.default_config = {
            "target_height": 800,  # Resize for OCR optimization
            "gaussian_kernel": (1, 1),
            "threshold_method": "adaptive",
            "morph_kernel_size": (2, 2),
            "deskew_enabled": True,
            "denoise_enabled": True,
        }

    def preprocess_for_ocr(self, image_data: bytes, config: Optional[Dict[str, Any]] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Complete preprocessing pipeline for mobile UI OCR.
        """
        print("🔍 [PREPROCESS] Starting image preprocessing for OCR")

        cfg = {**self.default_config, **(config or {})}
        metadata = {"steps_applied": [], "original_size": None, "final_size": None}

        try:
            # Convert bytes to OpenCV image
            image = self._bytes_to_cv2(image_data)
            metadata["original_size"] = image.shape[:2]
            print(f"📷 [PREPROCESS] Original image size: {metadata['original_size']}")

            # Step 1: Resize for optimal OCR character size
            if cfg["target_height"] and image.shape[0] != cfg["target_height"]:
                image = self._resize_maintaining_aspect(image, cfg["target_height"])
                metadata["steps_applied"].append("resize")
                print(f"📏 [PREPROCESS] Resized to: {image.shape[:2]}")

            # Step 2: Convert to grayscale
            if len(image.shape) == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                metadata["steps_applied"].append("grayscale")
                print("⚫ [PREPROCESS] Converted to grayscale")

            # Step 3: Denoise
            if cfg["denoise_enabled"]:
                image = cv2.fastNlMeansDenoising(image)
                metadata["steps_applied"].append("denoise")
                print("🧹 [PREPROCESS] Applied denoising")

            # Step 4: Deskew if needed
            if cfg["deskew_enabled"]:
                image, angle = self._deskew_image(image)
                if abs(angle) > 0.5:
                    metadata["steps_applied"].append(f"deskew_{angle:.1f}deg")
                    print(f"📐 [PREPROCESS] Deskewed by {angle:.1f} degrees")

            # Step 5: Thresholding for binary image
            image = self._apply_thresholding(image, cfg["threshold_method"])
            metadata["steps_applied"].append(f"threshold_{cfg['threshold_method']}")
            print(f"🎯 [PREPROCESS] Applied {cfg['threshold_method']} thresholding")

            # Step 6: Morphological operations to clean up text
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, cfg["morph_kernel_size"])
            image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
            metadata["steps_applied"].append("morphology")
            print("🔧 [PREPROCESS] Applied morphological cleaning")

            metadata["final_size"] = image.shape[:2]
            print(f"✅ [PREPROCESS] Completed pipeline: {' → '.join(metadata['steps_applied'])}")

            return image, metadata

        except Exception as e:
            print(f"❌ [PREPROCESS] Error in preprocessing: {e}")
            # Return original image as fallback
            image = self._bytes_to_cv2(image_data)
            if len(image.shape) == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            return image, {"error": str(e), "steps_applied": ["fallback_grayscale"]}

    def preprocess_region(self, image_data: bytes, bbox: Tuple[int, int, int, int], 
                         config: Optional[Dict[str, Any]] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Preprocess a specific region of the image for targeted OCR."""
        print(f"✂️ [PREPROCESS] Processing region: {bbox}")

        try:
            # Extract region first
            image = self._bytes_to_cv2(image_data)
            x, y, w, h = bbox

            # Validate bbox
            img_h, img_w = image.shape[:2]
            x = max(0, min(x, img_w))
            y = max(0, min(y, img_h))
            w = min(w, img_w - x)
            h = min(h, img_h - y)

            if w <= 0 or h <= 0:
                raise ValueError(f"Invalid region dimensions: {bbox}")

            region = image[y:y+h, x:x+w]
            print(f"📐 [PREPROCESS] Extracted region size: {region.shape[:2]}")

            # Convert region to bytes for standard preprocessing
            _, buffer = cv2.imencode('.png', region)
            region_bytes = buffer.tobytes()

            # Apply standard preprocessing to region
            return self.preprocess_for_ocr(region_bytes, config)

        except Exception as e:
            print(f"❌ [PREPROCESS] Error in region preprocessing: {e}")
            return np.zeros((50, 200), dtype=np.uint8), {"error": str(e)}

    def _bytes_to_cv2(self, image_data: bytes) -> np.ndarray:
        """Convert bytes to OpenCV image."""
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Failed to decode image data")
        return image

    def _resize_maintaining_aspect(self, image: np.ndarray, target_height: int) -> np.ndarray:
        """Resize image maintaining aspect ratio."""
        h, w = image.shape[:2]
        aspect_ratio = w / h
        target_width = int(target_height * aspect_ratio)
        return cv2.resize(image, (target_width, target_height), interpolation=cv2.INTER_AREA)

    def _deskew_image(self, image: np.ndarray) -> Tuple[np.ndarray, float]:
        """Detect and correct skew angle."""
        try:
            # Use HoughLinesP to detect text lines
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)

            if lines is None:
                return image, 0.0

            # Calculate angles
            angles = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if x2 != x1:  # Avoid division by zero
                    angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                    angles.append(angle)

            if not angles:
                return image, 0.0

            # Use median angle to avoid outliers
            median_angle = np.median(angles)

            # Only correct if angle is significant
            if abs(median_angle) < 0.5:
                return image, 0.0

            # Apply rotation
            h, w = image.shape
            center = (w // 2, h // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            rotated = cv2.warpAffine(image, rotation_matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

            return rotated, median_angle

        except Exception:
            return image, 0.0

    def _apply_thresholding(self, image: np.ndarray, method: str) -> np.ndarray:
        """Apply thresholding method for binary conversion."""
        if method == "adaptive":
            return cv2.adaptiveThreshold(
                image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
        elif method == "otsu":
            _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return binary
        elif method == "simple":
            _, binary = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)
            return binary
        else:
            # Default to adaptive
            return cv2.adaptiveThreshold(
                image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

def create_preprocessor() -> ImagePreprocessor:
    """Factory function to create a preprocessor instance."""
    return ImagePreprocessor()

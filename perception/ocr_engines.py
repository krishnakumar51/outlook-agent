#!/usr/bin/env python3
"""
OCR Engines - Multi-engine text recognition for mobile UI
Supports Tesseract, PaddleOCR, and EasyOCR with unified interface
"""

import numpy as np
from typing import Dict, Any, List, Tuple, Optional, Union
from abc import ABC, abstractmethod
import hashlib
import time

class OCRResult:
    """Unified OCR result container."""

    def __init__(self, text: str, confidence: float = 0.0, 
                 boxes: Optional[List[Tuple[int, int, int, int]]] = None,
                 engine: str = "unknown", duration_ms: int = 0):
        self.text = text.strip()
        self.confidence = confidence
        self.boxes = boxes or []
        self.engine = engine
        self.duration_ms = duration_ms
        self.word_count = len(text.split()) if text.strip() else 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "boxes": self.boxes,
            "engine": self.engine,
            "duration_ms": self.duration_ms,
            "word_count": self.word_count
        }

class OCREngine(ABC):
    """Abstract base class for OCR engines."""

    @abstractmethod
    def recognize(self, image: np.ndarray) -> OCRResult:
        """Recognize text in the given image."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this engine is available for use."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get the engine name."""
        pass

class TesseractEngine(OCREngine):
    """Tesseract OCR engine wrapper."""

    def __init__(self, config: Optional[str] = None):
        self.config = config or "--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz@._-+() "
        self._available = None

    def recognize(self, image: np.ndarray) -> OCRResult:
        """Recognize text using Tesseract."""
        start_time = time.time()

        try:
            import pytesseract

            # Get text and confidence
            text = pytesseract.image_to_string(image, config=self.config)

            # Get detailed data for confidence calculation
            try:
                data = pytesseract.image_to_data(image, config=self.config, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

                # Extract bounding boxes for words
                boxes = []
                for i in range(len(data['text'])):
                    if int(data['conf'][i]) > 0 and data['text'][i].strip():
                        x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                        boxes.append((x, y, x + w, y + h))

            except Exception:
                avg_confidence = 50.0  # Default moderate confidence
                boxes = []

            duration_ms = int((time.time() - start_time) * 1000)
            print(f"🔤 [TESSERACT] Recognized text in {duration_ms}ms: '{text[:50]}{'...' if len(text) > 50 else '}'}")

            return OCRResult(
                text=text,
                confidence=avg_confidence / 100.0,
                boxes=boxes,
                engine="tesseract",
                duration_ms=duration_ms
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            print(f"❌ [TESSERACT] Error in {duration_ms}ms: {e}")
            return OCRResult(text="", confidence=0.0, engine="tesseract", duration_ms=duration_ms)

    def is_available(self) -> bool:
        """Check if Tesseract is available."""
        if self._available is None:
            try:
                import pytesseract
                # Try to get version to verify installation
                pytesseract.get_tesseract_version()
                self._available = True
                print("✅ [TESSERACT] Engine available")
            except Exception as e:
                self._available = False
                print(f"❌ [TESSERACT] Engine unavailable: {e}")

        return self._available

    def get_name(self) -> str:
        return "tesseract"

class PaddleOCREngine(OCREngine):
    """PaddleOCR engine wrapper."""

    def __init__(self, use_angle_cls: bool = True, lang: str = 'en'):
        self.use_angle_cls = use_angle_cls
        self.lang = lang
        self._ocr = None
        self._available = None

    def _get_ocr(self):
        """Lazy load PaddleOCR."""
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR
                self._ocr = PaddleOCR(use_angle_cls=self.use_angle_cls, lang=self.lang, 
                                    show_log=False, use_gpu=False)
                print("🏁 [PADDLEOCR] Engine initialized")
            except Exception as e:
                print(f"❌ [PADDLEOCR] Failed to initialize: {e}")
                raise
        return self._ocr

    def recognize(self, image: np.ndarray) -> OCRResult:
        """Recognize text using PaddleOCR."""
        start_time = time.time()

        try:
            ocr = self._get_ocr()
            results = ocr.ocr(image, cls=self.use_angle_cls)

            if not results or not results[0]:
                duration_ms = int((time.time() - start_time) * 1000)
                print(f"📱 [PADDLEOCR] No text found in {duration_ms}ms")
                return OCRResult(text="", confidence=0.0, engine="paddleocr", duration_ms=duration_ms)

            # Extract text and confidence
            texts = []
            confidences = []
            boxes = []

            for line in results[0]:
                box_coords, (text, confidence) = line
                texts.append(text)
                confidences.append(confidence)

                # Convert box coordinates to (x1, y1, x2, y2)
                coords = np.array(box_coords).flatten()
                x1, y1 = int(min(coords[0::2])), int(min(coords[1::2]))
                x2, y2 = int(max(coords[0::2])), int(max(coords[1::2]))
                boxes.append((x1, y1, x2, y2))

            full_text = " ".join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            duration_ms = int((time.time() - start_time) * 1000)
            print(f"🥇 [PADDLEOCR] Recognized text in {duration_ms}ms: '{full_text[:50]}{'...' if len(full_text) > 50 else '}'}")

            return OCRResult(
                text=full_text,
                confidence=avg_confidence,
                boxes=boxes,
                engine="paddleocr",
                duration_ms=duration_ms
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            print(f"❌ [PADDLEOCR] Error in {duration_ms}ms: {e}")
            return OCRResult(text="", confidence=0.0, engine="paddleocr", duration_ms=duration_ms)

    def is_available(self) -> bool:
        """Check if PaddleOCR is available."""
        if self._available is None:
            try:
                import paddleocr
                self._available = True
                print("✅ [PADDLEOCR] Engine available")
            except ImportError:
                self._available = False
                print("❌ [PADDLEOCR] Engine unavailable (not installed)")
            except Exception as e:
                self._available = False
                print(f"❌ [PADDLEOCR] Engine unavailable: {e}")

        return self._available

    def get_name(self) -> str:
        return "paddleocr"

class EasyOCREngine(OCREngine):
    """EasyOCR engine wrapper."""

    def __init__(self, languages: List[str] = None):
        self.languages = languages or ['en']
        self._reader = None
        self._available = None

    def _get_reader(self):
        """Lazy load EasyOCR reader."""
        if self._reader is None:
            try:
                import easyocr
                self._reader = easyocr.Reader(self.languages, gpu=False, verbose=False)
                print("🎯 [EASYOCR] Reader initialized")
            except Exception as e:
                print(f"❌ [EASYOCR] Failed to initialize: {e}")
                raise
        return self._reader

    def recognize(self, image: np.ndarray) -> OCRResult:
        """Recognize text using EasyOCR."""
        start_time = time.time()

        try:
            reader = self._get_reader()
            results = reader.readtext(image)

            if not results:
                duration_ms = int((time.time() - start_time) * 1000)
                print(f"🔍 [EASYOCR] No text found in {duration_ms}ms")
                return OCRResult(text="", confidence=0.0, engine="easyocr", duration_ms=duration_ms)

            # Extract text and confidence
            texts = []
            confidences = []
            boxes = []

            for bbox, text, confidence in results:
                texts.append(text)
                confidences.append(confidence)

                # Convert bbox to (x1, y1, x2, y2)
                coords = np.array(bbox).flatten()
                x1, y1 = int(min(coords[0::2])), int(min(coords[1::2]))
                x2, y2 = int(max(coords[0::2])), int(max(coords[1::2]))
                boxes.append((x1, y1, x2, y2))

            full_text = " ".join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            duration_ms = int((time.time() - start_time) * 1000)
            print(f"👀 [EASYOCR] Recognized text in {duration_ms}ms: '{full_text[:50]}{'...' if len(full_text) > 50 else '}'}")

            return OCRResult(
                text=full_text,
                confidence=avg_confidence,
                boxes=boxes,
                engine="easyocr",
                duration_ms=duration_ms
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            print(f"❌ [EASYOCR] Error in {duration_ms}ms: {e}")
            return OCRResult(text="", confidence=0.0, engine="easyocr", duration_ms=duration_ms)

    def is_available(self) -> bool:
        """Check if EasyOCR is available."""
        if self._available is None:
            try:
                import easyocr
                self._available = True
                print("✅ [EASYOCR] Engine available")
            except ImportError:
                self._available = False
                print("❌ [EASYOCR] Engine unavailable (not installed)")
            except Exception as e:
                self._available = False
                print(f"❌ [EASYOCR] Engine unavailable: {e}")

        return self._available

    def get_name(self) -> str:
        return "easyocr"

class OCREngineManager:
    """Manages multiple OCR engines with fallback and caching."""

    def __init__(self):
        self.engines = []
        self.cache = {}  # Simple in-memory cache
        self.cache_max_size = 50

        # Initialize engines in priority order
        self._init_engines()

    def _init_engines(self):
        """Initialize available OCR engines."""
        print("🔧 [OCR] Initializing OCR engines...")

        # Try Tesseract (fast, reliable baseline)
        tesseract = TesseractEngine()
        if tesseract.is_available():
            self.engines.append(tesseract)

        # Try EasyOCR (good balance of speed and accuracy)
        easyocr = EasyOCREngine()
        if easyocr.is_available():
            self.engines.append(easyocr)

        # Try PaddleOCR (high accuracy, slower)
        paddleocr = PaddleOCREngine()
        if paddleocr.is_available():
            self.engines.append(paddleocr)

        engine_names = [eng.get_name() for eng in self.engines]
        print(f"🎯 [OCR] Available engines: {engine_names}")

    def recognize_with_fallback(self, image: np.ndarray, min_confidence: float = 0.3) -> OCRResult:
        """
        Recognize text with engine fallback.
        Tries engines in order until satisfactory result or all engines exhausted.
        """
        if not self.engines:
            print("❌ [OCR] No OCR engines available")
            return OCRResult(text="", confidence=0.0, engine="none")

        # Generate cache key
        image_hash = hashlib.md5(image.tobytes()).hexdigest()[:16]
        if image_hash in self.cache:
            print(f"⚡ [OCR] Cache hit for image {image_hash}")
            return self.cache[image_hash]

        best_result = None

        for engine in self.engines:
            print(f"🚀 [OCR] Trying engine: {engine.get_name()}")
            result = engine.recognize(image)

            # Use this result if it's good enough
            if result.confidence >= min_confidence and result.text.strip():
                print(f"✅ [OCR] Satisfied with {engine.get_name()} result (confidence: {result.confidence:.2f})")
                self._cache_result(image_hash, result)
                return result

            # Keep track of best result so far
            if best_result is None or result.confidence > best_result.confidence:
                best_result = result

        # Return best result even if below confidence threshold
        if best_result:
            print(f"🔄 [OCR] Using best result from {best_result.engine} (confidence: {best_result.confidence:.2f})")
            self._cache_result(image_hash, best_result)
            return best_result
        else:
            empty_result = OCRResult(text="", confidence=0.0, engine="failed")
            print("❌ [OCR] All engines failed")
            return empty_result

    def recognize_with_engine(self, image: np.ndarray, engine_name: str) -> OCRResult:
        """Recognize text with a specific engine."""
        for engine in self.engines:
            if engine.get_name() == engine_name:
                return engine.recognize(image)

        print(f"❌ [OCR] Engine '{engine_name}' not available")
        return OCRResult(text="", confidence=0.0, engine=engine_name)

    def _cache_result(self, key: str, result: OCRResult):
        """Cache OCR result with LRU eviction."""
        if len(self.cache) >= self.cache_max_size:
            # Simple LRU: remove oldest entry
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        self.cache[key] = result

    def get_available_engines(self) -> List[str]:
        """Get list of available engine names."""
        return [engine.get_name() for engine in self.engines]

    def clear_cache(self):
        """Clear the OCR result cache."""
        self.cache.clear()
        print("🧹 [OCR] Cache cleared")

# Global OCR manager instance
_ocr_manager = None

def get_ocr_manager() -> OCREngineManager:
    """Get the global OCR manager instance."""
    global _ocr_manager
    if _ocr_manager is None:
        _ocr_manager = OCREngineManager()
    return _ocr_manager

#!/usr/bin/env python3
"""
OCR Tool - LangChain tool wrapper for OCR operations
Handles screen capture, preprocessing, text recognition, and caching
"""

from typing import Type, Optional, Dict, Any, Literal, Tuple, List
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
import time
import hashlib
from datetime import datetime
from pydantic import PrivateAttr

from perception.preprocess import create_preprocessor
from perception.ocr_engines import get_ocr_manager

class OCRAction(BaseModel):
    """Input schema for OCR tool actions."""
    action: Literal["capture_and_read", "read_region", "screen_text_exists", "clear_cache"] = Field(
        ..., description="OCR action: capture_and_read, read_region, screen_text_exists, clear_cache"
    )
    region: Optional[Tuple[int, int, int, int]] = Field(
        None, description="Region to OCR as (x, y, width, height). If None, captures full screen"
    )
    target_text: Optional[str] = Field(
        None, description="Text to search for (used with screen_text_exists action)"
    )
    preprocess_config: Optional[Dict[str, Any]] = Field(
        None, description="OCR preprocessing configuration overrides"
    )
    engine: Optional[str] = Field(
        None, description="Specific OCR engine to use (tesseract, paddleocr, easyocr)"
    )
    min_confidence: Optional[float] = Field(
        0.3, description="Minimum confidence threshold for OCR results"
    )

class OCRTool(BaseTool):
    """LangChain tool for OCR operations."""

    name: str = "ocr"
    description: str = """Perform OCR (text recognition) on mobile screen.
Available actions:
- capture_and_read: Capture screen/region and extract all text
- read_region: Read text from specific screen region  
- screen_text_exists: Check if specific text exists on screen
- clear_cache: Clear OCR result cache
"""
    args_schema: Type[BaseModel] = OCRAction
    _driver: Any = PrivateAttr()
    _preprocessor = PrivateAttr()
    _ocr_manager = PrivateAttr()
    _screen_cache: Dict[str, Any] = PrivateAttr(default_factory=dict)


    def __init__(self, driver):
        super().__init__()
        self._driver = driver
        self._preprocessor = create_preprocessor()
        self._ocr_manager = get_ocr_manager()

    def _run(self, action: str, region: Optional[Tuple[int, int, int, int]] = None,
             target_text: Optional[str] = None, 
             preprocess_config: Optional[Dict[str, Any]] = None,
             engine: Optional[str] = None,
             min_confidence: float = 0.3) -> str:
        """Execute OCR action with logging."""

        start_time = time.time()
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Print tool call banner
        args_summary = f"action={action}"
        if region:
            args_summary += f", region={region}"
        if target_text:
            args_summary += f", target='{target_text[:20]}...'" if len(target_text) > 20 else f", target='{target_text}'"
        if engine:
            args_summary += f", engine={engine}"
        if min_confidence != 0.3:
            args_summary += f", confidence>={min_confidence}"

        print(f"👁️ [{timestamp}] >>> TOOL CALL: ocr({args_summary})")

        try:
            result = self._execute_ocr_action(action, region, target_text, 
                                            preprocess_config, engine, min_confidence)
            duration = int((time.time() - start_time) * 1000)

            print(f"✅ [{timestamp}] <<< TOOL RESULT: {result['status']} in {duration}ms - {result['message']}")

            return f"OCR: {action} | Status: {result['status']} | Message: {result['message']} | Duration: {duration}ms"

        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            error_msg = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)

            print(f"❌ [{timestamp}] <<< TOOL ERROR: {error_msg} in {duration}ms")

            return f"OCR: {action} | Status: ERROR | Message: {error_msg} | Duration: {duration}ms"

    def _execute_ocr_action(self, action: str, region: Optional[Tuple[int, int, int, int]],
                           target_text: Optional[str], preprocess_config: Optional[Dict[str, Any]],
                           engine: Optional[str], min_confidence: float) -> Dict[str, Any]:
        """Execute the specific OCR action."""

        if action == "capture_and_read":
            return self._capture_and_read(region, preprocess_config, engine, min_confidence)

        elif action == "read_region":
            if not region:
                return {"status": "ERROR", "message": "Region parameter required for read_region action"}
            return self._capture_and_read(region, preprocess_config, engine, min_confidence)

        elif action == "screen_text_exists":
            if not target_text:
                return {"status": "ERROR", "message": "target_text parameter required for screen_text_exists"}
            return self._check_text_exists(target_text, region, preprocess_config, engine, min_confidence)

        elif action == "clear_cache":
            self._ocr_manager.clear_cache()
            self._screen_cache.clear()
            return {"status": "SUCCESS", "message": "OCR caches cleared"}

        else:
            return {"status": "ERROR", "message": f"Unknown OCR action: {action}"}

    def _capture_and_read(self, region: Optional[Tuple[int, int, int, int]], 
                         preprocess_config: Optional[Dict[str, Any]],
                         engine: Optional[str], min_confidence: float) -> Dict[str, Any]:
        """Capture screen/region and perform OCR."""

        # Capture screenshot
        screenshot_data = self._driver.get_screenshot_as_png()

        # Generate cache key
        region_str = str(region) if region else "fullscreen"
        config_str = str(preprocess_config) if preprocess_config else "default"
        cache_key = hashlib.md5(f"{region_str}_{config_str}".encode()).hexdigest()[:16]

        # Check cache
        screenshot_hash = hashlib.md5(screenshot_data).hexdigest()[:16]
        full_cache_key = f"{screenshot_hash}_{cache_key}"

        if full_cache_key in self._screen_cache:
            cached_result = self._screen_cache[full_cache_key]
            print(f"⚡ [OCR] Cache hit for {region_str}")
            return {
                "status": "SUCCESS",
                "message": f"OCR result from cache: '{cached_result['text'][:50]}...'" if len(cached_result['text']) > 50 else f"OCR result from cache: '{cached_result['text']}'",
                "text": cached_result['text'],
                "confidence": cached_result['confidence'],
                "cached": True
            }

        # Preprocess image
        if region:
            processed_image, metadata = self._preprocessor.preprocess_region(
                screenshot_data, region, preprocess_config
            )
        else:
            processed_image, metadata = self._preprocessor.preprocess_for_ocr(
                screenshot_data, preprocess_config
            )

        # Perform OCR
        if engine:
            ocr_result = self._ocr_manager.recognize_with_engine(processed_image, engine)
        else:
            ocr_result = self._ocr_manager.recognize_with_fallback(processed_image, min_confidence)

        # Cache result
        cache_data = {
            "text": ocr_result.text,
            "confidence": ocr_result.confidence,
            "engine": ocr_result.engine
        }
        self._screen_cache[full_cache_key] = cache_data

        # Clean cache if too large
        if len(self._screen_cache) > 20:
            # Remove oldest entries
            old_keys = list(self._screen_cache.keys())[:5]
            for key in old_keys:
                del self._screen_cache[key]

        result_text = ocr_result.text or "No text found"
        confidence_pct = int(ocr_result.confidence * 100)

        return {
            "status": "SUCCESS" if ocr_result.text else "NO_TEXT",
            "message": f"OCR by {ocr_result.engine} ({confidence_pct}% confidence): '{result_text[:50]}...'" if len(result_text) > 50 else f"OCR by {ocr_result.engine} ({confidence_pct}% confidence): '{result_text}'",
            "text": ocr_result.text,
            "confidence": ocr_result.confidence,
            "engine": ocr_result.engine,
            "word_count": ocr_result.word_count
        }

    def _check_text_exists(self, target_text: str, region: Optional[Tuple[int, int, int, int]],
                          preprocess_config: Optional[Dict[str, Any]], engine: Optional[str],
                          min_confidence: float) -> Dict[str, Any]:
        """Check if specific text exists on screen."""

        ocr_result = self._capture_and_read(region, preprocess_config, engine, min_confidence)

        if ocr_result["status"] == "ERROR":
            return ocr_result

        extracted_text = ocr_result.get("text", "").lower()
        target_lower = target_text.lower()

        exists = target_lower in extracted_text

        return {
            "status": "SUCCESS",
            "message": f"Text '{target_text}' {'found' if exists else 'not found'} on screen",
            "text_exists": exists,
            "extracted_text": ocr_result.get("text", ""),
            "confidence": ocr_result.get("confidence", 0.0)
        }

    async def _arun(self, *args, **kwargs):
        """Async version not implemented."""
        raise NotImplementedError("OCR tool does not support async execution")

def create_ocr_tool(driver) -> OCRTool:
    """Factory function to create OCR tool with driver."""
    return OCRTool(driver)

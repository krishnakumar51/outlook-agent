#!/usr/bin/env python3
"""
UPDATED Mobile UI Tool - Added COMP.PY name typing methods
CRITICAL: Added new actions: get_elements, type_element_index
These support the EXACT comp.py name field logic:
- Direct element access: edit_texts[0], edit_texts[1]  
- UiSelector fallback: instance(1)
"""

from typing import Type, Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
import time
from datetime import datetime
from pydantic import PrivateAttr
from tools.mobile_ui import MobileUI

class MobileUIAction(BaseModel):
    """Input schema for mobile UI tool actions."""
    
    action: Literal[
        "click", "type", "exists", "wait_for", "clear", "next_button", 
        "find_elements", "get_elements", "type_element_index"
    ] = Field(
        ..., description="Action to perform: click, type, exists, wait_for, clear, next_button, find_elements, get_elements, type_element_index"
    )
    
    # Locator optional to support next_button
    locator: Optional[str] = Field(None, description="Element locator (xpath, class, id, etc.)")
    text: Optional[str] = Field(None, description="Text to type (required for 'type' action)")
    strategy: Optional[str] = Field("xpath", description="Locator strategy: xpath, class, id, uiautomator")
    timeout: int = Field(10, description="Timeout in seconds", ge=1, le=60)
    description: Optional[str] = Field(None, description="Human readable description of the action")
    
    # NEW: For COMP.PY method - element index selection
    element_index: Optional[int] = Field(None, description="Element index for type_element_index action (0=first, 1=second)")

class MobileUITool(BaseTool):
    """LangChain tool for mobile UI interactions."""
    
    name: str = "mobile_ui"
    description: str = """Perform mobile UI actions via Appium driver.

Available actions:
- click: Click on an element
- type: Type text into an element  
- exists: Check if element exists
- wait_for: Wait for element to appear
- clear: Clear text from element
- next_button: Click next/continue button
- find_elements: Find multiple elements
- get_elements: Get all elements matching locator (COMP.PY METHOD)
- type_element_index: Type in specific element by index (COMP.PY METHOD)
"""
    
    args_schema: Type[BaseModel] = MobileUIAction
    _ui: MobileUI = PrivateAttr()
    _driver: Any = PrivateAttr()
    _cached_elements: Dict[str, Any] = PrivateAttr(default_factory=dict)

    def __init__(self, driver):
        super().__init__()
        self._driver = driver
        self._ui = MobileUI(driver)
        self._cached_elements = {}

    def _run(self, action: str, locator: Optional[str] = None, text: Optional[str] = None,
             strategy: str = "xpath", timeout: int = 10, description: Optional[str] = None,
             element_index: Optional[int] = None) -> str:
        """Perform the UI action with structured logging."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        action_desc = description or f"{action} action"
        start_time = time.time()

        try:
            if action == "click":
                if not locator:
                    return self._format_error("click", "Locator is required for click action")
                success = self._ui.ui_click(locator, strategy, action_desc)
                message = f"Clicked: {action_desc}" if success else f"Failed to click: {action_desc}"

            elif action == "type":
                if not locator or not text:
                    return self._format_error("type", "Both locator and text are required for type action")
                success = self._ui.ui_type_text(locator, text, strategy=strategy, description=action_desc)
                message = f"Typed: {action_desc} = '{text[:20]}{'...' if len(text) > 20 else ''}''" if success else f"Failed to type: {action_desc}"

            elif action == "exists":
                if not locator:
                    return self._format_error("exists", "Locator is required for exists action")
                success = self._ui.ui_exists(locator, strategy=strategy)
                message = f"Element exists: {action_desc}" if success else f"Element not found: {action_desc}"

            elif action == "wait_for":
                if not locator:
                    return self._format_error("wait_for", "Locator is required for wait_for action")
                success = self._ui.ui_wait_for(locator, strategy=strategy, timeout=timeout)
                message = f"Element appeared: {action_desc}" if success else f"Element timeout: {action_desc}"

            elif action == "clear":
                if not locator:
                    return self._format_error("clear", "Locator is required for clear action")
                success = self._ui.ui_clear(locator, strategy=strategy)
                message = f"Cleared: {action_desc}" if success else f"Failed to clear: {action_desc}"

            elif action == "next_button":
                success = self._ui.click_next_button(description or "Next button")
                message = f"Clicked next button" if success else f"Failed to click next button"

            elif action == "find_elements":
                if not locator:
                    return self._format_error("find_elements", "Locator is required for find_elements action")
                elements = self._ui.ui_find_elements(locator, strategy=strategy)
                success = elements is not None and len(elements) > 0
                count = len(elements) if elements else 0
                message = f"Found {count} elements: {action_desc}" if success else f"No elements found: {action_desc}"

            # NEW: COMP.PY METHOD - Get elements and cache them
            elif action == "get_elements":
                if not locator:
                    return self._format_error("get_elements", "Locator is required for get_elements action")
                
                try:
                    # Find all elements using MobileUI
                    elements = self._ui.ui_find_elements(locator, strategy=strategy)
                    
                    if elements and len(elements) >= 2:
                        # Cache elements for later type_element_index usage
                        cache_key = f"{locator}_{strategy}"
                        self._cached_elements[cache_key] = elements
                        
                        success = True
                        count = len(elements)
                        message = f"Found {count} elements, cached for COMP.PY method: {action_desc}"
                    else:
                        success = False
                        count = len(elements) if elements else 0
                        message = f"Insufficient elements ({count}) for COMP.PY method: {action_desc}"
                        
                except Exception as e:
                    success = False
                    message = f"Error getting elements: {e}"

            # NEW: COMP.PY METHOD - Type in specific element by index
            elif action == "type_element_index":
                if not locator or not text or element_index is None:
                    return self._format_error("type_element_index", "locator, text, and element_index are required")
                
                try:
                    cache_key = f"{locator}_{strategy}"
                    
                    # Try cached elements first
                    elements = self._cached_elements.get(cache_key)
                    
                    # If no cache, find fresh elements
                    if not elements:
                        elements = self._ui.ui_find_elements(locator, strategy=strategy)
                        if elements:
                            self._cached_elements[cache_key] = elements
                    
                    if elements and len(elements) > element_index:
                        target_element = elements[element_index]
                        
                        # COMP.PY METHOD: Click, clear, then type
                        try:
                            # Focus on element
                            target_element.click()
                            time.sleep(0.5)
                            
                            # Clear using backspace (comp.py method)
                            try:
                                target_element.clear()
                            except:
                                # Fallback: backspace clear
                                for _ in range(10):
                                    self._driver.press_keycode(67)  # DEL key
                                    time.sleep(0.02)
                            
                            time.sleep(0.3)
                            
                            # Type text
                            target_element.send_keys(str(text))
                            success = True
                            message = f"COMP.PY METHOD: Typed '{text}' in element[{element_index}]: {action_desc}"
                            
                        except Exception as e:
                            # ADB fallback (comp.py style)
                            try:
                                import subprocess
                                subprocess.run(['adb', 'shell', 'input', 'text', str(text)], timeout=8, check=False)
                                success = True
                                message = f"COMP.PY ADB FALLBACK: Typed '{text}' in element[{element_index}]: {action_desc}"
                            except:
                                success = False
                                message = f"Failed to type in element[{element_index}]: {e}"
                                
                    else:
                        success = False
                        element_count = len(elements) if elements else 0
                        message = f"Element index {element_index} not available (found {element_count} elements): {action_desc}"
                        
                except Exception as e:
                    success = False
                    message = f"Error in type_element_index: {e}"

            else:
                return self._format_error("unknown", f"Unknown action '{action}'")

            duration_ms = int((time.time() - start_time) * 1000)
            status = "SUCCESS" if success else "FAILED"
            return f"Action: {action} | Status: {status} | Message: {message} | Duration: {duration_ms}ms"

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return f"Action: {action} | Status: ERROR | Message: Exception - {str(e)} | Duration: {duration_ms}ms"

    def _format_error(self, action: str, error_msg: str) -> str:
        """Format error message consistently."""
        return f"Action: {action} | Status: ERROR | Message: {error_msg} | Duration: 0ms"

    async def _arun(self, *args, **kwargs):
        """Async execution not supported."""
        raise NotImplementedError("Mobile UI tool does not support async execution")

def create_mobile_ui_tool(driver) -> MobileUITool:
    """Create MobileUITool instance."""
    return MobileUITool(driver)
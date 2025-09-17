#!/usr/bin/env python3
"""
Mobile UI Tool - LangChain tool wrapper for Appium mobile UI operations
Wraps existing MobileUI class with structured logging and tool interface
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
    action: Literal["click", "type", "exists", "wait_for", "clear", "next_button", "find_elements"] = Field(
        ..., description="Action to perform: click, type, exists, wait_for, clear, next_button, find_elements"
    )
    # Locator optional to support next_button
    locator: Optional[str] = Field(None, description="Element locator (xpath, class, id, etc.)")
    text: Optional[str] = Field(None, description="Text to type (required for 'type' action)")
    strategy: Optional[str] = Field("xpath", description="Locator strategy: xpath, class, id, uiautomator")
    timeout: int = Field(10, description="Timeout in seconds", ge=1, le=60)
    description: Optional[str] = Field(None, description="Human readable description of the action")

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
"""
    args_schema: Type[BaseModel] = MobileUIAction

    _ui: MobileUI = PrivateAttr()
    _driver: Any = PrivateAttr()

    def __init__(self, driver):
        super().__init__()
        self._driver = driver
        self._ui = MobileUI(driver)

    def _run(self, action: str, locator: Optional[str] = None, text: Optional[str] = None,
             strategy: str = "xpath", timeout: int = 10, description: Optional[str] = None) -> str:
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
                # FIX: use ui_type_text which exists in MobileUI
                success = self._ui.ui_type_text(locator, text, strategy=strategy, description=action_desc)
                message = f"Typed: {action_desc} = '{text[:20]}{'...' if len(text) > 20 else ''}'" if success else f"Failed to type: {action_desc}"

            elif action == "exists":
                if not locator:
                    return self._format_error("exists", "Locator is required for exists action")
                # Call shim wrapper for clarity
                success = self._ui.ui_exists(locator, strategy=strategy)
                message = f"Element exists: {action_desc}" if success else f"Element not found: {action_desc}"

            elif action == "wait_for":
                if not locator:
                    return self._format_error("wait_for", "Locator is required for wait_for action")
                # Default wait condition = visible
                success = self._ui.ui_wait_for(locator, strategy=strategy, timeout=timeout)
                message = f"Element appeared: {action_desc}" if success else f"Element timeout: {action_desc}"

            elif action == "clear":
                if not locator:
                    return self._format_error("clear", "Locator is required for clear action")
                success = self._ui.ui_clear(locator, strategy=strategy)
                message = f"Cleared: {action_desc}" if success else f"Failed to clear: {action_desc}"

            elif action == "next_button":
                # next_button doesn't need locator
                success = self._ui.click_next_button(description or "Next button")
                message = f"Clicked next button" if success else f"Failed to click next button"

            elif action == "find_elements":
                if not locator:
                    return self._format_error("find_elements", "Locator is required for find_elements action")
                elements = self._ui.ui_find_elements(locator, strategy=strategy)
                success = elements is not None and len(elements) > 0
                count = len(elements) if elements else 0
                message = f"Found {count} elements: {action_desc}" if success else f"No elements found: {action_desc}"

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

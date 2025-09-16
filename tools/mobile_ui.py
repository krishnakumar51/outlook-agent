#!/usr/bin/env python3
"""
Generic Mobile UI Tools for Appium Automation
Based on proven comp.py patterns - bulletproof element finding and interaction
Reusable across Outlook, IMSS, and other mobile apps
"""

import time
import subprocess
from typing import Optional, List, Any, Dict, Union
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

class MobileUI:
    """Generic mobile UI automation tools with bulletproof patterns"""

    def __init__(self, driver):
        self.driver = driver
        self.screen_size = driver.get_window_size()

    def ui_find_elements(self, selector: str, strategy: str = "xpath", 
                        timeout: int = 10, retry_attempts: int = 3) -> List[Any]:
        """
        Bulletproof element finding that always refreshes and filters for displayed elements
        Based on comp.py find_elements_bulletproof pattern

        Args:
            selector: Element selector string
            strategy: Selection strategy (xpath, id, class, uiautomator)
            timeout: Maximum wait time per attempt
            retry_attempts: Number of retry attempts

        Returns:
            List of displayed elements
        """
        by_map = {
            "xpath": AppiumBy.XPATH,
            "id": AppiumBy.ID, 
            "class": AppiumBy.CLASS_NAME,
            "uiautomator": AppiumBy.ANDROID_UIAUTOMATOR
        }

        by = by_map.get(strategy, AppiumBy.XPATH)

        for attempt in range(retry_attempts):
            try:
                elements = WebDriverWait(self.driver, timeout).until(
                    lambda d: d.find_elements(by, selector)
                )

                if elements:
                    # Filter for displayed elements (comp.py pattern)
                    visible_elements = []
                    for elem in elements:
                        try:
                            if elem.is_displayed():
                                visible_elements.append(elem)
                        except StaleElementReferenceException:
                            continue
                        except Exception:
                            # Include element if display check fails
                            visible_elements.append(elem)

                    if visible_elements:
                        return visible_elements

                time.sleep(0.5)

            except TimeoutException:
                if attempt < retry_attempts - 1:
                    print(f"⚠️ Element not found, retry {attempt + 1}/{retry_attempts}")
                    time.sleep(0.5)
            except Exception as e:
                if attempt < retry_attempts - 1:
                    print(f"⚠️ Find error, retry {attempt + 1}/{retry_attempts}: {e}")
                    time.sleep(0.5)

        return []

    def ui_find_one(self, selector: str, strategy: str = "xpath",
                   timeout: int = 10, retry_attempts: int = 3) -> Optional[Any]:
        """
        Find single element using bulletproof pattern

        Args:
            selector: Element selector string
            strategy: Selection strategy
            timeout: Maximum wait time
            retry_attempts: Number of retry attempts

        Returns:
            First displayed element or None
        """
        elements = self.ui_find_elements(selector, strategy, timeout, retry_attempts)
        return elements[0] if elements else None

    def ui_click(self, selector: str, strategy: str = "xpath", description: str = "",
                attempts: int = 3, timeout: int = 8) -> bool:
        """
        Bulletproof element clicking with fresh element lookup each attempt
        Based on comp.py click_element_bulletproof pattern

        Args:
            selector: Element selector
            strategy: Selection strategy  
            description: Description for logging
            attempts: Number of click attempts
            timeout: Element find timeout

        Returns:
            True if click succeeded, False otherwise
        """
        for attempt in range(attempts):
            try:
                element = self.ui_find_one(selector, strategy, timeout=timeout)
                if not element:
                    print(f"❌ Element not found for click: {description}")
                    return False

                # Try to click
                element.click()
                print(f"✅ Clicked: {description}")
                time.sleep(1)
                return True

            except StaleElementReferenceException:
                print(f"⚠️ Stale element, retry {attempt + 1}/{attempts}: {description}")
                time.sleep(0.5)
                continue
            except Exception as e:
                print(f"⚠️ Click failed, retry {attempt + 1}/{attempts}: {description} - {e}")
                time.sleep(0.5)
                continue

        print(f"❌ Click failed after {attempts} attempts: {description}")
        return False

    def ui_type_text(self, selector: str, text: str, strategy: str = "xpath",
                    field_type: Optional[str] = None, clear_strategy: str = "auto",
                    description: str = "", adb_fallback: bool = True) -> bool:
        """
        Bulletproof text input with special handling for different field types
        Based on comp.py type_text_bulletproof pattern with year field fix

        Args:
            selector: Element selector
            text: Text to type
            strategy: Selection strategy
            field_type: Field type hint (email, password, year, etc.)
            clear_strategy: Clearing method (auto, backspace, element_clear)
            description: Description for logging
            adb_fallback: Use ADB fallback if send_keys fails

        Returns:
            True if typing succeeded, False otherwise
        """
        for attempt in range(3):
            try:
                # Always find fresh element
                element = self.ui_find_one(selector, strategy, timeout=8)
                if not element:
                    print(f"❌ Element not found for typing: {description}")
                    return False

                # Focus on element
                element.click()
                time.sleep(0.5)

                # Handle clearing based on field type and strategy
                if field_type == "year" or clear_strategy == "backspace":
                    print(f"Using backspace clearing for: {description}")
                    # CRITICAL: Use backspace clearing for year field to avoid ACTION_SET_PROGRESS
                    for _ in range(15):
                        self.driver.press_keycode(67)  # DEL key
                        time.sleep(0.02)
                    time.sleep(0.3)

                elif clear_strategy == "auto":
                    try:
                        element.clear()
                        time.sleep(0.3)
                    except:
                        # Fallback to backspace
                        current_text = element.get_attribute("text") or ""
                        for _ in range(len(current_text) + 5):
                            self.driver.press_keycode(67)
                            time.sleep(0.02)
                        time.sleep(0.3)

                # Input text
                try:
                    element.send_keys(str(text))
                    print(f"✅ Typed: {description} = '{text}'")
                    time.sleep(0.5)
                    return True
                except Exception:
                    if adb_fallback:
                        # ADB fallback for text input
                        subprocess.run(['adb', 'shell', 'input', 'text', str(text)],
                                     timeout=8, check=False)
                        print(f"✅ Typed (ADB): {description} = '{text}'")
                        time.sleep(0.5)
                        return True

            except StaleElementReferenceException:
                if attempt < 2:
                    print(f"⚠️ Stale element, retry {attempt + 1}/3: {description}")
                    time.sleep(1)
                    continue
            except Exception as e:
                print(f"⚠️ Type failed, retry {attempt + 1}/3: {description} - {e}")
                if attempt < 2:
                    time.sleep(1)
                    continue

        print(f"❌ Type failed after 3 attempts: {description}")
        return False

    def ui_select_dropdown(self, dropdown_selector: str, option_text: str,
                          strategy: str = "xpath", description: str = "",
                          timeout: int = 5) -> bool:
        """
        Select option from dropdown menu

        Args:
            dropdown_selector: Dropdown element selector
            option_text: Text of option to select
            strategy: Selection strategy
            description: Description for logging
            timeout: Timeout for finding elements

        Returns:
            True if selection succeeded, False otherwise
        """
        try:
            # Click dropdown to open
            if not self.ui_click(dropdown_selector, strategy, f"{description} Dropdown"):
                return False

            time.sleep(1)

            # Find and click option
            option_selector = f"//*[@text='{option_text}']"
            option_element = self.ui_find_one(option_selector, "xpath", timeout=timeout)

            if option_element:
                try:
                    option_element.click()
                    print(f"✅ Selected {description}: {option_text}")
                    time.sleep(1)
                    return True
                except StaleElementReferenceException:
                    # Refind and click
                    option_element = self.ui_find_one(option_selector, "xpath", timeout=3)
                    if option_element:
                        option_element.click()
                        print(f"✅ Selected {description} (retry): {option_text}")
                        time.sleep(1)
                        return True

            print(f"❌ Option not found: {option_text}")
            return False

        except Exception as e:
            print(f"❌ Dropdown selection failed: {description} - {e}")
            return False

    def ui_wait_element(self, selector: str, strategy: str = "xpath",
                       condition: str = "visible", timeout: int = 10) -> bool:
        """
        Wait for element to meet condition

        Args:
            selector: Element selector
            strategy: Selection strategy
            condition: Wait condition (visible, present, gone)
            timeout: Maximum wait time

        Returns:
            True if condition met, False if timeout
        """
        try:
            if condition == "visible":
                element = self.ui_find_one(selector, strategy, timeout=timeout, retry_attempts=1)
                return element is not None
            elif condition == "gone":
                # Wait for element to disappear
                start_time = time.time()
                while time.time() - start_time < timeout:
                    element = self.ui_find_one(selector, strategy, timeout=1, retry_attempts=1)
                    if not element:
                        return True
                    time.sleep(0.5)
                return False
            else:  # present
                elements = self.ui_find_elements(selector, strategy, timeout=timeout, retry_attempts=1)
                return len(elements) > 0

        except Exception:
            return False

    def ui_hide_keyboard(self) -> bool:
        """Hide soft keyboard if visible"""
        try:
            self.driver.hide_keyboard()
            time.sleep(0.5)
            return True
        except:
            return False

    def ui_press_keycode(self, keycode: int) -> bool:
        """Press Android keycode (66=ENTER, 67=DEL, etc.)"""
        try:
            self.driver.press_keycode(keycode)
            time.sleep(0.5)
            return True
        except:
            return False

    def ui_tap_coordinates(self, x: int, y: int) -> bool:
        """Tap at specific coordinates"""
        try:
            self.driver.tap([(x, y)])
            time.sleep(1)
            return True
        except:
            return False

    def click_next_button(self, context: str = "") -> bool:
        """
        Production Next button clicking with multiple strategies
        Based on comp.py click_next_production pattern
        """
        strategies = [
            ('new UiSelector().textContains("Next").clickable(true).enabled(true)', "uiautomator"),
            ("//*[contains(@text, 'Next')]", "xpath"),
            ("//android.widget.Button[contains(@text, 'Next')]", "xpath")
        ]

        for selector, strategy in strategies:
            if self.ui_click(selector, strategy, f"Next ({context})"):
                return True

        # ENTER fallback
        try:
            self.driver.press_keycode(66)  # ENTER key
            time.sleep(1)
            print("✅ ENTER key pressed as Next fallback")
            return True
        except:
            pass

        print(f"❌ Next button not found: {context}")
        return False

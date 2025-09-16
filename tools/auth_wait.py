#!/usr/bin/env python3
"""
Authentication Progress Waiting Tools
Based on comp.py wait_authentication pattern - polls progress bars
"""

import time
from typing import Optional
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import StaleElementReferenceException

class AuthenticationWaiter:
    """Wait for authentication and progress indicators"""

    def __init__(self, driver):
        self.driver = driver

    def ui_wait_progress_gone(self, progress_class: str = "android.widget.ProgressBar",
                             max_seconds: int = 90, check_interval: float = 2.0) -> bool:
        """
        Wait for authentication by monitoring progress bars
        Based on comp.py wait_authentication pattern

        Args:
            progress_class: Progress bar class name to monitor
            max_seconds: Maximum wait time
            check_interval: Check interval in seconds

        Returns:
            True when progress bars are gone or timeout
        """
        print(f"⏳ Waiting for authentication (max {max_seconds}s)...")

        start_time = time.time()
        iterations = int(max_seconds / check_interval)

        for i in range(iterations):
            try:
                # Find all progress bar elements
                progress_bars = self.driver.find_elements(AppiumBy.CLASS_NAME, progress_class)

                # Filter for visible progress bars
                visible_bars = []
                for bar in progress_bars:
                    try:
                        if bar.is_displayed():
                            visible_bars.append(bar)
                    except StaleElementReferenceException:
                        continue
                    except Exception:
                        continue

                # If no visible progress bars, authentication is complete
                if not visible_bars:
                    elapsed = time.time() - start_time
                    print(f"✅ Authentication complete ({elapsed:.1f}s)")
                    time.sleep(3)  # Additional settle time
                    return True

                # Log progress
                if i % 5 == 0:  # Log every 10 seconds
                    elapsed = time.time() - start_time
                    print(f"⏳ Still waiting... ({elapsed:.1f}s, {len(visible_bars)} progress bars)")

            except Exception as e:
                print(f"⚠️ Progress check error: {e}")

            time.sleep(check_interval)

        # Timeout reached
        elapsed = time.time() - start_time
        print(f"⚠️ Authentication timeout ({elapsed:.1f}s), continuing anyway")
        return True  # Continue even on timeout

    def ui_wait_loading_gone(self, loading_indicators: list = None,
                           max_seconds: int = 30) -> bool:
        """
        Wait for various loading indicators to disappear

        Args:
            loading_indicators: List of loading element selectors
            max_seconds: Maximum wait time

        Returns:
            True when loading is complete
        """
        if loading_indicators is None:
            loading_indicators = [
                "android.widget.ProgressBar",
                "//*[contains(@text, 'Loading')]",
                "//*[contains(@text, 'Please wait')]"
            ]

        print(f"⏳ Waiting for loading to complete (max {max_seconds}s)...")

        start_time = time.time()

        while time.time() - start_time < max_seconds:
            loading_found = False

            for indicator in loading_indicators:
                try:
                    if indicator.startswith("android.widget."):
                        # Class name selector
                        elements = self.driver.find_elements(AppiumBy.CLASS_NAME, indicator)
                    else:
                        # XPath selector
                        elements = self.driver.find_elements(AppiumBy.XPATH, indicator)

                    # Check if any are visible
                    for element in elements:
                        try:
                            if element.is_displayed():
                                loading_found = True
                                break
                        except StaleElementReferenceException:
                            continue
                        except:
                            continue

                    if loading_found:
                        break

                except Exception:
                    continue

            if not loading_found:
                elapsed = time.time() - start_time
                print(f"✅ Loading complete ({elapsed:.1f}s)")
                return True

            time.sleep(1)

        elapsed = time.time() - start_time
        print(f"⚠️ Loading timeout ({elapsed:.1f}s), continuing")
        return True

    def ui_wait_text_present(self, text: str, max_seconds: int = 30) -> bool:
        """
        Wait for specific text to appear on screen

        Args:
            text: Text to wait for
            max_seconds: Maximum wait time

        Returns:
            True if text appears, False on timeout
        """
        print(f"⏳ Waiting for text: '{text}' (max {max_seconds}s)")

        start_time = time.time()

        while time.time() - start_time < max_seconds:
            try:
                # Search for text in various ways
                selectors = [
                    f"//*[@text='{text}']",
                    f"//*[contains(@text, '{text}')]", 
                    f"//*[contains(@content-desc, '{text}')]"
                ]

                for selector in selectors:
                    elements = self.driver.find_elements(AppiumBy.XPATH, selector)
                    for element in elements:
                        try:
                            if element.is_displayed():
                                elapsed = time.time() - start_time
                                print(f"✅ Text found: '{text}' ({elapsed:.1f}s)")
                                return True
                        except:
                            continue

            except Exception:
                pass

            time.sleep(1)

        elapsed = time.time() - start_time
        print(f"❌ Text not found: '{text}' ({elapsed:.1f}s)")
        return False

    def ui_wait_text_gone(self, text: str, max_seconds: int = 30) -> bool:
        """
        Wait for specific text to disappear from screen

        Args:
            text: Text to wait for disappearance
            max_seconds: Maximum wait time

        Returns:
            True when text is gone, False on timeout
        """
        print(f"⏳ Waiting for text to disappear: '{text}' (max {max_seconds}s)")

        start_time = time.time()

        while time.time() - start_time < max_seconds:
            try:
                # Check if text is still present
                text_found = False
                selectors = [
                    f"//*[@text='{text}']",
                    f"//*[contains(@text, '{text}')]"
                ]

                for selector in selectors:
                    elements = self.driver.find_elements(AppiumBy.XPATH, selector)
                    for element in elements:
                        try:
                            if element.is_displayed():
                                text_found = True
                                break
                        except:
                            continue
                    if text_found:
                        break

                if not text_found:
                    elapsed = time.time() - start_time
                    print(f"✅ Text disappeared: '{text}' ({elapsed:.1f}s)")
                    return True

            except Exception:
                pass

            time.sleep(1)

        elapsed = time.time() - start_time
        print(f"⚠️ Text still present: '{text}' ({elapsed:.1f}s)")
        return False

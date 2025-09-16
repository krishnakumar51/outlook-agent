#!/usr/bin/env python3
"""
Post-Authentication Fast Path Navigation
Based on comp.py step7_post_captcha pattern - time-bounded navigation to inbox
"""

import time
from typing import List, Dict

class PostAuthNavigator:
    """Fast navigation through post-authentication pages to reach inbox"""

    def __init__(self, driver):
        self.driver = driver

    def post_auth_fast_path(self, inbox_probe_selectors: List[str] = None,
                           button_sets: Dict[str, List[str]] = None,
                           budget_seconds: float = 7.0) -> bool:
        """
        Fast path navigation through post-CAPTCHA pages to reach inbox
        Based on comp.py optimized pattern with time budget

        Args:
            inbox_probe_selectors: Selectors to check for inbox presence
            button_sets: Dictionary of button categories and their selectors
            budget_seconds: Maximum time budget for navigation

        Returns:
            True if inbox reached or navigation completed
        """
        from .mobile_ui import MobileUI
        ui = MobileUI(self.driver)

        # Default inbox probe selectors
        if inbox_probe_selectors is None:
            inbox_probe_selectors = [
                "//*[@text='Search']",
                "//*[contains(@content-desc,'Search')]",
                "//*[contains(@text, 'Inbox')]",
                "//*[contains(@content-desc, 'Inbox')]"
            ]

        # Default button sets based on comp.py patterns
        if button_sets is None:
            button_sets = {
                "maybe_later": [
                    "//*[@text='MAYBE LATER']",
                    "//*[contains(translate(@text,'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'MAYBE LATER')]",
                    "//*[contains(@text,'Maybe later')]",
                    "//*[contains(@content-desc,'Maybe later')]"
                ],
                "next": [
                    "//*[@text='NEXT']", 
                    "//*[contains(translate(@text,'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'NEXT')]",
                    "//*[contains(@text,'Next')]",
                    "//*[contains(@content-desc,'Next')]"
                ],
                "accept": [
                    "//*[@text='ACCEPT']",
                    "//*[contains(translate(@text,'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'ACCEPT')]", 
                    "//*[contains(@text,'Accept')]",
                    "//*[contains(@content-desc,'Accept')]"
                ],
                "continue": [
                    "//*[@text='CONTINUE TO OUTLOOK']",
                    "//*[contains(translate(@text,'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'CONTINUE TO OUTLOOK')]",
                    "//*[contains(@text,'Continue to Outlook')]",
                    "//*[contains(@content-desc,'Continue to Outlook')]"
                ],
                "skip": [
                    "//*[contains(@text,'Not now')]",
                    "//*[contains(@text,'Skip')]", 
                    "//*[contains(@text,'No thanks')]"
                ]
            }

        print(f"🚀 Starting post-auth fast path (budget: {budget_seconds}s)")

        def inbox_reached() -> bool:
            """Check if inbox is visible"""
            for selector in inbox_probe_selectors:
                element = ui.ui_find_one(selector, "xpath", timeout=1, retry_attempts=1)
                if element:
                    print(f"✅ Inbox detected: {selector}")
                    return True
            return False

        def quick_click(selectors: List[str]) -> bool:
            """Quick click with minimal timeout"""
            for selector in selectors:
                element = ui.ui_find_one(selector, "xpath", timeout=1, retry_attempts=1)
                if element:
                    try:
                        element.click()
                        print(f"✅ Quick clicked: {selector}")
                        time.sleep(0.6)  # Small settle time
                        return True
                    except Exception as e:
                        print(f"⚠️ Quick click failed: {e}")
                        continue
            return False

        # Start navigation with time budget
        start_time = time.time()
        passes = 0

        while time.time() - start_time < budget_seconds:
            passes += 1

            # Check if already at inbox
            if inbox_reached():
                elapsed = time.time() - start_time
                print(f"✅ Reached inbox! ({elapsed:.1f}s, {passes} passes)")
                return True

            # Try button sequences with inbox probes after each
            button_clicked = False

            # 1. Maybe Later (add another account?)
            if quick_click(button_sets["maybe_later"]):
                button_clicked = True
                if inbox_reached():
                    elapsed = time.time() - start_time
                    print(f"✅ Reached inbox after Maybe Later! ({elapsed:.1f}s)")
                    return True

            # 2. Next (Your Data, Your Way)
            if quick_click(button_sets["next"]):
                button_clicked = True
                if inbox_reached():
                    elapsed = time.time() - start_time
                    print(f"✅ Reached inbox after Next! ({elapsed:.1f}s)")
                    return True

            # 3. Accept (Getting Better Together)
            if quick_click(button_sets["accept"]):
                button_clicked = True
                if inbox_reached():
                    elapsed = time.time() - start_time
                    print(f"✅ Reached inbox after Accept! ({elapsed:.1f}s)")
                    return True

            # 4. Continue to Outlook (Powering Your Experiences)
            if quick_click(button_sets["continue"]):
                button_clicked = True
                if inbox_reached():
                    elapsed = time.time() - start_time
                    print(f"✅ Reached inbox after Continue! ({elapsed:.1f}s)")
                    return True

            # 5. Skip system dialogs
            quick_click(button_sets["skip"])

            # Adaptive pause - shorter if we clicked something
            if button_clicked:
                time.sleep(0.3)
            else:
                time.sleep(0.5)

        # Final inbox check before exit
        if inbox_reached():
            elapsed = time.time() - start_time
            print(f"✅ Reached inbox at final check! ({elapsed:.1f}s)")
            return True

        elapsed = time.time() - start_time
        print(f"⚠️ Post-auth navigation completed without inbox confirmation ({elapsed:.1f}s)")
        return True  # Continue workflow even if inbox not confirmed

    def navigate_to_inbox_simple(self, max_attempts: int = 8, attempt_delay: float = 1.0) -> bool:
        """
        Simple navigation attempt with common buttons
        Fallback method if fast path doesn't work

        Args:
            max_attempts: Maximum navigation attempts
            attempt_delay: Delay between attempts

        Returns:
            True if navigation completed
        """
        from .mobile_ui import MobileUI
        ui = MobileUI(self.driver)

        print(f"🔄 Simple inbox navigation (max {max_attempts} attempts)")

        # Common buttons to try
        buttons = [
            ("//*[contains(@text, 'MAYBE LATER')]", "MAYBE LATER"),
            ("//*[contains(@text, 'ACCEPT')]", "ACCEPT"), 
            ("//*[contains(@text, 'NEXT')]", "NEXT"),
            ("//*[contains(@text, 'CONTINUE TO OUTLOOK')]", "CONTINUE TO OUTLOOK"),
            ("//*[contains(@text, 'Skip')]", "SKIP"),
            ("//*[contains(@text, 'Not now')]", "NOT NOW")
        ]

        for attempt in range(max_attempts):
            print(f"📱 Navigation attempt {attempt + 1}/{max_attempts}")

            # Check for inbox first
            inbox_selectors = ["//*[contains(@text, 'Search')]", "//*[contains(@text, 'Inbox')]"]
            for selector in inbox_selectors:
                if ui.ui_find_one(selector, "xpath", timeout=1):
                    print(f"✅ Reached inbox (attempt {attempt + 1})")
                    return True

            # Try clicking buttons
            button_clicked = False
            for selector, desc in buttons:
                if ui.ui_click(selector, "xpath", desc, attempts=1, timeout=1):
                    button_clicked = True
                    time.sleep(attempt_delay)
                    break

            if not button_clicked:
                print(f"⚠️ No buttons found on attempt {attempt + 1}")

            time.sleep(attempt_delay)

        print("✅ Simple navigation completed")
        return True

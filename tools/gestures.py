#!/usr/bin/env python3
"""
Mobile Gesture Tools - Long press, swipe, tap
Special handling for CAPTCHA long press based on comp.py patterns
"""

import time
import subprocess
from typing import Optional, Tuple

class MobileGestures:
    """Mobile gesture automation with native and ADB fallbacks"""

    def __init__(self, driver):
        self.driver = driver
        self.screen_size = driver.get_window_size()

    def ui_long_press(self, target: str, duration_ms: int = 15000, 
                     strategy: str = "xpath", prefer_native: bool = True,
                     description: str = "Long Press") -> bool:
        """
        Long press gesture with native mobile gesture and ADB fallback
        Critical for CAPTCHA handling - based on comp.py step6_captcha pattern

        Args:
            target: Element selector or coordinates (x,y)
            duration_ms: Hold duration in milliseconds
            strategy: Selection strategy if target is selector
            prefer_native: Try native gesture first
            description: Description for logging

        Returns:
            True if long press succeeded, False otherwise
        """
        try:
            from .mobile_ui import MobileUI
            ui = MobileUI(self.driver)

            # If target is string, find element; if tuple, use coordinates
            if isinstance(target, str):
                element = ui.ui_find_one(target, strategy, timeout=8)
                if not element:
                    print(f"❌ Element not found for long press: {description}")
                    return False

                location = element.location
                size = element.size
                x = location['x'] + size['width'] // 2
                y = location['y'] + size['height'] // 2

                # Try native long press first (comp.py pattern)
                if prefer_native:
                    try:
                        self.driver.execute_script("mobile: longClickGesture", {
                            "elementId": element.id,
                            "duration": duration_ms
                        })
                        print(f"✅ Native long press ({duration_ms}ms): {description}")
                        time.sleep(4)
                        return True
                    except Exception as e:
                        print(f"⚠️ Native long press failed: {e}")

            elif isinstance(target, tuple):
                x, y = target
            else:
                print(f"❌ Invalid target type for long press: {type(target)}")
                return False

            # ADB fallback (comp.py swipe pattern for long press)
            try:
                subprocess.run([
                    "adb", "shell", "input", "touchscreen", "swipe",
                    str(x), str(y), str(x), str(y), str(duration_ms)
                ], check=False, timeout=duration_ms//1000 + 5)
                print(f"✅ ADB long press ({duration_ms}ms): {description}")
                time.sleep(4)
                return True
            except Exception as e:
                print(f"❌ ADB long press failed: {e}")

            # Coordinate fallback (comp.py coordinate pattern)
            screen_x = self.screen_size['width'] // 2
            screen_y = int(self.screen_size['height'] * 0.6)

            try:
                subprocess.run([
                    "adb", "shell", "input", "touchscreen", "swipe", 
                    str(screen_x), str(screen_y), str(screen_x), str(screen_y), str(duration_ms)
                ], check=False, timeout=duration_ms//1000 + 5)
                print(f"✅ Coordinate long press ({duration_ms}ms): {description}")
                time.sleep(4)
                return True
            except Exception as e:
                print(f"❌ Coordinate long press failed: {e}")

        except Exception as e:
            print(f"❌ Long press completely failed: {description} - {e}")

        return False

    def ui_swipe(self, start_x: int, start_y: int, end_x: int, end_y: int,
                duration_ms: int = 1000) -> bool:
        """
        Swipe gesture between two points

        Args:
            start_x, start_y: Start coordinates
            end_x, end_y: End coordinates  
            duration_ms: Swipe duration

        Returns:
            True if swipe succeeded
        """
        try:
            # Try native swipe first
            self.driver.swipe(start_x, start_y, end_x, end_y, duration_ms)
            print(f"✅ Swipe: ({start_x},{start_y}) → ({end_x},{end_y})")
            time.sleep(1)
            return True
        except:
            # ADB fallback
            try:
                subprocess.run([
                    "adb", "shell", "input", "touchscreen", "swipe",
                    str(start_x), str(start_y), str(end_x), str(end_y), str(duration_ms)
                ], check=False)
                print(f"✅ Swipe (ADB): ({start_x},{start_y}) → ({end_x},{end_y})")
                time.sleep(1)
                return True
            except Exception as e:
                print(f"❌ Swipe failed: {e}")
                return False

    def ui_scroll_down(self, distance_ratio: float = 0.5) -> bool:
        """
        Scroll down by ratio of screen height

        Args:
            distance_ratio: Scroll distance as ratio of screen height

        Returns:
            True if scroll succeeded
        """
        screen_width = self.screen_size['width']
        screen_height = self.screen_size['height']

        start_x = screen_width // 2
        start_y = int(screen_height * 0.7)
        end_x = screen_width // 2  
        end_y = int(screen_height * (0.7 - distance_ratio))

        return self.ui_swipe(start_x, start_y, end_x, end_y)

    def ui_scroll_up(self, distance_ratio: float = 0.5) -> bool:
        """
        Scroll up by ratio of screen height

        Args:
            distance_ratio: Scroll distance as ratio of screen height

        Returns:
            True if scroll succeeded
        """
        screen_width = self.screen_size['width']
        screen_height = self.screen_size['height']

        start_x = screen_width // 2
        start_y = int(screen_height * 0.3)
        end_x = screen_width // 2
        end_y = int(screen_height * (0.3 + distance_ratio))

        return self.ui_swipe(start_x, start_y, end_x, end_y)

    def ui_tap_center_screen(self) -> bool:
        """Tap center of screen"""
        x = self.screen_size['width'] // 2
        y = self.screen_size['height'] // 2

        try:
            self.driver.tap([(x, y)])
            print(f"✅ Tapped center: ({x},{y})")
            time.sleep(1)
            return True
        except Exception as e:
            print(f"❌ Center tap failed: {e}")
            return False

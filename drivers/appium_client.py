#!/usr/bin/env python3
"""
Appium Driver Client
Production-ready driver setup based on comp.py patterns
"""

import time
from typing import Optional, Dict, Any
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy

class AppiumClient:
    """Appium driver setup and lifecycle management"""

    def __init__(self, app_package: str = 'com.microsoft.office.outlook',
                 appium_url: str = "http://localhost:4723"):
        self.app_package = app_package
        self.appium_url = appium_url
        self.driver = None
        self.screen_size = None

    def setup_driver(self, app_activity: str = '.MainActivity') -> bool:
        """
        Setup Appium driver with production capabilities
        Based on comp.py setup_driver pattern

        Args:
            app_activity: App activity to launch

        Returns:
            True if driver setup successful, False otherwise
        """
        try:
            print(f"🚀 Setting up Appium driver for {self.app_package}...")

            # Setup UiAutomator2 options (comp.py pattern)
            options = UiAutomator2Options()
            options.platform_name = 'Android'
            options.device_name = 'Android'  
            options.app_package = self.app_package
            options.app_activity = app_activity
            options.automation_name = 'UiAutomator2'
            options.no_reset = False
            options.full_reset = False
            options.new_command_timeout = 300
            options.unicode_keyboard = True
            options.reset_keyboard = True
            options.auto_grant_permissions = True

            # Connect to Appium server
            self.driver = webdriver.Remote(self.appium_url, options=options)

            # Apply production settings (comp.py pattern)
            self.driver.update_settings({"enforceXPath1": True})

            # Get screen size for coordinate fallbacks
            self.screen_size = self.driver.get_window_size()

            print(f"✅ Driver ready - Screen: {self.screen_size['width']}x{self.screen_size['height']}")

            # Wait for app to launch
            time.sleep(4)

            return True

        except Exception as e:
            print(f"❌ Driver setup failed: {e}")
            return False

    def get_driver(self):
        """Get the Appium driver instance"""
        return self.driver

    def get_screen_size(self) -> Optional[Dict[str, int]]:
        """Get screen dimensions"""
        return self.screen_size

    def quit_driver(self) -> bool:
        """Quit the Appium driver safely"""
        try:
            if self.driver:
                self.driver.quit()
                print("✅ Driver quit successfully")
            return True
        except Exception as e:
            print(f"⚠️ Driver quit error: {e}")
            return False

    def restart_app(self) -> bool:
        """Restart the target app"""
        try:
            if self.driver:
                self.driver.activate_app(self.app_package)
                time.sleep(2)
                print(f"✅ App restarted: {self.app_package}")
                return True
        except Exception as e:
            print(f"❌ App restart failed: {e}")
            return False

    def close_app(self) -> bool:
        """Close the target app"""
        try:
            if self.driver:
                self.driver.terminate_app(self.app_package)
                time.sleep(1)
                print(f"✅ App closed: {self.app_package}")
                return True
        except Exception as e:
            print(f"❌ App close failed: {e}")
            return False

    def check_driver_health(self) -> bool:
        """Check if driver is still responsive"""
        try:
            if self.driver:
                # Simple health check
                self.driver.current_activity
                return True
        except:
            return False

    def get_device_info(self) -> Dict[str, Any]:
        """Get device information for debugging"""
        try:
            if self.driver:
                return {
                    "platform_name": self.driver.capabilities.get('platformName'),
                    "platform_version": self.driver.capabilities.get('platformVersion'),
                    "device_name": self.driver.capabilities.get('deviceName'),
                    "app_package": self.app_package,
                    "screen_size": self.screen_size,
                    "current_activity": self.driver.current_activity
                }
        except Exception as e:
            return {"error": str(e)}

        return {}

class OutlookAppiumClient(AppiumClient):
    """Specialized Appium client for Outlook app"""

    def __init__(self, appium_url: str = "http://localhost:4723"):
        super().__init__(
            app_package='com.microsoft.office.outlook',
            appium_url=appium_url
        )

    def setup_outlook_driver(self) -> bool:
        """Setup driver specifically for Outlook app"""
        return self.setup_driver('.MainActivity')

    def check_outlook_installed(self) -> bool:
        """Check if Outlook app is installed"""
        try:
            if self.driver:
                installed_apps = self.driver.query_app_state(self.app_package)
                return installed_apps != 0  # 0 = not installed
        except:
            pass
        return False

    def launch_outlook(self) -> bool:
        """Launch Outlook app if not already running"""
        try:
            if self.driver:
                self.driver.activate_app(self.app_package)
                time.sleep(3)
                print("✅ Outlook launched")
                return True
        except Exception as e:
            print(f"❌ Outlook launch failed: {e}")
            return False

# Convenience function for quick setup
def create_outlook_driver(appium_url: str = "http://localhost:4723") -> Optional[AppiumClient]:
    """
    Quick setup for Outlook automation

    Args:
        appium_url: Appium server URL

    Returns:
        Configured AppiumClient or None if setup failed
    """
    client = OutlookAppiumClient(appium_url)
    if client.setup_outlook_driver():
        return client
    return None

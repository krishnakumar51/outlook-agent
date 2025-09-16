#!/usr/bin/env python3
"""
Outlook Mobile App Selectors
Organized selector strategies for different Outlook screens and elements
"""

from typing import Dict, List

class OutlookSelectors:
    """Outlook mobile app element selectors with fallback strategies"""

    # Welcome/Startup Screen
    WELCOME_SCREEN = {
        "create_account": [
            "//*[contains(@text, 'CREATE NEW ACCOUNT')]",
            "//*[contains(@text, 'Create new account')]", 
            "//android.widget.Button[contains(@text, 'CREATE')]",
            "//*[contains(@content-desc, 'Create')]"
        ],
        "sign_in": [
            "//*[contains(@text, 'SIGN IN')]",
            "//*[contains(@text, 'Sign in')]"
        ]
    }

    # Email Input Screen
    EMAIL_SCREEN = {
        "email_field": [
            "//*[contains(@hint, 'email')]",
            "//*[contains(@hint, 'Email')]",
            "android.widget.EditText",
            "//*[contains(@content-desc, 'email')]"
        ],
        "next_button": [
            'new UiSelector().textContains("Next").clickable(true).enabled(true)',
            "//*[contains(@text, 'Next')]",
            "//android.widget.Button[contains(@text, 'Next')]"
        ]
    }

    # Password Screen
    PASSWORD_SCREEN = {
        "password_field": [
            "//*[contains(@hint, 'Password')]",
            "//*[contains(@hint, 'password')]",
            "android.widget.EditText",
            "//*[@content-desc='Password']"
        ],
        "next_button": [
            'new UiSelector().textContains("Next").clickable(true).enabled(true)',
            "//*[contains(@text, 'Next')]",
            "//android.widget.Button[contains(@text, 'Next')]"
        ]
    }

    # Personal Details Screen
    DETAILS_SCREEN = {
        "day_dropdown": [
            "//*[contains(@text, 'Day')]",
            "//*[contains(@hint, 'Day')]",
            "//android.widget.Spinner[1]",
            "//*[contains(@content-desc, 'Day')]"
        ],
        "month_dropdown": [
            "//*[contains(@text, 'Month')]", 
            "//*[contains(@hint, 'Month')]",
            "//android.widget.Spinner[2]",
            "//*[contains(@content-desc, 'Month')]"
        ],
        "year_field": [
            "android.widget.EditText",  # Will use last EditText
            "//*[contains(@hint, 'Year')]",
            "//*[contains(@hint, 'year')]"
        ],
        "next_button": [
            'new UiSelector().textContains("Next").clickable(true).enabled(true)',
            "//*[contains(@text, 'Next')]"
        ]
    }

    # Name Input Screen  
    NAME_SCREEN = {
        "first_name_field": [
            "android.widget.EditText",  # First EditText
            "//*[contains(@hint, 'First')]",
            "//*[contains(@hint, 'first')]"
        ],
        "last_name_field": [
            'new UiSelector().className("android.widget.EditText").instance(1)',
            "//*[contains(@hint, 'Last')]", 
            "//*[contains(@hint, 'last')]"
        ],
        "next_button": [
            'new UiSelector().textContains("Next").clickable(true).enabled(true)',
            "//*[contains(@text, 'Next')]"
        ]
    }

    # CAPTCHA Screen
    CAPTCHA_SCREEN = {
        "captcha_button": [
            'new UiSelector().className("android.widget.Button").textContains("Press").clickable(true).enabled(true)',
            "//android.widget.Button[contains(@text,'Press')]",
            "//*[contains(@text, 'Press and hold')]",
            "//*[contains(@content-desc, 'Press')]"
        ]
    }

    # Authentication Progress
    AUTH_PROGRESS = {
        "progress_bars": [
            "android.widget.ProgressBar"
        ],
        "loading_text": [
            "//*[contains(@text, 'Please wait')]",
            "//*[contains(@text, 'Loading')]",
            "//*[contains(@text, 'Authenticating')]"
        ]
    }

    # Post-Authentication Pages
    POST_AUTH = {
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
            "//*[contains(@text,'No thanks')]",
            "//*[contains(@text,'Maybe later')]"
        ]
    }

    # Inbox/Success Indicators
    INBOX_SCREEN = {
        "search": [
            "//*[@text='Search']",
            "//*[contains(@content-desc,'Search')]", 
            "//*[contains(@text, 'Search')]"
        ],
        "inbox": [
            "//*[contains(@text, 'Inbox')]",
            "//*[contains(@content-desc, 'Inbox')]"
        ],
        "compose": [
            "//*[contains(@text, 'Compose')]",
            "//*[contains(@content-desc, 'Compose')]"
        ]
    }

    @classmethod
    def get_selectors(cls, screen: str, element: str) -> List[str]:
        """
        Get selectors for specific screen and element

        Args:
            screen: Screen name (welcome, email, password, etc.)
            element: Element name (create_account, email_field, etc.)

        Returns:
            List of selector strings to try in order
        """
        screen_map = {
            "welcome": cls.WELCOME_SCREEN,
            "email": cls.EMAIL_SCREEN, 
            "password": cls.PASSWORD_SCREEN,
            "details": cls.DETAILS_SCREEN,
            "name": cls.NAME_SCREEN,
            "captcha": cls.CAPTCHA_SCREEN,
            "auth": cls.AUTH_PROGRESS,
            "post_auth": cls.POST_AUTH,
            "inbox": cls.INBOX_SCREEN
        }

        screen_selectors = screen_map.get(screen, {})
        return screen_selectors.get(element, [])

    @classmethod
    def get_dropdown_options(cls, day: int = None, month: str = None) -> Dict[str, List[str]]:
        """
        Get dropdown option selectors

        Args:
            day: Day number to select
            month: Month name to select

        Returns:
            Dictionary with option selectors
        """
        options = {}

        if day is not None:
            options["day"] = [
                f"//*[@text='{day}']",
                f"//*[contains(@text, '{day}')]"
            ]

        if month is not None:
            options["month"] = [
                f"//*[@text='{month}']",
                f"//*[contains(@text, '{month}')]"
            ]

        return options

# Convenience functions for easy access
def get_outlook_selector(screen: str, element: str, index: int = 0) -> str:
    """Get single selector by index"""
    selectors = OutlookSelectors.get_selectors(screen, element)
    return selectors[index] if index < len(selectors) else ""

def get_all_outlook_selectors(screen: str, element: str) -> List[str]:
    """Get all selectors for element"""
    return OutlookSelectors.get_selectors(screen, element)

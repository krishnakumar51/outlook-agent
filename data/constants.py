#!/usr/bin/env python3
"""
Data Constants for Mobile Outlook Agent
Names, dates, and other test data
"""

import random
from typing import Dict, Any
from datetime import datetime

# First names for account generation
FIRST_NAMES = [
    "mary", "john", "david", "michael", "sarah", "jennifer", "william", "elizabeth", "robert", "lisa",
    "james", "maria", "christopher", "nancy", "daniel", "karen", "matthew", "betty", "anthony", "helen",
    "mark", "sandra", "donald", "donna", "steven", "carol", "paul", "ruth", "andrew", "sharon",
    "joshua", "michelle", "kenneth", "laura", "kevin", "sarah", "brian", "kimberly", "george", "deborah",
    "edward", "dorothy", "ronald", "lisa", "timothy", "nancy", "jason", "karen", "jeffrey", "betty"
]

# Last names for account generation
LAST_NAMES = [
    "smith", "johnson", "williams", "brown", "jones", "garcia", "miller", "davis", "rodriguez", "martinez",
    "hernandez", "lopez", "gonzalez", "wilson", "anderson", "thomas", "taylor", "moore", "jackson", "martin",
    "lee", "perez", "thompson", "white", "harris", "sanchez", "clark", "ramirez", "lewis", "robinson",
    "walker", "young", "allen", "king", "wright", "scott", "torres", "nguyen", "hill", "flores",
    "green", "adams", "nelson", "baker", "hall", "rivera", "campbell", "mitchell", "carter", "roberts"
]

# Full month names for Outlook
MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# Real CURP IDs for testing (placeholder - will be filled later)
REAL_CURP_IDS = [
    # Leave blank for now - will be populated with real CURPs
]

# Default secure password for all accounts
DEFAULT_PASSWORD = "wrfyh@6498$"

def generate_demo_data() -> Dict[str, Any]:
    """
    Generate realistic demo data for testing
    Based on your generate_demo_curp_data pattern
    """
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)

    # Generate realistic birth date (1980-2005) for working adults
    birth_year = random.randint(1980, 2005)
    birth_month = random.randint(1, 12)

    # Handle different month lengths
    if birth_month in [1, 3, 5, 7, 8, 10, 12]:
        birth_day = random.randint(1, 31)
    elif birth_month in [4, 6, 9, 11]:
        birth_day = random.randint(1, 30)
    else:  # February
        # Handle leap years
        if birth_year % 4 == 0 and (birth_year % 100 != 0 or birth_year % 400 == 0):
            birth_day = random.randint(1, 29)
        else:
            birth_day = random.randint(1, 28)

    # Format as YYYY-MM-DD
    date_of_birth = f"{birth_year:04d}-{birth_month:02d}-{birth_day:02d}"

    # Generate CURP ID (placeholder)
    curp_id = random.choice(REAL_CURP_IDS) if REAL_CURP_IDS else "DEMO123456HDFRNN01"

    return {
        "curp_id": curp_id,
        "first_name": first_name.title(),
        "last_name": last_name.title(), 
        "date_of_birth": date_of_birth,
        "age": 2025 - birth_year
    }

def generate_outlook_email(first_name: str, last_name: str) -> str:
    """
    Generate Outlook email address
    Based on your improved email generation strategy
    """
    # Clean names
    first_clean = first_name.lower().replace(" ", "")
    last_clean = last_name.lower().replace(" ", "")

    # Generate random numbers (3 digits each)
    first_numbers = f"{random.randint(100, 999)}"
    last_numbers = f"{random.randint(100, 999)}"

    # Create email: firstname + numbers + lastname + numbers
    username = f"{first_clean}{first_numbers}{last_clean}{last_numbers}"
    return f"{username}@outlook.com"

def parse_birth_date(date_string: str) -> Dict[str, Any]:
    """
    Parse date string into components for Outlook

    Args:
        date_string: Date in YYYY-MM-DD format

    Returns:
        Dictionary with day, month, year components
    """
    try:
        date_obj = datetime.strptime(date_string, "%Y-%m-%d")
        return {
            "day": date_obj.day,
            "month": MONTHS[date_obj.month - 1],  # Full month name
            "year": date_obj.year
        }
    except ValueError as e:
        raise ValueError(f"Invalid date format. Expected YYYY-MM-DD, got: {date_string}")

def validate_age(date_of_birth: str, min_age: int = 18, max_age: int = 100) -> bool:
    """
    Validate age is within acceptable range

    Args:
        date_of_birth: Date string YYYY-MM-DD
        min_age: Minimum acceptable age
        max_age: Maximum acceptable age

    Returns:
        True if age is valid
    """
    try:
        birth_date = datetime.strptime(date_of_birth, "%Y-%m-%d")
        today = datetime.now()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return min_age <= age <= max_age
    except ValueError:
        return False

# Sample data for testing
SAMPLE_USERS = [
    {
        "first_name": "John",
        "last_name": "Smith", 
        "date_of_birth": "1995-05-15",
        "curp_id": "DEMO123456HDFRNN01"
    },
    {
        "first_name": "Maria",
        "last_name": "Garcia",
        "date_of_birth": "1988-12-03",
        "curp_id": "DEMO654321MDFGHI02"
    },
    {
        "first_name": "David", 
        "last_name": "Johnson",
        "date_of_birth": "1992-08-22",
        "curp_id": "DEMO789012HDFABC03"
    }
]

# App configuration constants
OUTLOOK_APP_PACKAGE = "com.microsoft.office.outlook"
OUTLOOK_APP_ACTIVITY = ".MainActivity"
APPIUM_SERVER_URL = "http://localhost:4723"

# Timeout constants
ELEMENT_TIMEOUT = 10
LONG_PRESS_DURATION = 15000  # 15 seconds
AUTH_WAIT_TIMEOUT = 90       # 90 seconds
POST_AUTH_BUDGET = 7.0       # 7 seconds

# Retry constants
MAX_RETRIES = 3
RETRY_DELAY = 0.5

def get_app_config() -> Dict[str, Any]:
    """Get app configuration"""
    return {
        "app_package": OUTLOOK_APP_PACKAGE,
        "app_activity": OUTLOOK_APP_ACTIVITY,
        "appium_url": APPIUM_SERVER_URL,
        "timeouts": {
            "element": ELEMENT_TIMEOUT,
            "long_press": LONG_PRESS_DURATION,
            "auth_wait": AUTH_WAIT_TIMEOUT,
            "post_auth": POST_AUTH_BUDGET
        },
        "retries": {
            "max_retries": MAX_RETRIES,
            "delay": RETRY_DELAY
        }
    }

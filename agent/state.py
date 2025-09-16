#!/usr/bin/env python3
"""
Outlook Mobile Agent State Management
Defines the state structure for LangGraph agent
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime

@dataclass
class OutlookAccountData:
    """Outlook account data structure"""
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    birth_day: int
    birth_month: str  # Full month name
    birth_year: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "username": self.username,
            "email": self.email, 
            "password": self.password,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "birth_day": self.birth_day,
            "birth_month": self.birth_month,
            "birth_year": self.birth_year
        }

@dataclass
class OutlookAgentState:
    """State for Outlook Mobile Agent workflow"""

    # Input data
    process_id: str
    curp_id: Optional[str] = None
    first_name: str = ""
    last_name: str = ""  
    date_of_birth: str = ""  # YYYY-MM-DD format

    # Generated account data
    account_data: Optional[OutlookAccountData] = None

    # Workflow progress
    current_step: str = "init"
    step_number: int = 0
    total_steps: int = 9

    # Step completion status
    steps_completed: Dict[str, bool] = field(default_factory=lambda: {
        "init": False,
        "welcome": False, 
        "email": False,
        "password": False,
        "details": False,
        "name": False, 
        "captcha": False,
        "auth_wait": False,
        "post_auth": False,
        "verify": False
    })

    # Driver and tools
    driver: Optional[Any] = None
    screen_size: Optional[Dict[str, int]] = None

    # Status tracking
    success: bool = False
    error_message: Optional[str] = None

    # Logs and debugging
    logs: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # Retry tracking
    retry_counts: Dict[str, int] = field(default_factory=lambda: {
        "welcome": 0,
        "email": 0,
        "password": 0, 
        "details": 0,
        "name": 0,
        "captcha": 0,
        "auth_wait": 0,
        "post_auth": 0
    })

    max_retries: int = 3

    def add_log(self, message: str, step: Optional[str] = None):
        """Add log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        if step:
            log_entry = f"[{timestamp}] [{step.upper()}] {message}"

        self.logs.append(log_entry)
        print(log_entry)

    def mark_step_complete(self, step: str, success: bool = True):
        """Mark step as completed"""
        self.steps_completed[step] = success
        if success:
            self.add_log(f"✅ Step completed: {step}")
        else:
            self.add_log(f"❌ Step failed: {step}")

    def set_current_step(self, step: str, step_number: int = None):
        """Set current step"""
        self.current_step = step
        if step_number is not None:
            self.step_number = step_number
        self.add_log(f"📍 Starting step: {step} ({self.step_number}/{self.total_steps})")

    def increment_retry(self, step: str) -> bool:
        """
        Increment retry count for step

        Returns:
            True if retries available, False if max reached
        """
        self.retry_counts[step] = self.retry_counts.get(step, 0) + 1

        if self.retry_counts[step] <= self.max_retries:
            self.add_log(f"🔄 Retry {self.retry_counts[step]}/{self.max_retries} for step: {step}")
            return True
        else:
            self.add_log(f"❌ Max retries reached for step: {step}")
            return False

    def get_progress_percentage(self) -> int:
        """Calculate progress percentage"""
        completed_steps = sum(1 for completed in self.steps_completed.values() if completed)
        return int((completed_steps / len(self.steps_completed)) * 100)

    def set_error(self, error: str, step: Optional[str] = None):
        """Set error state"""
        self.success = False
        self.error_message = error
        self.end_time = datetime.now()

        if step:
            self.add_log(f"❌ Error in {step}: {error}")
        else:
            self.add_log(f"❌ Error: {error}")

    def set_success(self):
        """Set success state"""
        self.success = True
        self.error_message = None
        self.end_time = datetime.now()
        self.add_log("🎉 Outlook account creation completed successfully!")

    def get_duration(self) -> Optional[float]:
        """Get workflow duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def get_summary(self) -> Dict[str, Any]:
        """Get workflow summary"""
        return {
            "process_id": self.process_id,
            "success": self.success,
            "error_message": self.error_message,
            "current_step": self.current_step,
            "progress_percentage": self.get_progress_percentage(),
            "steps_completed": self.steps_completed,
            "duration_seconds": self.get_duration(),
            "account_email": self.account_data.email if self.account_data else None,
            "retry_counts": self.retry_counts,
            "logs": self.logs[-10:]  # Last 10 logs
        }

    def should_continue(self) -> bool:
        """Check if workflow should continue"""
        return not self.success and self.error_message is None

    def reset_for_retry(self, step: str):
        """Reset state for step retry"""
        self.steps_completed[step] = False
        self.error_message = None
        self.add_log(f"🔄 Resetting step for retry: {step}")

# Helper functions for state management
def create_initial_state(process_id: str, first_name: str, last_name: str, 
                        date_of_birth: str, curp_id: Optional[str] = None) -> OutlookAgentState:
    """Create initial agent state"""
    state = OutlookAgentState(
        process_id=process_id,
        curp_id=curp_id,
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        start_time=datetime.now()
    )

    state.add_log(f"🚀 Initializing Outlook agent for {first_name} {last_name}")
    return state

def generate_outlook_account_data(first_name: str, last_name: str, 
                                date_of_birth: str) -> OutlookAccountData:
    """Generate Outlook account data from personal info"""
    import random
    from datetime import datetime

    # Clean names for email
    first_clean = first_name.lower().replace(" ", "")
    last_clean = last_name.lower().replace(" ", "")

    # Generate random numbers for email uniqueness
    first_numbers = f"{random.randint(100, 999)}"
    last_numbers = f"{random.randint(100, 999)}"

    # Create username and email
    username = f"{first_clean}{first_numbers}{last_clean}{last_numbers}"
    email = f"{username}@outlook.com"

    # Parse birth date
    birth_date_obj = datetime.strptime(date_of_birth, "%Y-%m-%d")

    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    return OutlookAccountData(
        username=username,
        email=email,
        password="wrfyh@6498$",  # Secure fixed password
        first_name=first_name,
        last_name=last_name, 
        birth_day=birth_date_obj.day,
        birth_month=months[birth_date_obj.month - 1],
        birth_year=birth_date_obj.year
    )

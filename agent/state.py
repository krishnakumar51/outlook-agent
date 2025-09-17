#!/usr/bin/env python3
"""
PRODUCTION STATE - Based on comp.py exact flow
Fixed all issues: country selection, last name typing, recursion limits
"""

from typing import Dict, Any, List, Optional, Union, TypedDict, Annotated
from dataclasses import dataclass
from datetime import datetime
import time
from enum import Enum

from langgraph.graph.message import AnyMessage, add_messages
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage


class WorkflowStep(Enum):
    """Workflow steps matching comp.py EXACTLY"""
    INIT = "init"
    WELCOME = "welcome"           # step1_welcome() 
    EMAIL = "email"               # step2_email()
    PASSWORD = "password"         # step3_password()  
    DETAILS = "details"           # step4_details_fixed()
    NAME = "name"                 # step5_name()
    CAPTCHA = "captcha"           # step6_captcha()
    AUTH_WAIT = "auth_wait"       # wait_authentication()
    POST_AUTH = "post_auth"       # step7_post_captcha()
    VERIFY = "verify"             # Check inbox
    CLEANUP = "cleanup"
    ERROR = "error"


@dataclass
class OutlookAccountData:
    """Account data matching comp.py generation pattern"""
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    date_of_birth: str
    birth_day: int
    birth_month: str
    birth_year: int
    curp_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "username": self.username,
            "email": self.email,
            "password": self.password,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "date_of_birth": self.date_of_birth,
            "birth_day": self.birth_day,
            "birth_month": self.birth_month,
            "birth_year": self.birth_year,
            "curp_id": self.curp_id
        }


@dataclass
class ToolCallRecord:
    tool_name: str
    action: str
    parameters: Dict[str, Any]
    result: Dict[str, Any]
    success: bool
    duration_ms: int
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "action": self.action,
            "parameters": self.parameters,
            "result": self.result,
            "success": self.success,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat()
        }


class OutlookAgentState(TypedDict):
    """Complete state definition matching comp.py flow"""
    # Core identification
    process_id: str
    
    # User input data
    first_name: str
    last_name: str
    date_of_birth: str
    curp_id: Optional[str]
    
    # Generated account data
    account_data: Optional[OutlookAccountData]
    
    # Workflow tracking
    current_step: WorkflowStep
    progress_percentage: int
    steps_completed: Dict[str, bool]
    success: bool
    
    # Step flags - EXACTLY matching comp.py flow
    email_typed: Optional[bool]
    password_typed: Optional[bool]
    # Details step
    details_day_selected: Optional[bool]
    details_day_value_selected: Optional[bool]
    details_month_selected: Optional[bool]
    details_month_value_selected: Optional[bool]
    details_year_typed: Optional[bool]
    # Name step - CRITICAL: Both first AND last name
    first_name_typed: Optional[bool]
    last_name_typed: Optional[bool]
    # Other flags
    captcha_pressed: Optional[bool]
    auth_completed: Optional[bool]
    inbox_reached: Optional[bool]
    
    # LangGraph message history
    messages: Annotated[List[AnyMessage], add_messages]
    
    # Tool execution tracking
    tool_call_history: List[ToolCallRecord]
    consecutive_errors: int
    retry_counts: Dict[str, int]
    
    # Driver and screen context
    driver: Optional[Any]
    screen_size: Optional[Dict[str, int]]
    
    # Error handling
    error_message: Optional[str]
    last_error_context: Optional[Dict[str, Any]]
    
    # LLM integration
    use_llm: bool
    llm_analysis: Optional[Dict[str, Any]]
    
    # Timing
    start_time: float
    end_time: Optional[float]
    max_tool_calls: int  # UPDATED: Default 100
    
    # Automation context
    automation_goal: str


def create_initial_state(
    process_id: str,
    first_name: str,
    last_name: str,
    date_of_birth: str,
    curp_id: Optional[str] = None,
    use_llm: bool = True
) -> OutlookAgentState:
    """Create initial state for automation"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"🏗️  [{timestamp}] STATE: Creating initial workflow state...")
    
    return {
        # Core identification
        "process_id": process_id,
        
        # User input
        "first_name": first_name,
        "last_name": last_name,
        "date_of_birth": date_of_birth,
        "curp_id": curp_id,
        
        # Account data (to be generated)
        "account_data": None,
        
        # Workflow state
        "current_step": WorkflowStep.INIT,
        "progress_percentage": 0,
        "steps_completed": {},
        "success": False,
        
        # Step flags - ALL initialized to False
        "email_typed": False,
        "password_typed": False,
        "details_day_selected": False,
        "details_day_value_selected": False,
        "details_month_selected": False,
        "details_month_value_selected": False,
        "details_year_typed": False,
        "first_name_typed": False,  # CRITICAL
        "last_name_typed": False,   # CRITICAL
        "captcha_pressed": False,
        "auth_completed": False,
        "inbox_reached": False,
        
        # Message history
        "messages": [],
        
        # Tool tracking
        "tool_call_history": [],
        "consecutive_errors": 0,
        "retry_counts": {},
        
        # Driver context
        "driver": None,
        "screen_size": None,
        
        # Error handling
        "error_message": None,
        "last_error_context": None,
        
        # LLM integration
        "use_llm": use_llm,
        "llm_analysis": None,
        
        # Timing
        "start_time": time.time(),
        "end_time": None,
        "max_tool_calls": 100,  # UPDATED: Increased from 25
        
        # Context
        "automation_goal": f"Create Outlook account for {first_name} {last_name}"
    }


def generate_outlook_account_data(first_name: str, last_name: str, date_of_birth: str) -> OutlookAccountData:
    """Generate account data EXACTLY like comp.py"""
    import random
    from datetime import datetime as dt
    
    print(f"📧 [ACCOUNT] Generating account data for {first_name} {last_name}")
    
    try:
        bdt = dt.strptime(date_of_birth, "%Y-%m-%d")
        birth_day = bdt.day
        birth_year = bdt.year
        birth_month = bdt.strftime("%B")
    except ValueError:
        birth_day, birth_month, birth_year = 15, "January", 1995
        
    # EXACTLY match comp.py pattern
    username = f"fix{random.randint(100000, 999999)}"
    email = f"{username}@outlook.com"
    password = f"Fixed{random.randint(100, 999)}Pass!"
    
    return OutlookAccountData(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        birth_day=birth_day,
        birth_month=birth_month,
        birth_year=birth_year
    )


def add_tool_call_record(
    state: OutlookAgentState,
    tool_name: str,
    action: str,
    parameters: Dict[str, Any],
    result: Dict[str, Any],
    duration_ms: int,
    success: bool
) -> OutlookAgentState:
    """Add tool call record to state history"""
    record = ToolCallRecord(
        tool_name=tool_name,
        action=action,
        parameters=parameters,
        result=result,
        success=success,
        duration_ms=duration_ms,
        timestamp=datetime.now()
    )
    
    state["tool_call_history"].append(record)
    
    # Update retry counts
    retry_key = f"{tool_name}.{action}"
    if not success:
        state["retry_counts"][retry_key] = state["retry_counts"].get(retry_key, 0) + 1
        state["consecutive_errors"] = state.get("consecutive_errors", 0) + 1
    else:
        state["consecutive_errors"] = 0
        
    return state


def set_current_step(state: OutlookAgentState, step: WorkflowStep, progress: int) -> OutlookAgentState:
    """Update current workflow step and progress"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    old_step = state["current_step"].value if isinstance(state["current_step"], WorkflowStep) else state["current_step"]
    new_step = step.value if isinstance(step, WorkflowStep) else step
    
    print(f"📍 [{timestamp}] STATE: Step transition: {old_step} → {new_step} ({progress}%)")
    
    state["current_step"] = step
    state["progress_percentage"] = progress
    return state


def set_success(state: OutlookAgentState) -> OutlookAgentState:
    """Mark automation as successful"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"🎉 [{timestamp}] STATE: Automation marked as successful!")
    
    state["success"] = True
    state["progress_percentage"] = 100
    state["end_time"] = time.time()
    return state


def get_state_summary(state: OutlookAgentState) -> Dict[str, Any]:
    """Get comprehensive state summary for reporting"""
    duration = 0
    if state.get("start_time") and state.get("end_time"):
        duration = state["end_time"] - state["start_time"]
    elif state.get("start_time"):
        duration = time.time() - state["start_time"]
    
    # Get recent tool activity
    recent_tools = []
    if state.get("tool_call_history"):
        recent_calls = state["tool_call_history"][-5:]  # Last 5 calls
        for call in recent_calls:
            status_icon = "✅" if call.success else "❌"
            recent_tools.append(
                f"{status_icon} {call.tool_name}.{call.action} ({call.duration_ms}ms)"
            )
    
    return {
        "process_id": state["process_id"],
        "success": state.get("success", False),
        "progress_percentage": state.get("progress_percentage", 0),
        "current_step": state["current_step"].value if isinstance(state["current_step"], WorkflowStep) else state["current_step"],
        "created_account": state["account_data"].email if state.get("account_data") else None,
        "duration_seconds": round(duration, 1),
        "tool_calls_made": len(state.get("tool_call_history", [])),
        "use_llm": state.get("use_llm", False),
        "error_message": state.get("error_message"),
        "recent_tool_activity": recent_tools
    }
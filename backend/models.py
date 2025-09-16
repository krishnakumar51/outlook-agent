#!/usr/bin/env python3
"""
Backend Models for Mobile Outlook Agent
Pydantic models for API requests, responses, and database schemas
Updated with LLM integration models
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid

# Enums
class ProcessStatus(str, Enum):
    """Process status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class LLMProvider(str, Enum):
    """Supported LLM providers"""
    GROQ = "groq"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"

class OutlookSteps(str, Enum):
    """Outlook automation steps"""
    INIT = "init"
    WELCOME = "welcome"
    EMAIL = "email"
    PASSWORD = "password"
    DETAILS = "details"
    NAME = "name"
    CAPTCHA = "captcha"
    AUTH_WAIT = "auth_wait"
    POST_AUTH = "post_auth"
    VERIFY = "verify"

# Request Models
class OutlookAccountRequest(BaseModel):
    """Request model for Outlook account creation"""
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    date_of_birth: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    curp_id: Optional[str] = None
    use_llm: bool = True

class DemoAccountsRequest(BaseModel):
    """Request model for demo automation"""
    count: int = Field(1, ge=1, le=5)
    use_llm: bool = True

class LLMTestRequest(BaseModel):
    """Request model for LLM testing"""
    prompt: str = Field(..., min_length=1, max_length=5000)
    provider: Optional[str] = "groq"
    model: Optional[str] = None
    temperature: float = Field(0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(2048, ge=1, le=8192)

class LLMErrorAnalysisRequest(BaseModel):
    """Request model for LLM error analysis"""
    error_message: str = Field(..., min_length=1, max_length=1000)
    step: str = Field(..., min_length=1, max_length=50)
    context: Dict[str, Any] = Field(default_factory=dict)
    provider: Optional[str] = "groq"

# Response Models
class BaseResponse(BaseModel):
    """Base response model"""
    success: bool
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class OutlookAccountResponse(BaseResponse):
    """Response model for Outlook account creation"""
    process_id: str
    account_data: Optional[Dict[str, Any]] = None

class ProcessStatusResponse(BaseModel):
    """Process status response"""
    process_id: str
    status: str
    progress_percentage: int = Field(0, ge=0, le=100)
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    logs: List[str] = Field(default_factory=list)
    duration: Optional[float] = None
    retry_counts: Optional[Dict[str, int]] = Field(default_factory=dict)

class LLMResponse(BaseModel):
    """LLM response model"""
    success: bool
    response: Optional[str] = None
    provider: str
    model: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class LLMProvidersResponse(BaseModel):
    """Response for available LLM providers"""
    available_providers: List[str]
    default_provider: Optional[str] = None
    required_env_vars: Dict[str, str] = Field(default_factory=dict)

class OutlookAccountSummary(BaseModel):
    """Summary of Outlook account"""
    process_id: str
    email: Optional[str] = None
    password: Optional[str] = None
    status: str
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    used_llm: bool = False

class OutlookAccountsResponse(BaseModel):
    """Response for account listing"""
    accounts: List[OutlookAccountSummary]
    total_count: int
    successful_count: int = 0
    failed_count: int = 0

class SystemHealth(BaseModel):
    """System health status"""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"
    features: Dict[str, bool] = Field(default_factory=lambda: {
        "outlook_automation": True,
        "llm_integration": True,
        "database": True
    })
    llm_providers: List[str] = Field(default_factory=list)

class LogEntry(BaseModel):
    """Log entry model"""
    timestamp: str
    message: str
    process_id: Optional[str] = None
    level: str = "INFO"

class LogsResponse(BaseModel):
    """Response for logs endpoint"""
    logs: List[LogEntry]
    total_count: int
